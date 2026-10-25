/**
 * @file    PID.h
 * @brief   通用位置式 PID 控制器 —— 函数调用式接口
 *
 * 用法(三步):
 *   PID_t pid;
 *   PID_Init(&pid, kp, ki, kd, target, outMin, outMax);   // ① 建立控制器
 *   pid.Actual = 反馈值;  out = PID_Compute(&pid);          // ② 每个周期算一次
 *   PID_Reset(&pid);                                        // ③ 需要时清内部状态
 */
#ifndef __PID_H
#define __PID_H

typedef struct {
    /* ---- 外部设定(用户读写) ---- */
    float Target;       // 目标值
    float Actual;       // 实际反馈值(每周期喂入)
    float Kp, Ki, Kd;   // 比例/积分/微分增益
    float OutMax;       // 输出上限
    float OutMin;       // 输出下限

    /* ---- 输出(用户只读) ---- */
    float Out;          // 本周期计算结果(已限幅)

    /* ---- 内部状态(勿手改, 用 PID_Reset 清零) ---- */
    float prevErr;      // 上次误差(算微分项)
    float integral;     // 误差积分(算积分项)
} PID_t;

/* 初始化: 设定增益/目标/限幅, 并清零内部状态 */
void  PID_Init(PID_t *pid, float kp, float ki, float kd,
               float target, float outMin, float outMax);

/* 单步计算: 读 pid->Actual, 写并返回 pid->Out */
float PID_Compute(PID_t *pid);

/* 复位: 清空积分与上次误差(切控制状态前调用, 防止旧状态污染) */
void  PID_Reset(PID_t *pid);

#endif
