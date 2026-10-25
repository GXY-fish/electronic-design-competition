/**
 * @file    main.c
 * @brief   STM32F103C8 (BluePill) 旋转倒立摆(Furuta) · 自动启摆+直立控制器
 *
 * 控制思想(经典 Furuta 倒立摆):
 *   1) 启摆 —— 摆杆摆到最高点附近时, 用 bang-bang 反向瞬时踢(共振泵能),
 *      把能量一点点灌进摆杆, 直到它摆进中心区间。
 *   2) 直立 —— 进中心区间后切双环串级 PID:
 *      内环角度环(快, 5ms) 稳住摆杆, 外环位置环(慢, 50ms) 把横臂拉回中位。
 *
 * 代码组织(模块化, 控制逻辑与硬件/显示解耦):
 *   每 1ms 节拍由 TIM1 中断触发, 调用 Pendulum_RunTick(), 内部是一条
 *   "接力"流水线 —— 前一个函数的输出结构体, 直接喂给下一个函数:
 *
 *      Pendulum_Sense()  --SensorSample_t-->  Pendulum_Control()
 *                       <--MotorCmd_t--        |
 *                                             v
 *                                   Pendulum_Drive()  --写电机-->
 *
 *   全程状态(状态机 + 计次/角度历史/上次PWM)集中放在 PendulumCtx_t ctx 里,
 *   跨 1ms 调用保留, 不再散落一堆全局变量。
 *
 * 硬件映射(与江协参考逐条一致, 引脚无需改动):
 *   电机方向 TB6612 : PB12/PB13 ; PWM=PA0(TIM2_CH1, 20kHz, 占空比 0~100)
 *   臂编码器 TIM3  : PA6/PA7
 *   摆杆角度电位器 : PB0 (ADC1_CH8, 0~4095, 中心≈2010)
 *   按键 K1=PB10(本板损坏)/K2=PB11/K3=PA11/K4=PA12
 *
 * 注: 控制律源自江协科技《倒立摆-自动启摆》教学例程, 此处重写为自封装模块。
 */

#include "stm32f10x.h"
#include "Delay.h"
#include "OLED.h"
#include "LED.h"
#include "Timer.h"
#include "Key.h"
#include "RP.h"
#include "Motor.h"
#include "Encoder.h"
#include "Serial.h"
#include "AD.h"
#include "PID.h"

/* ===================== 可调参数(上板按机架实测改) ===================== */
#define ANGLE_CENTER   2010    // 摆杆垂直向下(平衡位)的电位器读数, 一般 1900~2200
                                // 不准 -> 摆杆老往一边跑 / 位置环稳态误差
#define ANGLE_BAND     500     // 中心区间半宽: |Angle-ANGLE_CENTER| < ANGLE_BAND 算"进中心"
#define SWING_PWM      35      // 启摆踢力, 一般 30~40; 泵不上就加, 常过冲就减
#define SWING_T_HOLD   100     // 单次踢的持续时间(ms), 一般 80~120; 太小力度发不出, 太大不利共振

/* ===================== 状态机常量 ===================== */
#define ST_STOP        0       // 停机
#define ST_JUDGE       1       // 判断: 采样摆杆最高点 / 是否进中心
#define ST_SW_L1       21      // 向左踢
#define ST_SW_L2       22      // 左踢后延时
#define ST_SW_L3       23      // 向右踢
#define ST_SW_L4       24      // 右踢后延时
#define ST_SW_R1       31      // 向右踢(对称分支)
#define ST_SW_R2       32
#define ST_SW_R3       33
#define ST_SW_R4       34
#define ST_BALANCE     4       // 双环 PID 直立

/* ===================== 数据结构(函数间接力传递) ===================== */
/* Sense 的输出 -> Control 的输入: 一帧传感器采样 */
typedef struct {
    uint16_t angle;     // 摆杆角度(ADC 原始值)
    int16_t  speed;     // 本周期电机速度(编码器增量)
    int32_t  pos;       // 臂累积位置(速度积分)
} SensorSample_t;

/* Control 的输出 -> Drive 的输入: 一条电机指令 */
typedef struct {
    int16_t pwm;        // 目标 PWM(-100~+100)
} MotorCmd_t;

/* 控制器持久上下文(跨 1ms 调用保留) —— 把所有状态收进一个地方 */
typedef struct {
    uint8_t  state;                 // 状态机当前状态
    uint16_t cntJudge;              // 判断状态计次(每40ms进一次)
    uint16_t cntAng;                // 角度环计次(每5ms进一次)
    uint16_t cntPos;                // 位置环计次(每50ms进一次)
    uint16_t cntTimer;              // 启摆瞬时驱动计时
    uint16_t angHist[3];           // 近3次角度采样(判最高点用, [0]最新)
    int16_t  lastPWM;               // 上次实际下发PWM(非更新周期保持电机输出)
    uint16_t angle;                 // 最新角度(给OLED显示)
    int32_t  pos;                   // 最新位置(给OLED显示)
    int16_t  speed;                 // 最新速度(给OLED显示)
    PID_t    angPID;                // 内环角度环
    PID_t    locPID;                // 外环位置环
} PendulumCtx_t;

/* 全局控制器实例(PID 增益在 main 里用 PID_Init 设定, 见下) */
static PendulumCtx_t ctx = { .state = ST_STOP };

uint8_t KeyNum;    // 按键键码(仅 main 显示/按键循环用)

/* =======================================================================
   函数1: Pendulum_Sense —— 采集一帧传感器数据
   输入: 无(直接读硬件)
   输出: SensorSample_t, 作为下一个函数(Control)的输入
   ======================================================================= */
static SensorSample_t Pendulum_Sense(void)
{
    SensorSample_t s;

    s.angle = AD_GetValue();        // 读摆杆角度
    s.speed = Encoder_Get();        // 读电机速度
    ctx.pos += s.speed;             // 速度积分 = 位置
    s.pos    = ctx.pos;

    ctx.angle = s.angle;            // 同步给 OLED 显示
    ctx.speed = s.speed;
    return s;                       // 把这一帧交给下一个函数
}

/* =======================================================================
   函数2: Pendulum_Control —— 状态机 + 双环PID决策
   输入: SensorSample_t(上一个函数的输出)
   输出: MotorCmd_t(给电机的指令), 作为下一个函数(Drive)的输入
   ======================================================================= */
static MotorCmd_t Pendulum_Control(SensorSample_t s)
{
    MotorCmd_t cmd;
    cmd.pwm = ctx.lastPWM;          // 默认保持上次输出(非更新周期电机不掉电)

    switch (ctx.state)
    {
    case ST_STOP:                   // 停机
        cmd.pwm = 0;
        break;

    case ST_JUDGE:                 // 判断状态: 每40ms采3次角, 判最高点 / 是否进中心
        if (++ctx.cntJudge >= 40)
        {
            ctx.cntJudge = 0;
            ctx.angHist[2] = ctx.angHist[1];
            ctx.angHist[1] = ctx.angHist[0];
            ctx.angHist[0] = s.angle;

            /* 右侧最高点: 三次都在右侧区间, 且中间一次最小 */
            if (ctx.angHist[0] > ANGLE_CENTER + ANGLE_BAND &&
                ctx.angHist[1] > ANGLE_CENTER + ANGLE_BAND &&
                ctx.angHist[2] > ANGLE_CENTER + ANGLE_BAND &&
                ctx.angHist[1] < ctx.angHist[0] &&
                ctx.angHist[1] < ctx.angHist[2])
            {
                ctx.state = ST_SW_L1;
            }
            /* 左侧最高点: 对称 */
            if (ctx.angHist[0] < ANGLE_CENTER - ANGLE_BAND &&
                ctx.angHist[1] < ANGLE_CENTER - ANGLE_BAND &&
                ctx.angHist[2] < ANGLE_CENTER - ANGLE_BAND &&
                ctx.angHist[1] > ctx.angHist[0] &&
                ctx.angHist[1] > ctx.angHist[2])
            {
                ctx.state = ST_SW_R1;
            }
            /* 进中心区间: 启摆完成, 切双环PID */
            if (ctx.angHist[0] > ANGLE_CENTER - ANGLE_BAND &&
                ctx.angHist[0] < ANGLE_CENTER + ANGLE_BAND &&
                ctx.angHist[1] > ANGLE_CENTER - ANGLE_BAND &&
                ctx.angHist[1] < ANGLE_CENTER + ANGLE_BAND)
            {
                ctx.pos = 0;               // 位置归零
                PID_Reset(&ctx.angPID);    // 清两环内部状态, 防旧积分污染
                PID_Reset(&ctx.locPID);
                ctx.state = ST_BALANCE;
            }
        }
        break;

    /* ---- 启摆: 左先踢 与 右先踢 两条对称分支, 靠"最高点反向踢"共振泵能 ---- */
    case ST_SW_L1:  cmd.pwm =  SWING_PWM; ctx.cntTimer = SWING_T_HOLD; ctx.state = ST_SW_L2; break;
    case ST_SW_L2:  if (--ctx.cntTimer == 0) ctx.state = ST_SW_L3; break;
    case ST_SW_L3:  cmd.pwm = -SWING_PWM; ctx.cntTimer = SWING_T_HOLD; ctx.state = ST_SW_L4; break;
    case ST_SW_L4:  if (--ctx.cntTimer == 0) { cmd.pwm = 0; ctx.state = ST_JUDGE; } break;

    case ST_SW_R1:  cmd.pwm = -SWING_PWM; ctx.cntTimer = SWING_T_HOLD; ctx.state = ST_SW_R2; break;
    case ST_SW_R2:  if (--ctx.cntTimer == 0) ctx.state = ST_SW_R3; break;
    case ST_SW_R3:  cmd.pwm =  SWING_PWM; ctx.cntTimer = SWING_T_HOLD; ctx.state = ST_SW_R4; break;
    case ST_SW_R4:  if (--ctx.cntTimer == 0) { cmd.pwm = 0; ctx.state = ST_JUDGE; } break;

    case ST_BALANCE:                // 双环串级 PID 直立
    {
        /* 摆杆跌出中心区间 -> 自动停机 */
        if (!(s.angle > ANGLE_CENTER - ANGLE_BAND && s.angle < ANGLE_CENTER + ANGLE_BAND))
            ctx.state = ST_STOP;

        /* 内环角度环(每5ms): 实际值=角度, 输出直接给电机 */
        if (++ctx.cntAng >= 5)
        {
            ctx.cntAng = 0;
            ctx.angPID.Actual = s.angle;
            cmd.pwm = PID_Compute(&ctx.angPID);   // 算内环, 输出直接给电机
        }
        /* 外环位置环(每50ms): 实际值=位置, 输出修正内环目标, 组成串级 */
        if (++ctx.cntPos >= 50)
        {
            ctx.cntPos = 0;
            ctx.locPID.Actual = ctx.pos;
            ctx.angPID.Target = ANGLE_CENTER - PID_Compute(&ctx.locPID);  // 外环修正内环目标, 组成串级
        }
        break;
    }
    }

    ctx.lastPWM = cmd.pwm;          // 记录本次下发值, 供下一周期保持电机输出
    return cmd;                     // 把决策结果交给下一个函数
}

/* =======================================================================
   函数3: Pendulum_Drive —— 执行驱动
   输入: MotorCmd_t(上一个函数的输出)
   输出: 无(直接写电机)
   ======================================================================= */
static void Pendulum_Drive(MotorCmd_t cmd)
{
    Motor_SetPWM(cmd.pwm);
}

/* =======================================================================
   接力编排: 把三个函数串成一条流水线, 每1ms由 TIM1 中断调用一次
   Sense的输出 -> Control的输入 -> Drive的输入
   ======================================================================= */
static void Pendulum_RunTick(void)
{
    SensorSample_t s = Pendulum_Sense();     // ① 采集: 输出 s
    MotorCmd_t    c = Pendulum_Control(s);   // ② 决策: 吃 s 的输出, 吐出 c
    Pendulum_Drive(c);                       // ③ 驱动: 吃 c 的输出, 写到电机
}

int main(void)
{
    /* 模块初始化 */
    OLED_Init();
    LED_Init();
    Key_Init();
    RP_Init();
    Motor_Init();
    Encoder_Init();
    Serial_Init();       // 串口, 波特率9600, 当前未使用
    AD_Init();
    Timer_Init();        // 定时器, 1ms 中断

    /* 建立双环 PID: 内环角度环(快) + 外环位置环(慢) */
    PID_Init(&ctx.angPID, 0.3f, 0.01f, 0.4f, ANGLE_CENTER, -100, 100);  // 角度环
    PID_Init(&ctx.locPID, 0.4f, 0.0f,  4.0f, 0,            -100, 100);  // 位置环

    /* 【本板适配】K1(PB10)硬件损坏(按下始终读到高电平), 原版靠按K1启动启摆,
       这里改为上电延时3秒后自动进入启摆(等效按K1 -> state=ST_SW_L1) */
    OLED_Printf(0, 0, OLED_6X8, "Auto 3s->");
    OLED_Update();
    Delay_ms(3000);
    ctx.state = ST_SW_L1;

    while (1)
    {
        /* 按键控制 */
        KeyNum = Key_GetNum();
        if (KeyNum == 1)                // K1: 停<->启摆切换
        {
            if (ctx.state == ST_STOP) ctx.state = ST_SW_L1;
            else                       ctx.state = ST_STOP;
        }
        if (KeyNum == 2)                // K2: 横臂正转一圈(位置环目标+408)
        {
            ctx.locPID.Target += 408;
            if (ctx.locPID.Target > 4080) ctx.locPID.Target = 4080;
        }
        if (KeyNum == 3)                // K3: 横臂反转一圈(位置环目标-408)
        {
            ctx.locPID.Target -= 408;
            if (ctx.locPID.Target < -4080) ctx.locPID.Target = -4080;
        }

        /* LED 指示运行状态 */
        if (ctx.state) LED_ON(); else LED_OFF();

        /* 电位器旋钮离线调PID(当前注释掉, 需要时解开对应行) */
//      ctx.angPID.Kp = RP_GetValue(1) / 4095.0 * 1;
//      ctx.angPID.Ki = RP_GetValue(2) / 4095.0 * 1;
//      ctx.angPID.Kd = RP_GetValue(3) / 4095.0 * 1;
//      ctx.locPID.Kp = RP_GetValue(1) / 4095.0 * 1;
//      ctx.locPID.Ki = RP_GetValue(2) / 4095.0 * 1;
//      ctx.locPID.Kd = RP_GetValue(3) / 4095.0 * 9;

        /* OLED 显示: 左=角度环, 右=位置环 */
        OLED_Printf(42, 0, OLED_6X8, "%02d", ctx.state);

        OLED_Printf(0, 0, OLED_6X8, "Angle");
        OLED_Printf(0, 12, OLED_6X8, "Kp:%05.3f", ctx.angPID.Kp);
        OLED_Printf(0, 20, OLED_6X8, "Ki:%05.3f", ctx.angPID.Ki);
        OLED_Printf(0, 28, OLED_6X8, "Kd:%05.3f", ctx.angPID.Kd);
        OLED_Printf(0, 40, OLED_6X8, "Tar:%04.0f", ctx.angPID.Target);
        OLED_Printf(0, 48, OLED_6X8, "Act:%04d", ctx.angle);
        OLED_Printf(0, 56, OLED_6X8, "Out:%+04.0f", ctx.angPID.Out);

        OLED_Printf(64, 0, OLED_6X8, "Location");
        OLED_Printf(64, 12, OLED_6X8, "Kp:%05.3f", ctx.locPID.Kp);
        OLED_Printf(64, 20, OLED_6X8, "Ki:%05.3f", ctx.locPID.Ki);
        OLED_Printf(64, 28, OLED_6X8, "Kd:%05.3f", ctx.locPID.Kd);
        OLED_Printf(64, 40, OLED_6X8, "Tar:%+05.0f", ctx.locPID.Target);
        OLED_Printf(64, 48, OLED_6X8, "Act:%+05d", ctx.pos);
        OLED_Printf(64, 56, OLED_6X8, "Out:%+04.0f", ctx.locPID.Out);

        OLED_Update();
    }
}

/* 1ms 定时中断: 只做按键节拍 + 控制器接力, 其余逻辑已全部封装进函数 */
void TIM1_UP_IRQHandler(void)
{
    if (TIM_GetITStatus(TIM1, TIM_IT_Update) == SET)
    {
        Key_Tick();
        Pendulum_RunTick();        // 主控制逻辑: 直接调 Sense -> Control -> Drive 接力
        TIM_ClearITPendingBit(TIM1, TIM_IT_Update);
    }
}
