/**
 * @file    xunji.h
 * @brief   八路红外巡线传感器驱动 — 亚博红外传感巡线模块
 *
 *          通讯方式:  GPIO 直读 (8路, 内部上拉)
 *          算法:      加权质心法 + PD 差速控制 (适配四驱)
 *          传感器值:  0 = 检测到黑线, 1 = 白色/无线
 *          巡线算法:  模式匹配 + PD 差速控制 (适配四驱)
 */

#ifndef __XUNJI_H__
#define __XUNJI_H__

#include "main.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ================================================================
 * 传感器驱动 API
 * ================================================================ */

void    XJ_Init(void);                       /* 初始化 I2C + 传感器 */
void    XJ_Update(void);                     /* 读取传感器数据 (I2C) */
uint8_t XJ_GetValue(uint8_t index);          /* 读单路传感器: 0=黑线, 1=白底 */
uint8_t XJ_GetAllChannels(void);             /* 读全部 8 路 (bit7=X1, bit0=X8) */
uint8_t XJ_DataUpdated(void);               /* 返回 1 表示数据已更新 */

/* ================================================================
 * 巡线控制 API
 * ================================================================ */

void XJ_LineFollowing_Init(void);            /* 初始化巡线 PID */
void XJ_LineFollowing_Update(void);          /* 巡线 PD 控制 (10ms 周期) */

void XJ_PID_SetTunings(float Kp, float Ki, float Kd);
void XJ_PID_GetTunings(float *Kp, float *Ki, float *Kd);

/* ================================================================
 * 巡线全局参数
 * ================================================================ */

extern uint8_t xj_enable;                    /* 1=启用巡线模式 */
extern float   xj_base_speed;               /* 巡线基础速度 (PWM值 0~1000) */
extern int16_t xj_error;                    /* 当前偏差×10 (供调试查看) */

/* 调试计数器 */
extern volatile uint32_t g_xj_read_ok;       /* I2C 读取成功次数 */
extern volatile uint32_t g_xj_read_fail;     /* I2C 读取超时次数 */
extern volatile uint32_t g_xj_ctrl_call;     /* 控制函数调用次数 */

#ifdef __cplusplus
}
#endif

#endif /* __XUNJI_H__ */
