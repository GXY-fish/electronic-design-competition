/**
 * @file    app_state.h
 * @brief   应用层状态机 — 矩阵键盘驱动的模式切换框架
 *          巡线核心逻辑保留在 main.c 不动, 状态机只做薄封装
 */

#ifndef __APP_STATE_H
#define __APP_STATE_H

#include <stdint.h>

/* ================================================================
 * 状态枚举
 * ================================================================ */

typedef enum {
    STATE_IDLE = 0,

    STATE_T2_CAR_LAP_STOP,      /* KEY1: 循迹一圈停车 */
    STATE_T3_EMERGENCY_STOP,    /* KEY2: 紧急停车 (锁死) */
    STATE_T5_SLOW_TRACK,        /* KEY3: 慢速循迹 */
    STATE_T6_SLOW_TEST,         /* KEY4: 慢速测试 */

    STATE_COUNT
} State_t;

/* ================================================================
 * 全局状态
 * ================================================================ */

extern State_t Current_State;
extern State_t Last_State;

/* ================================================================
 * API
 * ================================================================ */

void StateMachine_Init(void);
void StateMachine_Run(void);    /* 每 10ms 调用, ISR 上下文 */
void State_Enter(State_t s);    /* 进入状态时执行一次 */
void Key_Task(void);            /* 主循环调用, 按键 → 状态切换 */

void Motor_Stop(void);
void Track_Reset(void);

#endif /* __APP_STATE_H */
