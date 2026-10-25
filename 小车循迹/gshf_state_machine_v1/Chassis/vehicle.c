/**
 * @file    vehicle.c
 * @brief   小车状态机 + 控制器 — 完整实现
 *          架构: 状态机只切状态 | 控制器只算速度 | motor_pid 执行
 *
 *          状态转换图:
 *          INIT → TRACK ←→ LOST_HOLD → SEARCH → RECOVER → TRACK
 *                                            ↘ FAULT (超时)
 */

#include "vehicle.h"
#include "vehicle_track.h"
#include "vehicle_search.h"
#include "line_sensor.h"
#include "motor_pid.h"
#include <string.h>

/* ================================================================
 * 全局对象
 * ================================================================ */

Vehicle_t g_vehicle;

/* ================================================================
 * 状态切换 (统一入口, 重置 tick)
 * ================================================================ */

void Vehicle_ChangeState(VehicleState_t next)
{
    g_vehicle.state     = next;
    g_vehicle.state_tick = 0;
}

/* ================================================================
 * 初始化
 * ================================================================ */

void Vehicle_Init(void)
{
    memset(&g_vehicle, 0, sizeof(g_vehicle));
    g_vehicle.state = VEH_INIT;
}

/* ================================================================
 * 内部状态函数声明
 * ================================================================ */

static void State_Init(void);
static void State_LostHold(void);
static void State_Recover(void);
static void State_Fault(void);

static void Ctrl_LostHold(void);
static void Ctrl_Recover(void);
static void Ctrl_Stop(void);

/* ================================================================
 * 状态机 — Vehicle_UpdateState()
 *   只负责切状态, 不做控制
 *   每 10ms 调用一次, state_tick += 10
 * ================================================================ */

void Vehicle_UpdateState(void)
{
    g_vehicle.state_tick += 10;

    switch (g_vehicle.state)
    {
    case VEH_INIT:
        State_Init();
        break;

    case VEH_TRACK:
        State_Track();
        break;

    case VEH_LOST_HOLD:
        State_LostHold();
        break;

    case VEH_SEARCH:
        State_Search();
        break;

    case VEH_RECOVER:
        State_Recover();
        break;

    case VEH_FAULT:
        State_Fault();
        break;
    }
}

/* ================================================================
 * 控制器 — Vehicle_Control()
 *   根据当前状态计算左右轮目标速度
 * ================================================================ */

void Vehicle_Control(void)
{
    switch (g_vehicle.state)
    {
    case VEH_TRACK:
        Ctrl_Track();
        break;

    case VEH_LOST_HOLD:
        Ctrl_LostHold();
        break;

    case VEH_SEARCH:
        Ctrl_Search();
        break;

    case VEH_RECOVER:
        Ctrl_Recover();
        break;

    default:
        Ctrl_Stop();
        break;
    }
}

/* ================================================================
 * 输出目标速度给 PID
 * ================================================================ */

void Vehicle_ApplyTarget(void)
{
    Motor_SetTargetRPM(MOTOR_LF, g_vehicle.left_target);
    Motor_SetTargetRPM(MOTOR_LR, g_vehicle.left_target);
    Motor_SetTargetRPM(MOTOR_RF, g_vehicle.right_target);
    Motor_SetTargetRPM(MOTOR_RR, g_vehicle.right_target);
}

/* ================================================================
 * State_Init — 上电初始化状态
 *   等待传感器稳定后进入 TRACK
 * ================================================================ */

static void State_Init(void)
{
    /* 等 100ms 让传感器稳定, 然后直接进入巡线 */
    if (g_vehicle.state_tick >= 100)
    {
        Vehicle_ChangeState(VEH_TRACK);
    }
}

/* ================================================================
 * State_LostHold — 刚丢线先保持, 可能是瞬时干扰
 *   超过 LOST_HOLD_MS 仍未找回 → 进入 SEARCH
 * ================================================================ */

static void State_LostHold(void)
{
    if (g_line.valid)
    {
        Vehicle_ChangeState(VEH_TRACK);
        return;
    }

    if (g_vehicle.state_tick > LOST_HOLD_MS)
    {
        Vehicle_ChangeState(VEH_SEARCH);
    }
}

/* ================================================================
 * State_Recover — 重新找到线, 先低速稳定再回 TRACK
 * ================================================================ */

static void State_Recover(void)
{
    if (g_vehicle.state_tick > RECOVER_TIME_MS)
    {
        Vehicle_ChangeState(VEH_TRACK);
    }
}

/* ================================================================
 * State_Fault — 超时故障, 停止并等待手动复位
 * ================================================================ */

static void State_Fault(void)
{
    Ctrl_Stop();
}

/* ================================================================
 * Ctrl_LostHold — 短暂保持, 维持最后方向
 *   如果已知丢线前偏右(last_side>0), 保持右转趋势, 反之亦然
 *   速度降到 TRACK_MIN_RPM 避免冲出去
 * ================================================================ */

static void Ctrl_LostHold(void)
{
    if (g_vehicle.last_side > 0)
    {
        g_vehicle.left_target  = TRACK_MIN_RPM + 20;
        g_vehicle.right_target = TRACK_MIN_RPM - 20;
    }
    else
    {
        g_vehicle.left_target  = TRACK_MIN_RPM - 20;
        g_vehicle.right_target = TRACK_MIN_RPM + 20;
    }
}

/* ================================================================
 * Ctrl_Recover — 找回后低速直行稳定
 * ================================================================ */

static void Ctrl_Recover(void)
{
    g_vehicle.left_target  = 200;   /* x2.5 */
    g_vehicle.right_target = 200;
}

/* ================================================================
 * Ctrl_Stop — 全部停止
 * ================================================================ */

static void Ctrl_Stop(void)
{
    g_vehicle.left_target  = 0;
    g_vehicle.right_target = 0;
}
