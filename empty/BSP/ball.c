#include "ball.h"

/* 丢球超时: 200ms */
#define LOST_TIMEOUT_MS  200

/* 舵机安全范围 (根据实测: 10°水平, 80°球往正向快滚, 0°球往负向快滚) */
#define SERVO_SAFE_MIN   0
#define SERVO_SAFE_MAX   85

/**
 * @brief 绝对值 (整数)
 */
static int iabs(int x)
{
    return (x < 0) ? -x : x;
}

void Ball_Init(BallControl *ball, float kp, float kd, int baseline_angle)
{
    // PD 输出范围: 从 baseline 往两边到安全极限
    // servo = baseline + pd_out, 最终钳位到 [servo_min, servo_max]
    float pd_neg = (float)(SERVO_SAFE_MIN - baseline_angle);  // 负向极限
    float pd_pos = (float)(SERVO_SAFE_MAX - baseline_angle);  // 正向极限

    PD_Init(&ball->pd, kp, kd, pd_neg, pd_pos);

    ball->target_mm     = 0.0f;
    ball->current_mm    = 0;
    ball->current_v     = 0;
    ball->servo_angle   = baseline_angle;
    ball->baseline_angle = baseline_angle;
    ball->servo_min     = SERVO_SAFE_MIN;
    ball->servo_max     = SERVO_SAFE_MAX;
    ball->lost_ms       = 0;
    ball->stable_cnt    = 0;
    ball->ball_valid    = 0;
    ball->pd_enabled    = 1;
}

void Ball_UpdatePosition(BallControl *ball, int x_mm, int v_mm_s, uint8_t valid)
{
    ball->current_mm = x_mm;
    ball->current_v  = v_mm_s;
    ball->ball_valid = (valid != 0);

    if (ball->ball_valid) {
        ball->lost_ms = 0;
    }
}

void Ball_SetReference(BallControl *ball, float target_mm)
{
    ball->target_mm = target_mm;
    ball->stable_cnt = 0;
}

int Ball_Compute(BallControl *ball)
{
    if (!ball->pd_enabled || !ball->ball_valid) {
        // PD 未使能或丢球: 保持当前角度
        return ball->servo_angle;
    }

    // 位置误差 (mm)
    float error = ball->target_mm - (float)ball->current_mm;

    // PD 计算
    float pd_out = PD_Compute(&ball->pd, error, (float)ball->current_v);

    // 最终舵机角度 = 基准水平角度 + PD 修正
    int servo = ball->baseline_angle + (int)pd_out;

    // 钳位到安全范围
    if (servo < ball->servo_min) servo = ball->servo_min;
    if (servo > ball->servo_max) servo = ball->servo_max;

    ball->servo_angle = servo;
    return servo;
}

int Ball_IsStable(BallControl *ball, float err_thresh_mm,
                  float vel_thresh_mm_s, int dur_frames)
{
    float error = ball->target_mm - (float)ball->current_mm;
    float abs_err  = (error < 0.0f) ? -error : error;
    float abs_vel  = (ball->current_v < 0) ? (float)(-ball->current_v)
                                           : (float)ball->current_v;

    if (abs_err < err_thresh_mm && abs_vel < vel_thresh_mm_s) {
        ball->stable_cnt++;
        if (ball->stable_cnt >= dur_frames)
            return 1;
    } else {
        ball->stable_cnt = 0;
    }
    return 0;
}

void Ball_LostProtect(BallControl *ball)
{
    /* 丢球立刻回中, 防止舵机保持上次角度导致水管大幅倾斜 */
    ball->servo_angle = ball->baseline_angle;

    /* 丢球超时则禁用 PD (PD 在 Ball_UpdatePosition 收到有效帧时自动恢复) */
    ball->lost_ms += 30;  // ~33fps 每帧约 30ms
    if (ball->lost_ms > LOST_TIMEOUT_MS) {
        ball->pd_enabled = 0;
        ball->lost_ms = 0;
    }
}
