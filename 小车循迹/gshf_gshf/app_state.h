/**
 * @file    app_state.h
 * @brief   应用层状态机 — 主循环运行, ISR 巡线逻辑不碰
 */

#ifndef __APP_STATE_H
#define __APP_STATE_H

#include <stdint.h>

typedef enum {
    STATE_IDLE = 0,
    STATE_T2_CAR_LAP_STOP,      /* KEY1: 循迹一圈停车 */
    STATE_T3_EMERGENCY_STOP,    /* KEY2: 紧急停车 (锁死) */
    STATE_T5_SLOW_TRACK,        /* KEY3: 慢速循迹 */
    STATE_T6_SLOW_TEST,         /* KEY4: 慢速测试 */
    STATE_T7_SLOW_TRACK,        /* KEY5: 慢速循迹 (同T5/T6) */
    STATE_COUNT
} State_t;

extern volatile State_t Current_State;
extern volatile uint32_t g_lap_time_ms;
extern volatile uint32_t g_lap_start;

void StateMachine_Init(void);
void StateMachine_Run(void);    /* 主循环调用 */
void Key_Task(void);            /* 主循环调用, 按键 → 状态切换 */

#endif /* __APP_STATE_H */
