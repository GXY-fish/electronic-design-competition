/**
 * @file    vehicle_search.c
 * @brief   SEARCH 状态 — 丢线后慢转搜索
 */

#include "vehicle_search.h"
#include "vehicle.h"
#include "line_sensor.h"

/* ================================================================
 * 搜索状态判断
 * ================================================================ */

void State_Search(void)
{
    if (g_line.valid)
    {
        Vehicle_ChangeState(VEH_RECOVER);
        return;
    }

    if (g_vehicle.state_tick > SEARCH_TIMEOUT_MS)
    {
        Vehicle_ChangeState(VEH_FAULT);
    }
}

/* ================================================================
 * 搜索控制: 朝丢线方向慢转
 *   右边丢线(last_side>0) → 向右慢转
 *   左边丢线(last_side<0) → 向左慢转
 * ================================================================ */

void Ctrl_Search(void)
{
    if (g_vehicle.last_side > 0)
    {
        /* 线偏右, 向右转找线 */
        g_vehicle.left_target  = SEARCH_RPM;
        g_vehicle.right_target = 0;
    }
    else
    {
        /* 线偏左, 向左转找线 */
        g_vehicle.left_target  = 0;
        g_vehicle.right_target = SEARCH_RPM;
    }
}
