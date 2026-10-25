/**
 * @file    vehicle.h
 * @brief   小车状态机 + 控制器 — 顶层接口
 *          架构: 状态机决定目标速度 → 控制器计算 → motor_pid → PWM
 */

#ifndef __VEHICLE_H
#define __VEHICLE_H

#include <stdint.h>
#include "vehicle_param.h"

/* 状态枚举 */
typedef enum
{
    VEH_INIT = 0,

    VEH_TRACK,          /* 正常巡线 */

    VEH_LOST_HOLD,      /* 短暂丢线保持 */

    VEH_SEARCH,         /* 搜索找回线 */

    VEH_RECOVER,        /* 找回后稳定 */

    VEH_FAULT           /* 超时故障 */

} VehicleState_t;

/* 车辆全局对象 */
typedef struct
{
    VehicleState_t state;

    uint32_t state_tick;       /* 状态持续时间 (ms), 每 10ms +10 */

    float   left_target;       /* 左侧目标速度 (RPM) */
    float   right_target;      /* 右侧目标速度 (RPM) */

    int8_t  last_side;         /* 丢线前最后位置: +1=偏右, -1=偏左 */

} Vehicle_t;

extern Vehicle_t g_vehicle;

/* 顶层 API */
void Vehicle_Init(void);
void Vehicle_UpdateState(void);   /* 状态机, 只切状态 */
void Vehicle_Control(void);       /* 控制器, 根据状态计算目标速度 */
void Vehicle_ApplyTarget(void);   /* 将目标速度发给 motor_pid */

/* 状态切换 (供 vehicle_track / vehicle_search 等模块调用) */
void Vehicle_ChangeState(VehicleState_t next);

#endif /* __VEHICLE_H__ */
