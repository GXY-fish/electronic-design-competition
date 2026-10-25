#ifndef BALL_CONTROL_H
#define BALL_CONTROL_H

#include <stdbool.h>

typedef struct {
    float alpha;
    float beta;
    float kp_deg_per_mm;
    float kd_deg_per_mm_s;
    float ki_deg_per_mm_s;
    float theta_limit_deg;
    float theta_step_per_20ms_deg;
    float integral_limit_deg;
    float integral_window_mm;
    float integral_speed_window_mm_s;
    float speed_limit_mm_s;
} BallControlConfig;

typedef struct {
    BallControlConfig config;
    float x_est_mm;
    float v_est_mm_s;
    float integral_angle_deg;
    float last_theta_cmd_deg;
    float last_target_mm;
    bool filter_initialized;
    bool target_initialized;
    bool last_saturated;
} BallControl;

typedef struct {
    float x_mm;
    float v_mm_s;
    float error_mm;
    float theta_raw_deg;
    float theta_target_deg;
    float theta_cmd_deg;
    bool saturated;
} BallControlOutput;

BallControlConfig BallControl_DefaultConfig(void);
void BallControl_Init(BallControl *control, const BallControlConfig *config);
void BallControl_Reset(BallControl *control, float x_mm);
BallControlOutput BallControl_Update(BallControl *control,
                                     float measured_x_mm,
                                     float target_x_mm,
                                     bool measurement_valid,
                                     float dt_s);
float BallControl_SlewToLevel(BallControl *control, float dt_s);

#endif
