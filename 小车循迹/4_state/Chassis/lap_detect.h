/**
 * @file    lap_detect.h
 * @brief   圈数检测 — 5cm 黑胶布标记识别
 *
 *          正常循迹: 中间 2~3 路红外检测到黑线
 *          经过黑胶布: 中间 6 路红外同时检测到黑 (全遮)
 *
 *          track_bits 约定: 0=检测到黑, 1=白
 *          MARKER_MASK = 0x7E 对应 X2 X3 X4 X5 X6 X7 (bits 6-1)
 *          6 路全黑 ⇔ (track_bits & 0x7E) == 0x00
 */
#ifndef __LAP_DETECT_H
#define __LAP_DETECT_H

#include <stdint.h>

/* 中间 6 路红外: X2 X3 X4 X5 X6 X7 → bits 6-1 */
#define MARKER_MASK  0x7E

typedef struct {
    uint8_t LapCount;      /* 已检测到的圈数 (经过胶布次数) */
    uint8_t MarkerFlag;    /* 本轮已触发 (防重复计数) */
    uint8_t MarkerCnt;     /* 连续检测到胶布的周期数 */
} LapDetect_t;

extern LapDetect_t Lap;

void    LapDetect_Init(void);
void    LapDetect_Reset(void);
void    LapDetect_Task(void);       /* 每 10ms 周期调用 */
uint8_t LapDetect_GetCount(void);   /* 返回 LapCount */

#endif /* __LAP_DETECT_H */
