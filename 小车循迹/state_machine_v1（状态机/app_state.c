/**
 * @file    app_state.c
 * @brief   状态机 — 薄封装, 只管理状态切换和速度设定
 *          巡线核心逻辑不动, 留在 main.c 的 App_Task10ms() 里
 */

#include "app_state.h"
#include "main.h"
#include "hardware/motor_ctrl.h"
#include "Chassis/vehicle.h"
#include "Chassis/line_sensor.h"
#include "Chassis/motor_pid.h"
#include "Chassis/lap_detect.h"
#include "hardware/keypad.h"

/* ================================================================
 * 全局状态变量
 * ================================================================ */

State_t Current_State = STATE_IDLE;
State_t Last_State    = STATE_IDLE;

/* ================================================================
 * 辅助
 * ================================================================ */

void Motor_Stop(void)
{
    MOTORS_DISABLE();
}

void Track_Reset(void)
{
    g_line.derivative = 0.0f;
    g_line.error      = 0.0f;
    g_line.valid      = 0;
    Motor_PID_Init();
}

/* ================================================================
 * State_Enter — 进入状态时执行一次 (在 ISR 里被 StateMachine_Run 调用)
 * ================================================================ */

void State_Enter(State_t state)
{
    switch (state)
    {
    case STATE_IDLE:
        Motor_Stop();
        break;

    case STATE_T2_CAR_LAP_STOP:
        Track_Reset();
        LapDetect_Reset();
        Basic_Speed = 75.0f;
        MOTORS_ENABLE();
        break;

    case STATE_T3_EMERGENCY_STOP:
        Motor_Stop();
        break;

    case STATE_T5_SLOW_TRACK:
        Track_Reset();
        Basic_Speed = 45.0f;
        MOTORS_ENABLE();
        break;

    case STATE_T6_SLOW_TEST:
        Track_Reset();
        Basic_Speed = 25.0f;
        MOTORS_ENABLE();
        break;

    default:
        Current_State = STATE_IDLE;
        break;
    }
}

/* ================================================================
 * StateMachine_Init
 * ================================================================ */

void StateMachine_Init(void)
{
    Current_State = STATE_IDLE;
    Last_State    = STATE_IDLE;
    Motor_Stop();
}

/* ================================================================
 * StateMachine_Run — 每 10ms 被 ISR 调用
 *   只做两件事: ① 状态变化时调 State_Enter  ② 特定状态的循环逻辑
 *   巡线流水线在 main.c 里不变
 * ================================================================ */

void StateMachine_Run(void)
{
    /* 状态变化 → 执行进入动作 */
    if (Current_State != Last_State) {
        State_Enter(Current_State);
        Last_State = Current_State;
    }

    /* 状态循环逻辑 (巡线之外的特定处理) */
    switch (Current_State)
    {
    case STATE_IDLE:
    case STATE_T3_EMERGENCY_STOP:
        Motor_Stop();
        break;

    case STATE_T2_CAR_LAP_STOP:
        /* 一圈停车检测 */
        if (LapDetect_GetCount() >= 1) {
            Motor_Stop();
            Track_Reset();
            Current_State = STATE_IDLE;
        }
        break;

    case STATE_T5_SLOW_TRACK:
    case STATE_T6_SLOW_TEST:
        /* 巡线由 main.c 的通用流水线处理 */
        break;

    default:
        Current_State = STATE_IDLE;
        break;
    }
}

/* ================================================================
 * Key_Task — 主循环调用, 按键 → 状态切换 (仅上升沿)
 * ================================================================ */

void Key_Task(void)
{
    static uint8_t prev_key = 0;
    uint8_t key = Keypad_GetKey();

    if (key != prev_key) {
        prev_key = key;

        if (key != 0) {
            /* 紧急停车状态下禁止按键切换 (锁死) */
            if (Current_State == STATE_T3_EMERGENCY_STOP)
                return;

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
