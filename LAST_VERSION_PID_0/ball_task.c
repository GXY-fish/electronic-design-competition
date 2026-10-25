#include "ball_task.h"

#include "ball_config.h"

#include <math.h>
#include <stddef.h>

static void clear_condition_timer(BallTask *task)
{
    task->condition_active = false;
    task->condition_start_ms = 0U;
}

static bool condition_held(BallTask *task,
                           bool condition,
                           uint32_t now_ms,
                           uint32_t required_ms)
{
    if (!condition) {
        clear_condition_timer(task);
        return false;
    }

    if (!task->condition_active) {
        task->condition_active = true;
        task->condition_start_ms = now_ms;
        return required_ms == 0U;
    }

    return (uint32_t)(now_ms - task->condition_start_ms) >= required_ms;
}

static void enter_fault(BallTask *task, uint16_t fault)
{
    task->fault_flags |= fault;
    task->state = BALL_TASK_FAULT;
    task->target_mm = 0.0f;
    clear_condition_timer(task);
}

void BallTask_Init(BallTask *task, float task_position_sign)
{
    if (task == NULL) {
        return;
    }

    task->task_position_sign =
        (task_position_sign < 0.0f) ? -1.0f : 1.0f;
    BallTask_Reset(task);
}

void BallTask_Reset(BallTask *task)
{
    float sign;

    if (task == NULL) {
        return;
    }

    sign = (task->task_position_sign < 0.0f) ? -1.0f : 1.0f;
    task->state = BALL_TASK_IDLE;
    task->task_position_sign = sign;
    task->target_mm = 0.0f;
    task->start_ms = 0U;
    task->frozen_elapsed_ms = 0U;
    task->condition_start_ms = 0U;
    task->fault_flags = BALL_FAULT_NONE;
    task->condition_active = false;
}

void BallTask_Start(BallTask *task, uint32_t now_ms)
{
    if ((task == NULL) || (task->state != BALL_TASK_IDLE)) {
        return;
    }

    task->start_ms = now_ms;
    task->frozen_elapsed_ms = 0U;
    task->fault_flags = BALL_FAULT_NONE;
    task->target_mm =
        task->task_position_sign * BALL_TARGET_PLUS_MM;
    task->state = BALL_TASK_GO_PLUS_5;
    clear_condition_timer(task);
}

void BallTask_Update(BallTask *task,
                     uint32_t now_ms,
                     float x_mm,
                     float v_mm_s,
                     bool vision_ok)
{
    float error_mm;

    if ((task == NULL) || (task->state == BALL_TASK_IDLE) ||
        (task->state == BALL_TASK_FAULT)) {
        return;
    }

    if (!vision_ok) {
        enter_fault(task, BALL_FAULT_VISION);
        return;
    }
    if (fabsf(x_mm) > BALL_DANGER_POSITION_MM) {
        enter_fault(task, BALL_FAULT_POSITION);
        return;
    }
    if (task->state == BALL_TASK_FINISHED) {
        return;
    }
    if ((uint32_t)(now_ms - task->start_ms) >= BALL_TASK_TIMEOUT_MS) {
        enter_fault(task, BALL_FAULT_TIMEOUT);
        return;
    }

    error_mm = x_mm - task->target_mm;

    if (task->state == BALL_TASK_GO_PLUS_5) {
        const bool arrived =
            (fabsf(error_mm) <= BALL_PLUS_POSITION_TOL_MM) &&
            (fabsf(v_mm_s) <= BALL_PLUS_SPEED_TOL_MM_S);
        if (condition_held(task, arrived, now_ms, BALL_PLUS_HOLD_MS)) {
            task->target_mm =
                task->task_position_sign * BALL_TARGET_MINUS_MM;
            task->state = BALL_TASK_GO_MINUS_5;
            clear_condition_timer(task);
        }
        return;
    }

    if (task->state == BALL_TASK_GO_MINUS_5) {
        const bool stable =
            (fabsf(error_mm) <= BALL_MINUS_POSITION_TOL_MM) &&
            (fabsf(v_mm_s) <= BALL_MINUS_SPEED_TOL_MM_S);
        if (condition_held(task, stable, now_ms, BALL_MINUS_HOLD_MS)) {
            task->frozen_elapsed_ms =
                (uint32_t)(now_ms - task->start_ms);
            task->state = BALL_TASK_FINISHED;
            clear_condition_timer(task);
        }
    }
}

BallTaskState BallTask_GetState(const BallTask *task)
{
    return (task != NULL) ? task->state : BALL_TASK_FAULT;
}

float BallTask_GetTargetMm(const BallTask *task)
{
    return (task != NULL) ? task->target_mm : 0.0f;
}

uint32_t BallTask_GetElapsedMs(const BallTask *task, uint32_t now_ms)
{
    if (task == NULL) {
        return 0U;
    }
    if ((task->state == BALL_TASK_FINISHED) ||
        (task->frozen_elapsed_ms > 0U)) {
        return task->frozen_elapsed_ms;
    }
    if (task->state == BALL_TASK_IDLE) {
        return 0U;
    }
    return (uint32_t)(now_ms - task->start_ms);
}

uint16_t BallTask_GetFaultFlags(const BallTask *task)
{
    return (task != NULL) ? task->fault_flags : BALL_FAULT_VISION;
}
