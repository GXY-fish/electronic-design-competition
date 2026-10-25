/**
 * @file    vehicle_track.h
 * @brief   TRACK 状态 — 正常巡线
 */

#ifndef __VEHICLE_TRACK_H
#define __VEHICLE_TRACK_H

void State_Track(void);     /* 状态判断 (丢线检测) */
void Ctrl_Track(void);      /* 模糊 PD 控制计算 */
void Ctrl_Track_Init(void); /* 初始化模糊 PD */

#endif /* __VEHICLE_TRACK_H__ */
