/**
 * @file    keypad.h
 * @brief   4×4 矩阵键盘驱动 (多端口)
 *          行: PB25, PA24, PA14, PA16 (输出)
 *          列: PA22, PA2, PA26, PB21 (输入, 内部上拉)
 *          扫描放在 10ms 任务中, 消抖需连续 2 次一致 (20ms)
 *
 *          键盘布局:
 *             C1   C2   C3   C4
 *          R1 key1 key2 key3 key4
 *          R2 key5 key6 key7 key8
 *          R3 key9 key10 key11 key12
 *          R4 key13 key14 key15 key16
 */

#ifndef __KEYPAD_H__
#define __KEYPAD_H__

#include <stdint.h>
#include <stdbool.h>

#define KEYPAD_NO_KEY   0       /* 无按键 */

void     Keypad_Init(void);
uint8_t  Keypad_Scan(void);     /* 驱动消抖状态机 (每10ms调用), 返回当前键号 */
uint8_t  Keypad_GetKey(void);   /* 返回当前按下的键号 1~16, 0=无按键 */
bool     Keypad_IsPressed(void);/* 有键按下返回 true */
uint8_t  Keypad_Read(void);     /* 扫描并返回键号 1~16 */

extern volatile uint8_t debug_raw;     /* 调试: 最近一次 raw 扫描值 */
extern volatile uint8_t debug_stable;  /* 调试: 消抖后的 stable_key */

#endif /* __KEYPAD_H__ */
