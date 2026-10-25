/**
 * @file    motor_pid.c
 * @brief   Step 5: 每电机独立前馈 + PI 速度闭环
 *
 *          PWM_i = FF(target_rpm_i) + PI_speed_i(e_speed_i)
 *
 *          前馈负责"达到该速度大约需要多少 PWM"
 *          PI 只修正剩余误差, 启动快、积分负担轻
 */

#include "motor_pid.h"
#include "ti_msp_dl_config.h"
#include "hardware/motor_ctrl.h"
#include "hardware/Encoder.h"
#include "Chassis/vehicle_param.h"

/* ================================================================
 * 目标 RPM 存储
 * ================================================================ */

static float g_target_rpm[4];

/* 四路独立 PI 控制器 */
typedef struct {
    float Kp, Ki;
    float integral;
    float prev_error;
} PI_t;

static PI_t g_pi[4];

/* ================================================================
 * 限幅
 * ================================================================ */

static float Clamp(float v, float lo, float hi)
{
    if (v > hi) return hi;
    if (v < lo) return lo;
    return v;
}

/* ================================================================
 * 初始化
 * ================================================================ */

void Motor_PID_Init(void)
{
    for (int i = 0; i < 4; i++)
    {
        g_target_rpm[i]   = 0.0f;
        g_pi[i].Kp        = MOTOR_KP;
        g_pi[i].Ki        = MOTOR_KI;
        g_pi[i].integral  = 0.0f;
        g_pi[i].prev_error = 0.0f;
    }
}

/* ================================================================
 * 设置目标 RPM
 * ================================================================ */

void Motor_SetTargetRPM(MotorIndex_t motor, float rpm)
{
    if (motor < 4)
        g_target_rpm[motor] = rpm;
}

/* ================================================================
 * 前馈 + PI 更新 + PWM 输出
 *
 *   ① 前馈 PWM = target_rpm × FF_GAIN         (粗估)
 *   ② target_mm_s = target_rpm × RPM_TO_MMS   (换算单位)
 *   ③ e = target_mm_s - measure_mm_s          (速度误差)
 *   ④ PI 修正 = Kp×e + Ki×∫e                  (微调)
 *   ⑤ PWM = 前馈 + PI修正                     (最终输出)
 * ================================================================ */

void Motor_PID_Update(void)
{
    /* 四路速度 (编码器实测, mm/s) */
    float measure[4] = {
        Motor1_Speed,
        Motor2_Speed,
        Motor3_Speed,
        Motor4_Speed
    };

    int pwm[4];

    for (int i = 0; i < 4; i++)
    {
        float target = g_target_rpm[i];

        /* ── 前馈 ── */
        float ff = target * MOTOR_FF_GAIN;

        /* ── PI 修正: RPM≈PWM, 小增益处理单位差异 ── */
        float error = target - measure[i];

        g_pi[i].integral += g_pi[i].Ki * error;
        g_pi[i].integral  = Clamp(g_pi[i].integral, -200.0f, 200.0f);

        float pi_out = g_pi[i].Kp * error + g_pi[i].integral;

        g_pi[i].prev_error = error;

        /* ── PWM = 前馈 + 修正 ── */
        float out = ff + pi_out;
        out = Clamp(out, -2000.0f, 2000.0f);
        pwm[i] = (int)out;
    }

    /* 输出到四路电机 (LF, RF, LR, RR) */
    SET_MOTORS_SPEED(pwm[0], pwm[1], pwm[2], pwm[3]);
}

/* ================================================================
 * 使能/禁用
 * ================================================================ */

void Motor_Enable(void)  { MOTORS_ENABLE(); }
void Motor_Disable(void) { MOTORS_DISABLE(); }

/* ================================================================
 * 获取当前速度
 * ================================================================ */

float Motor_GetSpeed(MotorIndex_t motor)
{
    switch (motor)
    {
    case MOTOR_LF: return Motor1_Speed;
    case MOTOR_LR: return Motor3_Speed;
    case MOTOR_RF: return Motor2_Speed;
    case MOTOR_RR: return Motor4_Speed;
    default:       return 0.0f;
    }
}
