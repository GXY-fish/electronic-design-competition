/**
 * @file    vehicle_track.c
 * @brief   Step 2+3+4: PD转向 → 弯道降速 → 差速分配
 *
 *   Step2: yaw_rate = Kp × e_line + Kd × de/dt   (PD, 无 I)
 *   Step3: base     = max - slow_gain × |e_line|  (弯道降速)
 *   Step4: left     = base + yaw_rate
 *          right    = base - yaw_rate
 */

#include "vehicle_track.h"
#include "vehicle.h"
#include "line_sensor.h"
#include <math.h>

static float Clamp(float v, float lo, float hi)
{
    if (v > hi) return hi;
    if (v < lo) return lo;
    return v;
}

/* ================================================================
 * 状态判断
 * ================================================================ */

void State_Track(void)
{
    if (!g_line.valid)
    {
        Vehicle_ChangeState(VEH_LOST_HOLD);
        return;
    }

    if (g_line.error > 0)
        g_vehicle.last_side = 1;
    else
        g_vehicle.last_side = -1;
}

/* ================================================================
 * Step 2+3+4
 * ================================================================ */

void Ctrl_Track(void)
{
    float e  = g_line.error;       /* e_line, 范围 ±7 */
    float de = g_line.derivative;  /* 误差变化率 */

#if 0  /* 测试模式: 先确认电机差速能转弯 */
    if (e > 0.5f) {
        /* 线在右边 → 右转 */
        g_vehicle.left_target  = 350;
        g_vehicle.right_target = 0;
    } else if (e < -0.5f) {
        /* 线在左边 → 左转 */
        g_vehicle.left_target  = 0;
        g_vehicle.right_target = 350;
    } else {
        /* 居中 → 直走 */
        g_vehicle.left_target  = 200;
        g_vehicle.right_target = 200;
    }
#else
    /* ── Step 2: PD 目标角速度 ── */
    float turn = LINE_KP * e + LINE_KD * de;
    turn = Clamp(turn, -MAX_TURN_RPM, MAX_TURN_RPM);

    /* ── Step 3: 弯道自动降速 ── */
    float base = TRACK_MAX_RPM - CURVE_SLOW_GAIN * fabsf(e);
    base = Clamp(base, TRACK_MIN_RPM, TRACK_MAX_RPM);

    /* ── Step 4: 差速分配 + 内侧保底 ── */
    float left  = base + turn;
    float right = base - turn;

    /* 内侧轮最低转速: 防止 PWM 太低转不动变成刹车 */
    #define INNER_MIN 100.0f  /* 内侧最低转速 (x2.5) */
    if (left > 0 && left < INNER_MIN)   left  = INNER_MIN;
    if (right > 0 && right < INNER_MIN) right = INNER_MIN;
    if (left < 0 && left > -INNER_MIN)  left  = 0.0f;
    if (right < 0 && right > -INNER_MIN) right = 0.0f;

    g_vehicle.left_target  = left;
    g_vehicle.right_target = right;
#endif
}

void Ctrl_Track_Init(void) {}
