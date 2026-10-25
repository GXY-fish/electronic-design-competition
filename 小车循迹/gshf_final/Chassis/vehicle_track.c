/**
 * @file    vehicle_track.c
 * @brief   Step 2+3+4: PD转向 → 弯道降速 → 差速分配
 *
 *   T2(key1): 原始竞速逻辑, 对标 speed_test
 *   T5/T6(key3/4): 运货稳定逻辑 (死区+EMA平滑)
 *
 *   Step2: yaw_rate = Kp × e_line + Kd × de/dt   (PD, 无 I)
 *   Step3: base     = max - slow_gain × |e_line|  (弯道降速)
 *   Step4: left     = base + yaw_rate
 *          right    = base - yaw_rate
 */

#include "vehicle_track.h"
#include "vehicle.h"
#include "line_sensor.h"
#include "app_state.h"
#include <math.h>

extern float Basic_Speed;

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
 * Ctrl_Track — 双路径
 *   T2: 对标 speed_test 原始逻辑
 *   T5/T6: 运货稳定逻辑
 * ================================================================ */

void Ctrl_Track(void)
{
    float e  = g_line.error;       /* e_line, 范围 ±7 */
    float de = g_line.derivative;  /* 误差变化率 */

#if 0  /* 测试模式: 先确认电机差速能转弯 */
    if (e > 0.5f) {
        g_vehicle.left_target  = 350;
        g_vehicle.right_target = 0;
    } else if (e < -0.5f) {
        g_vehicle.left_target  = 0;
        g_vehicle.right_target = 350;
    } else {
        g_vehicle.left_target  = 200;
        g_vehicle.right_target = 200;
    }
#else

    if (Current_State == STATE_T5_SLOW_TRACK ||
        Current_State == STATE_T6_SLOW_TEST ||
        Current_State == STATE_T7_SLOW_TRACK)
    {
        /* ============================================================
         * T5/T6 运货稳定逻辑
         * ============================================================ */

        /* ── Step 2: PD 转向 (降灵敏度 + 强阻尼) ── */
        float turn = SLOW_LINE_KP * e + SLOW_LINE_KD * de;
        turn = Clamp(turn, -SLOW_MAX_TURN, SLOW_MAX_TURN);

        /* ── Step 3: 弯道降速 (直道死区 + 逐步降速) ── */
        float s = Basic_Speed / 75.0f;
        float max_rpm = TRACK_MAX_RPM * s;
        float min_rpm = SLOW_MIN_RPM * s;
        float abs_e = fabsf(e);
        float base;
        if (abs_e < SLOW_DEADBAND) {
            base = max_rpm;     /* 直道/小偏差: 恒定全速 */
        } else {
            base = max_rpm - SLOW_CURVE_GAIN * s * (abs_e - SLOW_DEADBAND);
            base = Clamp(base, min_rpm, max_rpm);
        }

        /* ── Step 4: 差速分配 ── */
        float left  = base + turn;
        float right = base - turn;

        float inner_min = INNER_MIN_RPM * s;
        if (left > 0 && left < inner_min)   left  = inner_min;
        if (right > 0 && right < inner_min) right = inner_min;
        if (left < 0 && left > -inner_min)  left  = 0.0f;
        if (right < 0 && right > -inner_min) right = 0.0f;

        if (left  > max_rpm) left  = max_rpm;
        if (right > max_rpm) right = max_rpm;

        /* ── EMA 低通滤波: 平滑起步 + 直弯过渡 ── */
        {
            static float filt_left  = 0.0f;
            static float filt_right = 0.0f;

            filt_left  += SLOW_EMA_ALPHA * (left  - filt_left);
            filt_right += SLOW_EMA_ALPHA * (right - filt_right);

            left  = filt_left;
            right = filt_right;
        }

        g_vehicle.left_target  = left;
        g_vehicle.right_target = right;
    }
    else
    {
        /* ============================================================
         * T2 原始竞速逻辑 — 对标 speed_test
         * ============================================================ */

        /* ── Step 2: PD 转向 ── */
        float turn = LINE_KP * e + LINE_KD * de;
        turn = Clamp(turn, -MAX_TURN_RPM, MAX_TURN_RPM);

        /* ── Step 3: 弯道自动降速 (随 Basic_Speed 缩放) ── */
        float s = Basic_Speed / 75.0f;
        float max_rpm = TRACK_MAX_RPM * s;
        float min_rpm = TRACK_MIN_RPM * s;
        float base = max_rpm - CURVE_SLOW_GAIN * s * fabsf(e);
        base = Clamp(base, min_rpm, max_rpm);

        /* ── Step 4: 差速分配 ── */
        float left  = base + turn;
        float right = base - turn;

        /* 内侧轮最低转速 */
        #define INNER_MIN 100.0f
        if (left > 0 && left < INNER_MIN)   left  = INNER_MIN;
        if (right > 0 && right < INNER_MIN) right = INNER_MIN;
        if (left < 0 && left > -INNER_MIN)  left  = 0.0f;
        if (right < 0 && right > -INNER_MIN) right = 0.0f;

        g_vehicle.left_target  = left;
        g_vehicle.right_target = right;
    }
#endif
}

void Ctrl_Track_Init(void) {}
