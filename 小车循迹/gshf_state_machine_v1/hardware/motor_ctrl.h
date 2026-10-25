/**
 * @file    motor_ctrl.h
 * @brief   4 通道电机控制 + PID 控制器
 *          TIMA0 PWM: C0=PA0, C1=PA1, C2=PA15, C3=PB24
 *          Dir: M1(PA7/8), M2(PA12/13), M3(PB15/16), M4(PB17/18)
 */

#ifndef __MOTOR_CTRL_H__
#define __MOTOR_CTRL_H__

#include "main.h"

/* PID 结构体 */
typedef struct pid_t
{
    float Kp, Ki, Kd;
    float Target;
    float Measure;
    float Error[3];
    float KpOut, KiOut, KdOut;
    float PID_Out;
    uint32_t PID_Limit_MAX;
    uint32_t Ki_Limit_MAX;
} pid_t;

float PID_Calculate(pid_t *pid, float Measure, float Target);
void  Set_PID_Param(pid_t *pid, float P, float I, float D);

/* 电机使能 */
extern uint8_t MOTOR1_ENABLE_FLAG;
extern uint8_t MOTOR2_ENABLE_FLAG;
extern uint8_t MOTOR3_ENABLE_FLAG;
extern uint8_t MOTOR4_ENABLE_FLAG;

/* 使能/禁用宏 */
#define MOTORS_ENABLE()   { MOTOR1_ENABLE_FLAG=1;MOTOR2_ENABLE_FLAG=1;MOTOR3_ENABLE_FLAG=1;MOTOR4_ENABLE_FLAG=1; }
#define MOTORS_DISABLE()  { MOTOR1_ENABLE_FLAG=0;MOTOR2_ENABLE_FLAG=0;MOTOR3_ENABLE_FLAG=0;MOTOR4_ENABLE_FLAG=0; }
#define MOTORS_BRAKE()    { Motor1_Brake(); Motor2_Brake(); Motor3_Brake(); Motor4_Brake(); }

/* ---- Motor1 方向 ---- */
#define AIN1(x) (x ? DL_GPIO_setPins(Motor_Ctrl_A_PORT, Motor_Ctrl_A_AIN1_PIN) : DL_GPIO_clearPins(Motor_Ctrl_A_PORT, Motor_Ctrl_A_AIN1_PIN))
#define AIN2(x) (x ? DL_GPIO_setPins(Motor_Ctrl_A_PORT, Motor_Ctrl_A_AIN2_PIN) : DL_GPIO_clearPins(Motor_Ctrl_A_PORT, Motor_Ctrl_A_AIN2_PIN))
#define Motor1_Forward()   { AIN1(1); AIN2(0); }
#define Motor1_Backward()  { AIN1(0); AIN2(1); }
#define Motor1_Stop()      { AIN1(0); AIN2(0); }
#define Motor1_Brake()     { AIN1(1); AIN2(1); }  /* 短接制动 */

/* ---- Motor2 方向 (反转: 与 M1 同侧, 物理反向安装) ---- */
#define BIN1(x) (x ? DL_GPIO_setPins(Motor_Ctrl_A_PORT, Motor_Ctrl_A_BIN1_PIN) : DL_GPIO_clearPins(Motor_Ctrl_A_PORT, Motor_Ctrl_A_BIN1_PIN))
#define BIN2(x) (x ? DL_GPIO_setPins(Motor_Ctrl_A_PORT, Motor_Ctrl_A_BIN2_PIN) : DL_GPIO_clearPins(Motor_Ctrl_A_PORT, Motor_Ctrl_A_BIN2_PIN))
#define Motor2_Forward()   { BIN1(1); BIN2(0); }
#define Motor2_Backward()  { BIN1(0); BIN2(1); }
#define Motor2_Stop()      { BIN1(0); BIN2(0); }
#define Motor2_Brake()     { BIN1(1); BIN2(1); }

/* ---- Motor3 方向 ---- */
#define CIN1(x) (x ? DL_GPIO_setPins(Motor_Ctrl_B_PORT, Motor_Ctrl_B_CIN1_PIN) : DL_GPIO_clearPins(Motor_Ctrl_B_PORT, Motor_Ctrl_B_CIN1_PIN))
#define CIN2(x) (x ? DL_GPIO_setPins(Motor_Ctrl_B_PORT, Motor_Ctrl_B_CIN2_PIN) : DL_GPIO_clearPins(Motor_Ctrl_B_PORT, Motor_Ctrl_B_CIN2_PIN))
#define Motor3_Forward()   { CIN1(0); CIN2(1); }
#define Motor3_Backward()  { CIN1(1); CIN2(0); }
#define Motor3_Stop()      { CIN1(0); CIN2(0); }
#define Motor3_Brake()     { CIN1(1); CIN2(1); }

/* ---- Motor4 方向 (硬件只能 LOW/HIGH 转, 方向在 Set_Motor4_Speed 里反转) ---- */
#define DIN1(x) (x ? DL_GPIO_setPins(Motor_Ctrl_B_PORT, Motor_Ctrl_B_DIN1_PIN) : DL_GPIO_clearPins(Motor_Ctrl_B_PORT, Motor_Ctrl_B_DIN1_PIN))
#define DIN2(x) (x ? DL_GPIO_setPins(Motor_Ctrl_B_PORT, Motor_Ctrl_B_DIN2_PIN) : DL_GPIO_clearPins(Motor_Ctrl_B_PORT, Motor_Ctrl_B_DIN2_PIN))
#define Motor4_Forward()   { DIN1(0); DIN2(1); }
#define Motor4_Backward()  { DIN1(1); DIN2(0); }
#define Motor4_Stop()      { DIN1(0); DIN2(0); }
#define Motor4_Brake()     { DIN1(1); DIN2(1); }

/* 函数声明 */
void Set_Motor1_Speed(int Target_Speed);
void Set_Motor2_Speed(int Target_Speed);
void Set_Motor3_Speed(int Target_Speed);
void Set_Motor4_Speed(int Target_Speed);
void SET_MOTORS_SPEED(int s1, int s2, int s3, int s4);
void SET_MOTORS_SPEED_DIFF(int baseSpeed, int diff);

/* PID 实例 */
extern pid_t pid_Motor1_Speed;
extern pid_t pid_Motor2_Speed;
extern pid_t pid_Motor3_Speed;
extern pid_t pid_Motor4_Speed;
extern pid_t pid_Turn;
extern pid_t pid_Distance;

extern uint8_t Turn_PID_Flag;
extern uint8_t Distance_PID_Flag;

#endif /* __MOTOR_CTRL_H__ */
