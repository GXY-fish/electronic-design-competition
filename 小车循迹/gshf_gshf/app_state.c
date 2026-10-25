/**
 * @file    app_state.c
 * @brief   状态机 — 只在主循环运行, 不碰 ISR 巡线逻辑
 *          只做: 按键→状态 / 电机开关 / T2 圈数检测
 */

#include "app_state.h"
#include "main.h"
#include "hardware/motor_ctrl.h"
#include "Chassis/lap_detect.h"
#include "hardware/keypad.h"
#include "hardware/OLED/oled.h"
#include "Chassis/vehicle.h"

volatile State_t Current_State = STATE_IDLE;
State_t Last_State    = STATE_IDLE;
volatile uint32_t g_lap_time_ms = 0;  /* 圈速, OLED 显示用 */
volatile uint32_t g_lap_start    = 0;  /* 计时起点, 主循环停车用 */

void Motor_Stop(void) { MOTORS_DISABLE(); }

void StateMachine_Init(void)
{
    Current_State = STATE_IDLE;
    Last_State    = STATE_IDLE;
    Motor_Stop();
}

/* ================================================================
 * StateMachine_Run — 主循环调用, 处理状态切换和圈数
 * ================================================================ */

void StateMachine_Run(void)
{
    /* 状态变化 → 进入动作 */
    if (Current_State != Last_State) {
        switch (Current_State) {
        case STATE_IDLE:
            Motor_Stop();
            if (g_lap_time_ms > 0) {
                uint32_t sec = g_lap_time_ms / 1000;
                uint32_t min = sec / 60;
                uint32_t ds = (g_lap_time_ms % 1000) / 100;
                sec %= 60;
                OLED_CLS();
                OLED_ShowString(1, 1, "LAP TIME", 2);
                OLED_ShowNum(2, 1, min, 2, 2);
                OLED_ShowString(2, 3, ":", 2);
                OLED_ShowNum(2, 4, sec, 2, 2);
                OLED_ShowString(2, 6, ".", 2);
                OLED_ShowNum(2, 7, ds, 1, 2);
            } else {
                OLED_CLS();
                OLED_ShowString(1, 1, "WHEEL bige", 2);
                OLED_ShowString(2, 1, "READY", 2);
            }
            break;
        case STATE_T2_CAR_LAP_STOP:
            LapDetect_Reset();
            Basic_Speed = 95.0f;
            g_lap_start = g_msTick;
            Vehicle_ChangeState(VEH_TRACK);  /* 先开电机, OLED I2C 可能卡死 */
            MOTORS_ENABLE();
            OLED_CLS();
            OLED_ShowString(1, 1, "T2 RUN", 2);
            break;
        case STATE_T3_EMERGENCY_STOP:
            Motor_Stop();
            break;
        case STATE_T5_SLOW_TRACK:
            LapDetect_Reset();
            Basic_Speed = 50.0f;
            g_lap_start = g_msTick;
            Vehicle_ChangeState(VEH_TRACK);  /* 先开电机, OLED I2C 可能卡死 */
            MOTORS_ENABLE();
            OLED_CLS();
            OLED_ShowString(1, 1, "T5 RUN", 2);
            break;
        case STATE_T6_SLOW_TEST:
            LapDetect_Reset();
            Basic_Speed = 50.0f;
            g_lap_start = g_msTick;
            Vehicle_ChangeState(VEH_TRACK);
            MOTORS_ENABLE();
            OLED_CLS();
            OLED_ShowString(1, 1, "T6 RUN", 2);
            break;
        case STATE_T7_SLOW_TRACK:
            LapDetect_Reset();
            Basic_Speed = 50.0f;
            g_lap_start = g_msTick;
            Vehicle_ChangeState(VEH_TRACK);
            MOTORS_ENABLE();
            OLED_CLS();
            OLED_ShowString(1, 1, "T7 RUN", 2);
            break;
        default:
            Current_State = STATE_IDLE;
            break;
        }
        Last_State = Current_State;
    }

    /* IDLE / T3: 持续关电机 */
    if (Current_State == STATE_IDLE ||
        Current_State == STATE_T3_EMERGENCY_STOP) {
        Motor_Stop();
    }

    /* T2/T5/T6/T7: 运行中实时显示计时 (每200ms刷新) */
    if (Current_State == STATE_T2_CAR_LAP_STOP ||
        Current_State == STATE_T5_SLOW_TRACK ||
        Current_State == STATE_T6_SLOW_TEST ||
        Current_State == STATE_T7_SLOW_TRACK) {
        static uint32_t last_oled = 0;
        if (g_msTick - last_oled >= 200) {
            last_oled = g_msTick;
            uint32_t ms = g_msTick - g_lap_start;
            uint32_t sec = ms / 1000;
            uint32_t min = sec / 60;
            uint32_t ds = (ms % 1000) / 100;
            sec %= 60;
            OLED_ShowNum(2, 1, min, 2, 2);
            OLED_ShowString(2, 3, ":", 2);
            OLED_ShowNum(2, 4, sec, 2, 2);
            OLED_ShowString(2, 6, ".", 2);
            OLED_ShowNum(2, 7, ds, 1, 2);
        }
    }

    /* T2: 两次判定线急刹 */
    if (Current_State == STATE_T2_CAR_LAP_STOP) {
        if (LapDetect_GetCount() >= 2) {
            g_lap_time_ms = g_msTick - g_lap_start;
            Motor_Stop();
            Current_State = STATE_IDLE;
        }
    }

    /* T5: 8s 刹车 */
    if (Current_State == STATE_T5_SLOW_TRACK) {
        if (g_msTick - g_lap_start >= 8000) {
            g_lap_time_ms = g_msTick - g_lap_start;
            Motor_Stop();
            Current_State = STATE_IDLE;
        }
    }

    /* T6/T7: 30s 刹车 */
    if (Current_State == STATE_T6_SLOW_TEST ||
        Current_State == STATE_T7_SLOW_TRACK) {
        if (g_msTick - g_lap_start >= 30000) {
            g_lap_time_ms = g_msTick - g_lap_start;
            Motor_Stop();
            Current_State = STATE_IDLE;
        }
    }

}

/* ================================================================
 * Key_Task — 按键 → 状态切换 (上升沿)
 * ================================================================ */

void Key_Task(void)
{
    static uint8_t prev_key = 0;
    uint8_t key = Keypad_GetKey();

    if (key != prev_key) {
        prev_key = key;
        if (key != 0) {
            switch (key) {
            case 1: Current_State = STATE_T2_CAR_LAP_STOP;   break;
            case 2: Current_State = STATE_T3_EMERGENCY_STOP; break;
            case 3: Current_State = STATE_T5_SLOW_TRACK;     break;
            case 4: Current_State = STATE_T6_SLOW_TEST;      break;
            case 5: Current_State = STATE_T7_SLOW_TRACK;     break;
            default: break;
            }
        }
    }
}
