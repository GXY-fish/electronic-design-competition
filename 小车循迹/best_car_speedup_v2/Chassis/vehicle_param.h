/**
 * @file    vehicle_param.h
 * @brief   全部参数集中管理 — 调车只改这里
 *
 *   RPM 和 PWM 一一对应: target_rpm=350 → 前馈 PWM≈350
 *   五步因果链:
 *   1. e_line = Σ(命中权重) / 命中数           (line_sensor)
 *   2. turn  = Kp×e + Kd×de                     (PD, 无积分)
 *   3. base  = max - slow_gain×|e|               (弯道降速)
 *   4. left  = base + turn, right = base - turn  (差速)
 *   5. PWM   = target + PI(target, measure)      (前馈1:1 + PI修正)
 */

#ifndef __VEHICLE_PARAM_H
#define __VEHICLE_PARAM_H

//----------------------------------
// Step 2: 线误差 → 转向差速 (PD, 不要 I)
//   对标 wheel_4 pid_Turn Kp=400
//   我们的 e_line 范围是 2x, 所以 Kp 可以小一半
//----------------------------------

#define LINE_KP           200.0f    /* P 增益: e_line→自动回中 */
#define LINE_KD             5.0f    /* D 增益: 抑制振荡 */

#define MAX_TURN_RPM      550.0f    /* 转向差速上限 */

//----------------------------------
// Step 3: 弯道自动降速
//----------------------------------

#define TRACK_MAX_RPM     700.0f    /* 直道最高速 */
#define TRACK_MIN_RPM     120.0f    /* 弯道最低速 */

#define CURVE_SLOW_GAIN    50.0f    /* 降速系数 */

//----------------------------------
// Step 4: 差速分配在 Ctrl_Track 中完成
//----------------------------------

//----------------------------------
// Step 5: 电机前馈 1:1 + PI 修正
//   RPM 直接映射到 PWM (前馈=1:1), PI 只修剩余误差
//----------------------------------

#define MOTOR_FF_GAIN       1.0f    /* RPM→PWM 1:1 */

/* PI 增益 (先关掉, 纯前馈避免跟转向打架) */
#define MOTOR_KP            0.0f
#define MOTOR_KI            0.0f
#define MOTOR_KD            0.0f

//----------------------------------
// 状态机参数
//----------------------------------

#define LOST_HOLD_MS        60
#define SEARCH_TIMEOUT_MS  2500
#define RECOVER_TIME_MS    150
#define SEARCH_RPM          80

#endif /* __VEHICLE_PARAM_H__ */
