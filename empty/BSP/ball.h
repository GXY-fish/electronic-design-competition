#ifndef BALL_H
#define BALL_H

#include "pid.h"
#include <stdint.h>

/**
 * @brief 滚球 PD 控制模块
 *
 * 接收 K230 的球位置/速度, 通过 PD 控制器计算舵机角度,
 * 使小球稳定在目标位置 (Ball-and-Beam 一维平衡控制).
 *
 * 坐标系: 中心 O=0mm, 右侧为正, 左侧为负
 * 舵机:   角度越大球越往正向移动 (baseline=10° 时水管水平)
 *
 * 使用方法:
 *   1. Ball_Init()          — 初始化 PD 参数
 *   2. Ball_SetReference()  — 设置目标位置
 *   3. 每收到一帧 K230 数据:
 *      Ball_UpdatePosition() — 更新当前位置/速度
 *      servo = Ball_Compute() — 计算舵机角度
 *      Servo_SetAngle(servo)
 *   4. Ball_IsStable()      — 检查是否稳定在目标位置
 *   5. Ball_LostProtect()   — 丢球时安全回中
 */
typedef struct {
    PD_Controller pd;          // PD 控制器
    float target_mm;           // 目标位置 (mm)
    int   current_mm;          // 当前位置 (mm)
    int   current_v;           // 当前速度 (mm/s, K230 alpha-beta)
    int   servo_angle;         // 当前舵机输出角度
    int   baseline_angle;      // 水管水平时的舵机角度 (10°)
    int   servo_min;           // 舵机安全范围下限
    int   servo_max;           // 舵机安全范围上限
    int   lost_ms;             // 丢球累计时间 (ms)
    int   stable_cnt;          // 连续稳定帧数
    uint8_t ball_valid;        // 当前帧是否有效
    uint8_t pd_enabled;        // PD 是否使能
} BallControl;

/**
 * @brief 初始化滚球控制模块
 * @param ball          控制实例
 * @param kp            比例增益 (建议 1.0~5.0)
 * @param kd            微分增益 (建议 0.1~2.0)
 * @param baseline_angle 水管水平时的舵机角度 (10°)
 */
void Ball_Init(BallControl *ball, float kp, float kd, int baseline_angle);

/**
 * @brief 更新球位置/速度 (每收到一帧 K230 数据调用)
 * @param ball   控制实例
 * @param x_mm   位置 (mm), 中心 O=0
 * @param v_mm_s 速度 (mm/s), K230 alpha-beta 滤波值
 * @param valid  检测是否有效 (ball.flags & 0x01)
 */
void Ball_UpdatePosition(BallControl *ball, int x_mm, int v_mm_s, uint8_t valid);

/**
 * @brief 设置目标位置
 * @param ball      控制实例
 * @param target_mm 目标位置 (mm), 例如 0=原点, -50=-5cm, +50=+5cm
 */
void Ball_SetReference(BallControl *ball, float target_mm);

/**
 * @brief 运行 PD 计算, 返回舵机角度
 * @param ball 控制实例
 * @return 舵机角度 (0~180), 可直接传给 Servo_SetAngle()
 */
int Ball_Compute(BallControl *ball);

/**
 * @brief 检查小球是否稳定在目标位置
 * @param ball            控制实例
 * @param err_thresh_mm   位置误差阈值 (mm), 例如 3
 * @param vel_thresh_mm_s 速度阈值 (mm/s), 例如 5
 * @param dur_frames      需要连续稳定的帧数, 例如 50 (约 1.5s @33fps)
 * @return 1=稳定, 0=未稳定
 */
int Ball_IsStable(BallControl *ball, float err_thresh_mm,
                  float vel_thresh_mm_s, int dur_frames);

/**
 * @brief 丢球保护: 丢球超过 200ms 自动回中并停用 PD
 * @param ball 控制实例
 */
void Ball_LostProtect(BallControl *ball);

#endif /* BALL_H */
