/**
 * @file    lap_detect.c
 * @brief   圈数检测实现 — 连续判定 + 防重复触发
 *
 *          原理:
 *            正常线宽 ≈ 2~3 路红外命中
 *            5cm 胶布 → 中间 6 路同时命中
 *            (track_bits & 0x7E) == 0x00 表示 6 路全黑
 *
 *          防抖策略:
 *            - 需连续 ≥3 次命中才判定为经过胶布
 *            - MarkerFlag 保证一次经过只计 1 圈
 *            - 完全离开胶布后自动复位 MarkerFlag
 */
#include "lap_detect.h"
#include "line_sensor.h"

LapDetect_t Lap;

/* ================================================================
 * 初始化 / 复位
 * ================================================================ */

void LapDetect_Init(void)
{
    Lap.LapCount   = 0;
    Lap.MarkerFlag = 0;
    Lap.MarkerCnt  = 0;
}

void LapDetect_Reset(void)
{
    Lap.LapCount   = 0;
    Lap.MarkerFlag = 0;
    Lap.MarkerCnt  = 0;
}

/* ================================================================
 * 周期检测 (每 10ms)
 * ================================================================ */

void LapDetect_Task(void)
{
    uint8_t ir = LineSensor_GetAllChannels();

    /* 中间 6 路全黑: (track_bits & 0x7E) == 0x00  (0=黑) */
    if ((ir & MARKER_MASK) == 0x00)
    {
        if (Lap.MarkerCnt < 20) {
            Lap.MarkerCnt++;
        }
    }
    else
    {
        /* 离开胶布 — 之前连续检测到 ≥3 次则计一圈 */
        if (Lap.MarkerCnt >= 3)
        {
            if (Lap.MarkerFlag == 0)
            {
                Lap.LapCount++;
                Lap.MarkerFlag = 1;
            }
        }
        Lap.MarkerCnt = 0;
    }

    /* 完全离开胶布后复位 flag, 准备下一次检测 */
    if ((ir & MARKER_MASK) != 0x00)
    {
        if (Lap.MarkerCnt == 0)
        {
            Lap.MarkerFlag = 0;
        }
    }
}

/* ================================================================
 * 查询接口
 * ================================================================ */

uint8_t LapDetect_GetCount(void)
{
    return Lap.LapCount;
}
