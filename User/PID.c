/**
 * @file    PID.c
 * @brief   通用位置式 PID 控制器实现
 *
 * 位置式公式:  Out = Kp*e + Ki*∑e + Kd*(e - e_prev)
 *   - 积分项做了"Ki=0 即清零"处理, 便于分步调参(先调P, 此时积分不会空积累到饱和)。
 *   - 输出统一走 Clamp 限幅, 防止执行器被打到超范围。
 */
#include "PID.h"

/* 输出限幅小工具: 把 v 夹在 [lo, hi] 内 */
static float Clamp(float v, float lo, float hi)
{
    if (v > hi) return hi;
    if (v < lo) return lo;
    return v;
}

void PID_Init(PID_t *pid, float kp, float ki, float kd,
              float target, float outMin, float outMax)
{
    pid->Kp     = kp;
    pid->Ki     = ki;
    pid->Kd     = kd;
    pid->Target = target;
    pid->OutMin = outMin;
    pid->OutMax = outMax;

    pid->Actual = 0;
    pid->Out    = 0;
    PID_Reset(pid);         // 清内部状态
}

void PID_Reset(PID_t *pid)
{
    pid->prevErr  = 0;
    pid->integral = 0;
}

float PID_Compute(PID_t *pid)
{
    float err = pid->Target - pid->Actual;      // 本次误差 = 目标 - 实际

    /* 积分项: Ki 为 0 时直接清零, 避免调试阶段误差空积累造成积分饱和 */
    if (pid->Ki != 0) pid->integral += err;
    else              pid->integral  = 0;

    /* 位置式 PID: 比例 + 积分 + 微分(对误差做一阶差分) */
    pid->Out = pid->Kp * err
             + pid->Ki * pid->integral
             + pid->Kd * (err - pid->prevErr);

    pid->prevErr = err;                          // 保存本次误差, 供下次算微分
    pid->Out = Clamp(pid->Out, pid->OutMin, pid->OutMax);   // 输出限幅
    return pid->Out;
}
