#ifndef __BOARD_H__
#define __BOARD_H__

#include "ti_msp_dl_config.h"
#include "oled.h"
#include "key.h"
#include "menu.h"
//#include "MPU6050.h"
#include "bsp_siic.h"
#include "moter.h"
#include "encoder.h"
#include "weite.h"
#include "imu.h"
//任意串口printf
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
#include <math.h>

//Systick最大计数值,24位
#define SysTickMAX_COUNT 0xFFFFFF

//Systick计数频率
#define SysTickFre 80000000

//将systick的计数值转换为具体的时间单位
#define SysTick_MS(x)  ((SysTickFre/1000U)*(uint32_t)(x))
#define SysTick_US(x)  ((SysTickFre/1000000U)*(uint32_t)(x))

void board_init(void);

void delay_us(unsigned long __us);
void delay_ms(unsigned long ms);
void delay_1us(unsigned long __us);
void delay_1ms(unsigned long ms);

void any_printf(UART_Regs *uart,char *format,...);

#endif