#include "ball_control.h"

#include "ball_config.h"

#include <math.h>
#include <stddef.h>

static float clampf(float value, float low, float high)
{
    if (value < low) {
        return low;
    }
    if (value > high) {
        return high;
    }
    return value;
}

static float move_toward(float current, float target, float max_step)
{
    const float delta = target - current;
    if (delta > max_step) {
        return current + max_step;
    }
    if (delta < -max_step) {
        return current - max_step;
    }
    return target;
}

static float normalized_dt(float dt_s)
{
    return clampf(dt_s, 0.010f, 0.050f);
}

BallControlConfig BallControl_DefaultConfig(void)
{
    const BallControlConfig config = {
        .alpha = BALL_FILTER_ALPHA,
        .beta = BALL_FILTER_BETA,
        .kp_deg_per_mm = BALL_KP_DEG_PER_MM,
        .kd_deg_per_mm_s = BALL_KD_DEG_PER_MM_S,
        .ki_deg_per_mm_s = BALL_KI_DEG_PER_MM_S,
        .theta_limit_deg = BALL_THETA_LIMIT_DEG,
        .theta_step_per_20ms_deg = BALL_THETA_STEP_PER_20MS_DEG,
        .integral_limit_deg = BALL_INTEGRAL_LIMIT_DEG,
        .integral_window_mm = BALL_INTEGRAL_WINDOW_MM,
        .integral_speed_window_mm_s =
            BALL_INTEGRAL_SPEED_WINDOW_MM_S,
        .speed_limit_mm_s = BALL_SPEED_LIMIT_MM_S,
    };
    return config;
}

void BallControl_Init(BallControl *control, const BallControlConfig *config)
{
    if (control == NULL) {
        return;
    }

    control->config =
        (config != NULL) ? *config : BallControl_DefaultConfig();
    BallControl_Reset(control, 0.0f);
    control->filter_initialized = false;
}

void BallControl_Reset(BallControl *control, float x_mm)
{
    if (control == NULL) {
        return;
    }

    control->x_est_mm = x_mm;
    control->v_est_mm_s = 0.0f;
    control->integral_angle_deg = 0.0f;
    control->last_theta_cmd_deg = 0.0f;
    control->last_target_mm = 0.0f;
    control->filter_initialized = true;
    control->target_initialized = false;
    control->last_saturated = false;
}

BallControlOutput BallControl_Update(BallControl *control,
                                     float measured_x_mm,
                                     float target_x_mm,
                                     bool measurement_valid,
                                     float dt_s)
{
    BallControlOutput output = {0};
    float dt;
    float predicted_x;
    float error;
    float theta_raw;
    float theta_target;
    float max_step;

    if (control == NULL) {
        return output;
    }

    dt = normalized_dt(dt_s);

    if (!control->filter_initialized) {
        control->x_est_mm = measurement_valid ? measured_x_mm : 0.0f;
        control->v_est_mm_s = 0.0f;
        control->filter_initialized = true;
    } else {
        predicted_x = control->x_est_mm + control->v_est_mm_s * dt;
        if (measurement_valid) {
            const float residual = measured_x_mm - predicted_x;
            control->x_est_mm =
                predicted_x + control->config.alpha * residual;
            control->v_est_mm_s +=
                (control->config.beta / dt) * residual;
            control->v_est_mm_s =
                clampf(control->v_est_mm_s,
                       -control->config.speed_limit_mm_s,
                       control->config.speed_limit_mm_s);
        } else {
            control->x_est_mm = predicted_x;
        }
    }

    if (!control->target_initialized ||
        (fabsf(target_x_mm - control->last_target_mm) > 0.001f)) {
        control->integral_angle_deg = 0.0f;
        control->last_target_mm = target_x_mm;
        control->target_initialized = true;
    }

    error = control->x_est_mm - target_x_mm;

    if ((control->config.ki_deg_per_mm_s != 0.0f) &&
        (fabsf(error) < control->config.integral_window_mm) &&
        (fabsf(control->v_est_mm_s) <
         control->config.integral_speed_window_mm_s) &&
        !control->last_saturated) {
        control->integral_angle_deg +=
            control->config.ki_deg_per_mm_s * error * dt;
        control->integral_angle_deg =
            clampf(control->integral_angle_deg,
                   -control->config.integral_limit_deg,
                   control->config.integral_limit_deg);
    }

    theta_raw =
        control->config.kp_deg_per_mm * error +
        control->config.kd_deg_per_mm_s * control->v_est_mm_s +
        control->integral_angle_deg;
    theta_target =
        clampf(theta_raw,
               -control->config.theta_limit_deg,
               control->config.theta_limit_deg);
    control->last_saturated = fabsf(theta_target - theta_raw) > 0.0001f;

    max_step =
        control->config.theta_step_per_20ms_deg *
        (dt / BALL_CONTROL_PERIOD_S);
    control->last_theta_cmd_deg =
        move_toward(control->last_theta_cmd_deg, theta_target, max_step);

    output.x_mm = control->x_est_mm;
    output.v_mm_s = control->v_est_mm_s;
    output.error_mm = error;
    output.theta_raw_deg = theta_raw;
    output.theta_target_deg = theta_target;
    output.theta_cmd_deg = control->last_theta_cmd_deg;
    output.saturated = control->last_saturated;
    return output;
}

float BallControl_SlewToLevel(BallControl *control, float dt_s)
{
    float max_step;

    if (control == NULL) {
        return 0.0f;
    }

    max_step =
        control->config.theta_step_per_20ms_deg *
        (normalized_dt(dt_s) / BALL_CONTROL_PERIOD_S);
    control->last_theta_cmd_deg =
        move_toward(control->last_theta_cmd_deg, 0.0f, max_step);
    control->integral_angle_deg = 0.0f;
    control->target_initialized = false;
    return control->last_theta_cmd_deg;
}
