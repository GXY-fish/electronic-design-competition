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

State_t Current_State = STATE_IDLE;
State_t Last_State    = STATE_IDLE;

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
            break;
        case STATE_T2_CAR_LAP_STOP:
            LapDetect_Reset();
            Basic_Speed = 95.0f;
            MOTORS_ENABLE();
            break;
        case STATE_T3_EMERGENCY_STOP:
            Motor_Stop();
            break;
        case STATE_T5_SLOW_TRACK:
            Basic_Speed = 50.0f;
            MOTORS_ENABLE();
            break;
        case STATE_T6_SLOW_TEST:
            Basic_Speed = 50.0f;
            MOTORS_ENABLE();
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

    /* T2: 一圈停车 */
    if (Current_State == STATE_T2_CAR_LAP_STOP) {
        if (LapDetect_GetCount() >= 2) {
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
        if (key != 0 && Current_State != STATE_T3_EMERGENCY_STOP) {
            switch (key) {
            case 1: Current_State = STATE_T2_CAR_LAP_STOP;   break;
            case 2: Current_State = STATE_T3_EMERGENCY_STOP; break;
            case 3: Current_State = STATE_T5_SLOW_TRACK;     break;
            case 4: Current_State = STATE_T6_SLOW_TEST;      break;
            default: break;
            }
        }
    }
}
