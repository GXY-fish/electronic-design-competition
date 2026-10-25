/**
 * @file    key.h
 * @brief   2×2 矩阵键盘
 *          R1=PA14  R2=PA16  C1=PB20  C2=PB25
 *
 *          PB20(C1) PB25(C2)
 *   PA14(R1) KEY1    KEY2
 *   PA16(R2) KEY3    KEY4
 */
#ifndef __KEY_H
#define __KEY_H
#include <stdint.h>
#define KEY1  0
#define KEY2  1
#define KEY3  2
#define KEY4  3
void Key_Init(void);
void Key_Scan(void);
uint8_t Key_Pressed(uint8_t id);
#endif
