/**
 * @file    motor_pid.h
 * @brief   四路电机 PID 速度控制 — 统一接口
 *          LF=左前 LR=左后 RF=右前 RR=右后
 */

#ifndef __MOTOR_PID_H
#define __MOTOR_PID_H

#include <stdint.h>

/* 电机索引 */
typedef enum
{
    MOTOR_LF = 0,   /* 左前 M1 → s1 */
    MOTOR_RF = 1,   /* 右前 M2 → s2 */
    MOTOR_LR = 2,   /* 左后 M3 → s3 */
    MOTOR_RR = 3    /* 右后 M4 → s4 */
} MotorIndex_t;

void Motor_PID_Init(void);
void Motor_SetTargetRPM(MotorIndex_t motor, float rpm);
void Motor_PID_Update(void);   /* 运行 PID → 输出 PWM */

/* 使能/禁用全部电机 */
void Motor_Enable(void);
void Motor_Disable(void);

/* 获取当前速度 (调试用) */
float Motor_GetSpeed(MotorIndex_t motor);

#endif /* __MOTOR_PID_H__ */
