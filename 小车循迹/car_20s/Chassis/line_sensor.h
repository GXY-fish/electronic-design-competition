/**
 * @file    line_sensor.h
 * @brief   八路红外巡线传感器 — 加权质心法
 *           X1=PB6 X2=PB7 X3=PB8 X4=PB9 X5=PB10 X6=PB11 X7=PB14 X8=PB19
 */

#ifndef __LINE_SENSOR_H
#define __LINE_SENSOR_H

#include <stdint.h>

/* 传感器数据结构 */
typedef struct
{
    float   error;       /* 位置偏差 (-7 ~ +7), 正=偏右 */
    float   derivative;  /* 偏差变化率 */
    uint8_t valid;       /* 1 = 检测到线, 0 = 丢线 */
} LineSensor_t;

extern LineSensor_t g_line;

void LineSensor_Init(void);
void LineSensor_Update(void);

/* 获取原始传感器值 (调试用) */
uint8_t LineSensor_GetChannel(uint8_t index);
uint8_t LineSensor_GetAllChannels(void);

#endif /* __LINE_SENSOR_H__ */
