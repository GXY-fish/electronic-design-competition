#ifndef BALL_TASK_H
#define BALL_TASK_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    BALL_TASK_IDLE = 0,
    BALL_TASK_GO_PLUS_5,
    BALL_TASK_GO_MINUS_5,
    BALL_TASK_FINISHED,
    BALL_TASK_FAULT
} BallTaskState;

enum {
    BALL_FAULT_NONE = 0U,
    BALL_FAULT_VISION = 1U << 0,
    BALL_FAULT_POSITION = 1U << 1,
    BALL_FAULT_TIMEOUT = 1U << 2
};

typedef struct {
    BallTaskState state;
    float task_position_sign;
    float target_mm;
    uint32_t start_ms;
    uint32_t frozen_elapsed_ms;
    uint32_t condition_start_ms;
    uint16_t fault_flags;
    bool condition_active;
} BallTask;

void BallTask_Init(BallTask *task, float task_position_sign);
void BallTask_Reset(BallTask *task);
void BallTask_Start(BallTask *task, uint32_t now_ms);
void BallTask_Update(BallTask *task,
                     uint32_t now_ms,
                     float x_mm,
                     float v_mm_s,
                     bool vision_ok);
BallTaskState BallTask_GetState(const BallTask *task);
float BallTask_GetTargetMm(const BallTask *task);
uint32_t BallTask_GetElapsedMs(const BallTask *task, uint32_t now_ms);
uint16_t BallTask_GetFaultFlags(const BallTask *task);

#endif
