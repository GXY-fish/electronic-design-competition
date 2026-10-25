#ifndef PID_H
#define PID_H

/**
 * @brief PD 控制器 (位置式, 速度来自 K230 alpha-beta 滤波器)
 *
 * 公式: output = kp * error - kd * velocity
 *   - kp: 比例增益, 误差越大输出越大
 *   - kd: 微分增益, 速度越快阻尼越大 (负号 = 抵抗运动方向)
 *   - 输出自动钳位到 [out_min, out_max]
 */
typedef struct {
    float kp;        // Proportional gain
    float kd;        // Derivative gain (damps via K230 velocity)
    float out_min;   // Output lower clamp
    float out_max;   // Output upper clamp
    float output;    // Last computed output
} PD_Controller;

/**
 * @brief 初始化 PD 控制器
 * @param pd   PD 控制器实例
 * @param kp   比例增益
 * @param kd   微分增益
 * @param out_min 输出下限
 * @param out_max 输出上限
 */
void PD_Init(PD_Controller *pd, float kp, float kd, float out_min, float out_max);

/**
 * @brief 计算 PD 输出
 * @param pd       PD 控制器实例
 * @param error    位置误差 (target - current), 单位 mm
 * @param velocity 当前速度 (K230 alpha-beta 滤波), 单位 mm/s
 * @return 钳位后的 PD 输出
 */
float PD_Compute(PD_Controller *pd, float error, float velocity);

/**
 * @brief 重置 PD 控制器内部状态
 */
void PD_Reset(PD_Controller *pd);

#endif /* PID_H */
