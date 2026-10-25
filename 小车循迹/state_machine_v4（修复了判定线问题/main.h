/**
 * @file    main.h
 * @brief   wheel_4 四驱小车主头文件
 *          天猛星 MSPM0G3507 (LQFP-64)
 */

#ifndef __MAIN_H__
#define __MAIN_H__

#include "ti_msp_dl_config.h"

/* 标准库 */
#include "stdbool.h"
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>

/* 类型定义 */
typedef int32_t  s32;
typedef int16_t  s16;
typedef int8_t   s8;
typedef const int32_t sc32;
typedef const int16_t sc16;
typedef const int8_t  sc8;
typedef __IO int32_t  vs32;
typedef __IO int16_t  vs16;
typedef __IO int8_t   vs8;
typedef __I int32_t   vsc32;
typedef __I int16_t   vsc16;
typedef __I int8_t    vsc8;
typedef uint32_t  u32;
typedef uint16_t  u16;
typedef uint8_t   u8;
typedef const uint32_t uc32;
typedef const uint16_t uc16;
typedef const uint8_t  uc8;
typedef __IO uint32_t  vu32;
typedef __IO uint16_t vu16;
typedef __IO uint8_t  vu8;
typedef __I uint32_t  vuc32;
typedef __I uint16_t  vuc16;
typedef __I uint8_t   vuc8;
typedef float  fp32;
typedef double fp64;

/* 全局函数声明 */
void NVIC_EnableIRQ_Init(void);

/* 全局变量 */
extern volatile uint32_t g_msTick;
extern volatile uint8_t  g_lap_done;
extern float Basic_Speed;
extern float Target_Distance;
extern uint8_t Car_Mode;

/* 小车模式 */
#define Run_Mode        0
#define Speed_Mode      1
#define Turn_Mode       2
#define Distance_Mode   3
#define Xunji_Mode      4   /* 红外巡线模式 */

#endif /* __MAIN_H__ */
