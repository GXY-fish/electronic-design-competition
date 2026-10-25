#include "stm32f10x.h"
#include "Balance.h"
#include "Pendulum.h"
#include "Motor.h"
#include <math.h>

/* ---------------- 可调参数 (上板主要整定这几组) ----------------
 * 仿真(balance_dualpid_sim.py)已验证: 角度环 |Kp| 越大(配适中 Kd)角误差RMS越小,
 * |Kp_a|>=15 稳定域宽; 位置环取小值只做"约束臂位不飞", 别喧宾夺主。
 * 下列为仿真量纲起点, 真机务必从小到大试凑(先角度环等幅震荡, 再加 Kd 阻尼)。
 */
/* 内环: 摆杆角度环 PD (镇定摆角) */
static float g_bKp = 25.0f;   /* 激进/稳态两套, 见 SetAggressive/SetSteady */
static float g_bKd = 4.0f;
/* 外环: 臂位置环 PD (约束臂位) —— 取小 */
static float g_pKp = 2.0f;
static float g_pKd = 3.0f;

/* 直立区判据: 摆角距竖直(180°)多近算"进区" */
#define BAL_ZONE_DEG      20.0f
/* 输出限幅: ★Motor_SetSpeed 是 int8_t 占空比, 必须 [-100,100] */
#define BAL_PWM_LIMIT     100

static float   g_armZeroDeg = 0.0f;   /* 位置环目标(切入稳摆时的臂角) */
static float   g_armPrevDeg = 0.0f;   /* 上一拍臂角(内部差分求臂角速度) */
static uint8_t g_armInit    = 0;
static float   g_lastMoto   = 0.0f;

void Balance_Init(void)
{
    g_armZeroDeg = 0.0f;
    g_armPrevDeg = 0.0f;
    g_armInit    = 0;
    g_lastMoto   = 0.0f;
    Balance_SetAggressive();
}

/* 刚进平衡区: 激进增益, 确保"抓住"倒立不溜走 */
void Balance_SetAggressive(void)
{
    g_bKp = 40.0f; g_bKd = 4.0f;
    g_pKp = 2.0f;  g_pKd = 3.0f;
}

/* 稳定后: 温和增益, 减少抖动 (对应 WHEELTEC success_count>109 恢复温和参数) */
void Balance_SetSteady(void)
{
    g_bKp = 25.0f; g_bKd = 4.0f;
    g_pKp = 2.0f;  g_pKd = 3.0f;
}

/* 切入稳摆时调一次: 把当前臂角记为位置环目标, 差分基准同步, 避免第一拍臂角速度突跳 */
void Balance_CaptureArmZero(void)
{
    float arm = Pendulum_GetArmAngle();
    g_armZeroDeg = arm;
    g_armPrevDeg = arm;
    g_armInit    = 1;
}

/* 摆角进入直立区: |theta| 接近 180° (取最近的 +180 或 -180 一支) */
uint8_t Balance_InZone(float theta_deg)
{
    float target = (theta_deg >= 0.0f) ? 180.0f : -180.0f;
    float dist   = target - theta_deg;
    return (fabsf(dist) < BAL_ZONE_DEG) ? 1u : 0u;
}

/* 每个控制节拍(5ms)调用: 双环串级 PID (A 式融合) -> 电机占空比 */
void Balance_Update(float theta_deg, float theta_dot_dps)
{
    /* --- 内环: 摆杆角度环 PD --- */
    /* 目标 = 竖直(取最近的 ±180 一支); err = target - theta; d(err)/dt = -theta_dot */
    float target = (theta_deg >= 0.0f) ? 180.0f : -180.0f;
    float err    = target - theta_deg;
    float inner  = g_bKp * err - g_bKd * theta_dot_dps;

    /* --- 外环: 臂位置环 PD (内部差分求臂角速度) --- */
    float arm = Pendulum_GetArmAngle();
    if (!g_armInit) { g_armZeroDeg = arm; g_armPrevDeg = arm; g_armInit = 1; }
    float armErr  = arm - g_armZeroDeg;
    float armRate = (arm - g_armPrevDeg) / CONTROL_TS;   /* 度/秒 */
    g_armPrevDeg  = arm;
    float outer   = g_pKp * armErr + g_pKd * armRate;

    /* --- A 式融合 + 方向 + 限幅(★int8_t 占空比) --- */
    float moto = (float)BAL_MOTOR_SIGN * (inner - outer);
    if (moto >  (float)BAL_PWM_LIMIT) moto =  (float)BAL_PWM_LIMIT;
    if (moto < -(float)BAL_PWM_LIMIT) moto = -(float)BAL_PWM_LIMIT;

    g_lastMoto = moto;
    Motor_SetSpeed((int8_t)moto);
}

float Balance_GetLastMoto(void) { return g_lastMoto; }
