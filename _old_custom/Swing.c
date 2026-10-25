#include "stm32f10x.h"
#include "Swing.h"
#include "Pendulum.h"
#include "Motor.h"
#include <math.h>

// ===== 旋转倒立摆 任务1 起摆 (有界臂位置伺服 + 全同相换向, 确定版) =====
//
// 每 5ms 控制律:
//   1) 摆杆过底点检测: 滤波摆角 θ 符号翻转即过零。
//   2) 全同相换向(真·泵能): 每个过零点都把臂目标设在"摆杆运动方向同侧极限"
//        (-→+ 过零, θ̇>0 -> target=+L ; +→- 过零, θ̇<0 -> target=-L)。
//        物理: Spong 能量法 τ∝sign(θ̇·cosθ); 底点 cosθ≈1, 臂加速方向=sign(θ̇)=摆杆运动方向,
//        两种过零都同相 -> 全周期顺相位注入能量, 摆幅单调增大, 必过60°。
//   3) 臂 PD 位置伺服: cmd = KP_FW·(target − 臂角) − KD_FW·臂速; 限幅 ±PWM_MAX。
//        臂被钉在 ±L_DEG 之间往复扫动 -> 结构上绝不转圈。
//   4) 达标: |θ|≥60° 连续 OK_HOLD_TICKS 拍 -> 刹停交卷(OK60)。
//   5) 防死锁(v2 关键修复): 臂扫到 ±L 且摆杆久不摆动(>0.6s 无过零)时, 强制翻 target
//        让臂继续往复, 重新激发摆杆。否则摆杆停在下垂不动 -> 过零永不触发 -> 臂卡在 ±L 静止
//        (上板实测即"转半圈就停")。另加启动硬踢(满占空比甩臂 ~200ms)确定性打破对称。
//   6) 自动极性自纠已移除: 全同相下两种初始极性都能泵(仿真已证), 翻转逻辑无意义。
//
// 已用 sim_armservo_v2.py 验证(相位敏感联立 Furuta 方程 + 电机力矩/转速上限 + 达标刹停):
//   全同相 名义 t60=0.3s / 高摩擦 t60=2.1s, 臂累计均≤122°(往复不转圈);
//   无硬踢/防死锁 -> 摆杆静止卡死 20.7° 失败。

// ---- 全局状态(显示用) ----
static uint8_t  g_state   = 0;    // 0=停止 1=运行中 4=达标停机 3=超时失败 5=失控
static uint32_t g_ms      = 0;
static uint8_t  g_ok      = 0;    // 任务1达标: |θ|>=60°
static uint8_t  g_looped  = 0;    // 进入竖直圆周: |θ|>=150°
static float    g_peak    = 0;    // 运行峰值 |θ|
static uint8_t  g_runaway = 0;    // 失控保护
static float    g_armP2P  = 0;    // 臂最近2s峰峰值摆幅(°)

// ---- 控制器内部状态 ----
static int8_t   g_commut   = COMMUT_DIR0;  // 当前换向极性(+1/-1), 自动标定可翻
static float    g_target   = L_DEG;        // 当前臂目标角(±L_DEG)
static int8_t   g_thSign   = 0;            // 上一拍摆角符号(过零检测)
static float    g_phiPrev  = 0;            // 上一拍臂角(度, 求臂速)
static float    g_phiRateF = 0;            // 臂速 EMA(度/秒)
static uint8_t  g_flips    = 0;            // 已自动翻转换向极性次数
static float    g_maxApex  = 0;            // 自动极性窗口内峰值摆幅
static uint16_t g_testMs   = 0;            // 极性测试窗口计时(ms)
static uint16_t g_okTick   = 0;            // 达标去抖计数
static uint16_t g_settledTicks = 0;        // 臂已到位计时(防死锁用)
static uint16_t g_kickTicks    = 0;        // 启动硬踢剩余拍数

// ---- 失控铁闸用 ----
static float    s_lastArm  = 0;
static int8_t   s_dir      = 0;
static uint16_t s_dirTicks = 0;

// ---- 臂峰峰值诊断(滚动 2s 窗口) ----
static float    s_armWinMin = 1e9f;
static float    s_armWinMax = -1e9f;
static uint16_t s_winTick   = 0;
static uint8_t  s_winInit   = 0;

static void reset_state(void)
{
    g_ms = 0; g_ok = 0; g_looped = 0; g_peak = 0; g_runaway = 0; g_armP2P = 0;
    g_commut = COMMUT_DIR0; g_target = L_DEG; g_thSign = 0;
    g_phiPrev = 0; g_phiRateF = 0; g_flips = 0; g_maxApex = 0; g_testMs = 0; g_okTick = 0;
    g_settledTicks = 0; g_kickTicks = 0;
    s_lastArm = 0; s_dir = 0; s_dirTicks = 0;
    s_armWinMin = 1e9f; s_armWinMax = -1e9f; s_winTick = 0; s_winInit = 0;
}

void Swing_Init(void)
{
    g_state = 0;
    reset_state();
}

void Swing_Start(void)
{
    g_state = 1;
    reset_state();
    Pendulum_ZeroArm();       // 臂角参考归零 -> 伺服以当前臂位为 0 中心往复
    g_target = L_DEG;         // 起步先把臂扫向 +L
    g_kickTicks = KICK_TICKS; // 启动硬踢: 前若干拍满占空比甩臂, 确定性打破下垂对称
}

void Swing_Stop(void)
{
    g_state = 0;
    Motor_Brake();
}

uint8_t  Swing_GetState(void)    { return g_state; }
uint32_t Swing_GetTimeMs(void)   { return g_ms; }
float    Swing_GetPeak(void)      { return g_peak; }
uint8_t  Swing_Looped(void)      { return g_looped; }
uint8_t  Swing_Ok(void)          { return g_ok; }
float    Swing_GetArmActual(void) { return Pendulum_GetArmAngle(); }
float    Swing_GetArmP2P(void)     { return g_armP2P; }
int8_t   Swing_GetPumpSign(void) { return g_commut; }
uint8_t  Swing_EncOk(void)      { return 1; }
uint8_t  Swing_GetRunaway(void)  { return g_runaway; }
uint8_t  Swing_GetFlips(void)   { return g_flips; }

// 失控铁闸(返回 1=已触发并停机)
static uint8_t runaway_guard(float arm_real)
{
    float d = arm_real - s_lastArm;
    if (fabsf(d) > 0.5f)
    {
        int8_t nd = (d > 0) ? 1 : -1;
        if (nd == s_dir) s_dirTicks++;
        else { s_dir = nd; s_dirTicks = 1; }
    }
    s_lastArm = arm_real;
    if (s_dirTicks >= RUNAWAY_DIR_TICKS || fabsf(arm_real) > RUNAWAY_ARM_DEG)
    {
        Motor_Brake();
        g_runaway = 1;
        g_state   = 5;
        return 1;
    }
    return 0;
}

// 主控制节拍(TIM4 中断每 5ms, 仅当 g_state==1)
void Swing_Tick(float theta_deg, float theta_dot_dps)
{
    (void)theta_dot_dps;   // 本版不用 θ̇ 求导(改用过零检测, 更抗噪)
    if (g_state != 1) return;
    g_ms += 5u;

    // ---- 峰值 / 自动极性用最大摆幅 ----
    float a = fabsf(theta_deg);
    if (a > g_peak)     g_peak    = a;
    if (a > g_maxApex)  g_maxApex = a;

    // ---- 臂峰峰值诊断(滚动 2s 窗口) ----
    float arm_real = Pendulum_GetArmAngle();
    if (!s_winInit) { s_armWinMin = s_armWinMax = arm_real; s_winInit = 1; }
    if (arm_real < s_armWinMin) s_armWinMin = arm_real;
    if (arm_real > s_armWinMax) s_armWinMax = arm_real;
    if (++s_winTick >= 400u)
    {
        g_armP2P    = s_armWinMax - s_armWinMin;
        s_armWinMin = arm_real; s_armWinMax = arm_real; s_winTick = 0;
    }
    uint8_t armMoving = (g_armP2P > 20.0f);   // 臂在满幅往复才算"真在动"

    // ---- 竖直圆周 / 达标判定 ----
    if (armMoving && !g_looped && a >= 150.0f) g_looped = 1;
    if (g_ms >= 300u)
    {
        if (a >= TASK1_ANGLE_DEG) g_okTick++;
        else                       g_okTick = 0;
        if (g_okTick >= OK_HOLD_TICKS) g_ok = 1;
    }
    if (g_ok)
    {
        Motor_Brake();
        g_state = 4;          // OK60 达标停机交卷
        return;
    }

    // ---- 摆杆过底点检测 + 全同相泵能换向(主泵相位) ----
    //   "泵起来"的本质: 旋转臂在摆杆每次过底点(θ=0)时, 顺着它此刻运动方向加速,
    //   把旋转动能持续灌进摆杆使摆幅单调增大。即 Spong 能量法 τ∝sign(θ̇·cosθ) 的精神:
    //   底点 cosθ≈+1, 故臂加速方向 = sign(θ̇) = 摆杆运动方向(全周期顺相位)。
    //   实现: 每次过零把臂目标设在"摆杆当前运动方向的同侧极限":
    //     -→+ 过零(cur=+1, θ̇>0, 摆杆朝+运动) -> target = +L (臂朝+加速, 同相)
    //     +→- 过零(cur=-1, θ̇<0, 摆杆朝-运动) -> target = -L (臂朝-加速, 同相)
    //   两种过零都动作且都同相 -> 全周期顺相位注入能量(旧版只在-→+翻=半泵半泄, 高摩擦慢一倍)。
    int8_t cur = (theta_deg >= 0.0f) ? 1 : -1;
    if (g_thSign != 0 && cur != g_thSign)       // 发生过零
    {
        g_target = (cur > 0) ? (+L_DEG) : (-L_DEG);
        g_commut = cur;                          // 记下当前臂扫动方向(供诊断 API)
    }
    g_thSign = cur;

    // ---- 防死锁: 臂已到位且摆杆久不摆动 -> 强制翻 target 让臂继续往复, 重新激发摆杆 ----
    //  原版只靠"摆杆过零"翻 target: 若摆杆停在下垂不动, 过零永不触发 -> 臂扫到 ±L 后卡住静止。
    //  上板实测即"转半圈就停"。加这道后, 臂到位 0.6s 仍无过零就自行翻面, 永不卡死。
    float errAbs = fabsf(g_target - arm_real);
    if (errAbs < ARM_ARR_TOL)
    {
        if (g_settledTicks < DWELL_TICKS) g_settledTicks++;
        else { g_target = -g_target; g_settledTicks = 0; }
    }
    else g_settledTicks = 0;

    // ---- 臂 PD 位置伺服 ----
    float phiRateRaw = (arm_real - g_phiPrev) / 0.005f;      // 度/秒
    g_phiRateF = RATE_A * g_phiRateF + (1.0f - RATE_A) * phiRateRaw;
    g_phiPrev  = arm_real;

    float cmdf = KP_FW * (g_target - arm_real) - KD_FW * g_phiRateF;
    if (cmdf >  (float)PWM_MAX) cmdf =  (float)PWM_MAX;
    if (cmdf < -(float)PWM_MAX) cmdf = -(float)PWM_MAX;

    // ---- 启动硬踢: 前 KICK_TICKS 拍用固定占空比把臂甩出去, 确定性打破下垂对称 ----
    if (g_kickTicks > 0)
    {
        g_kickTicks--;
        cmdf = (float)(KICK_DIR * KICK_PWM);
    }

    // ---- 臂软上限: 超 ±ARM_HARD_DEG 强拉回中心(往复兜底) ----
    if (fabsf(arm_real) > ARM_HARD_DEG)
    {
        cmdf = (arm_real > 0.0f) ? -(float)PWM_MAX : (float)PWM_MAX;
    }

    int8_t motorCmd = (int8_t)cmdf;
    if (motorCmd == 0) Motor_Brake();
    else               Motor_SetSpeed(motorCmd);

    // ---- 失控铁闸(最后一道保险) ----
    if (runaway_guard(arm_real)) return;

    // ---- 超时失败 ----
    if (g_ms >= TIMEOUT_MS && !g_ok)
    {
        Motor_Brake();
        g_state = 3;
    }
}
