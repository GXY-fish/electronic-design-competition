#include "pid.h"

void PD_Init(PD_Controller *pd, float kp, float kd, float out_min, float out_max)
{
    pd->kp = kp;
    pd->kd = kd;
    pd->out_min = out_min;
    pd->out_max = out_max;
    pd->output = 0.0f;
}

float PD_Compute(PD_Controller *pd, float error, float velocity)
{
    float output = pd->kp * error - pd->kd * velocity;

    // 钳位输出
    if (output > pd->out_max) output = pd->out_max;
    if (output < pd->out_min) output = pd->out_min;

    pd->output = output;
    return output;
}

void PD_Reset(PD_Controller *pd)
{
    pd->output = 0.0f;
}
