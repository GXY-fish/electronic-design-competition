/**
 * @file    delay.h
 * @brief   延时函数 + 毫秒计数器 (CPUCLK_FREQ = 32MHz)
 */

#ifndef __DELAY_H__
#define __DELAY_H__

#include "main.h"

void     delay_us(uint32_t us);
void     delay_ms(uint32_t ms);
void     delay_tick_inc(void);       /* 由 1ms ISR 调用 */
uint32_t delay_ms_gettick(void);     /* 获取当前毫秒计数 */

#endif /* __DELAY_H__ */
