/**
 * @file    Encoder.h
 * @brief   4 通道编码器驱动 — 8 个 GPIOB 中断引脚
 *          E1:PB0/PB1→M1, E2:PB2/PB3→M2, E3:PB4/PB5→M3, E4:PB12/PB13→M4
 */

#ifndef __ENCODER_H__
#define __ENCODER_H__

#include "main.h"

/* ===== 编码器/车轮参数 (按实际调整) ===== */
#define CPR           780       /* 轮子转一圈的编码器计数 */
#define DIAMETER_MM   65.0f     /* 轮子直径 mm */
#define PI            3.1415f
#define SAMPLE_TIME   0.01f     /* 采样周期 10ms (秒) */

/* 轮子周长 mm */
#define WHEEL_CIRCUM  (PI * DIAMETER_MM)

/* 编码器引脚读取宏 */
#define Read_Encoder_E1A  ((DL_GPIO_readPins(Encoder_PORT, Encoder_E1A_PIN) == Encoder_E1A_PIN) ? 0 : 1)
#define Read_Encoder_E1B  ((DL_GPIO_readPins(Encoder_PORT, Encoder_E1B_PIN) == Encoder_E1B_PIN) ? 0 : 1)
#define Read_Encoder_E2A  ((DL_GPIO_readPins(Encoder_PORT, Encoder_E2A_PIN) == Encoder_E2A_PIN) ? 0 : 1)
#define Read_Encoder_E2B  ((DL_GPIO_readPins(Encoder_PORT, Encoder_E2B_PIN) == Encoder_E2B_PIN) ? 0 : 1)
#define Read_Encoder_E3A  ((DL_GPIO_readPins(Encoder_PORT, Encoder_E3A_PIN) == Encoder_E3A_PIN) ? 0 : 1)
#define Read_Encoder_E3B  ((DL_GPIO_readPins(Encoder_PORT, Encoder_E3B_PIN) == Encoder_E3B_PIN) ? 0 : 1)
#define Read_Encoder_E4A  ((DL_GPIO_readPins(Encoder_PORT, Encoder_E4A_PIN) == Encoder_E4A_PIN) ? 0 : 1)
#define Read_Encoder_E4B  ((DL_GPIO_readPins(Encoder_PORT, Encoder_E4B_PIN) == Encoder_E4B_PIN) ? 0 : 1)

/* 电机速度 (mm/s) */
extern float Motor1_Speed;
extern float Motor2_Speed;
extern float Motor3_Speed;
extern float Motor4_Speed;
extern float Measure_Distance;

/* 编码器原始累计值 (用于串口查看) */
extern int32_t Motor1_Encoder_Value;
extern int32_t Motor2_Encoder_Value;
extern int32_t Motor3_Encoder_Value;
extern int32_t Motor4_Encoder_Value;

/* ISR 触发次数 (诊断: M1/M2/M3/M4 各触发了多少次中断) */
extern volatile uint32_t g_enc_isr_cnt[4];

void Motor1_Get_Speed(void);
void Motor2_Get_Speed(void);
void Motor3_Get_Speed(void);
void Motor4_Get_Speed(void);
void MEASURE_MOTORS_SPEED(void);

#endif /* __ENCODER_H__ */
