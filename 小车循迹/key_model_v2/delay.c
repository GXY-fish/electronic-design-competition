/**
 * @file    delay.c
 * @brief   延时函数 + 毫秒计数器
 */

#include "delay.h"

static volatile uint32_t ms_tick = 0;

void delay_tick_inc(void)
{
    ms_tick++;
}

uint32_t delay_ms_gettick(void)
{
    return ms_tick;
}

void delay_ms(uint32_t ms)
{
    delay_cycles(ms * (CPUCLK_FREQ / 1000));
}

void delay_us(uint32_t us)
{
    delay_cycles(us * (CPUCLK_FREQ / 1000000));
}
