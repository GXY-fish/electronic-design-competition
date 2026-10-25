#ifndef BALL_CONFIG_H
#define BALL_CONFIG_H

/* ═══════════════════════════════════════════════════════════════════
 *  PD+I 闭环控制参数 (ωn=2.27 rad/s, ζ=0.74)
 *
 *  物理关系: 舵机倾斜 θ° → 重力分量 g·sin(θ) ≈ 171·θ mm/s²
 *  Kp = ωn² / 171,  Kd = 2ζωn / 171
 * ═══════════════════════════════════════════════════════════════════ */

#define BALL_CONTROL_PERIOD_S              0.020f

/* ── Alpha-Beta 滤波器 ── */
#define BALL_FILTER_ALPHA                  0.65f
#define BALL_FILTER_BETA                   0.15f

/* ── PD+I 增益 ── */
#define BALL_KP_GO_PLUS_DEG_PER_MM         0.030f
#define BALL_KP_GO_MINUS_DEG_PER_MM        0.030f

#define BALL_KP_DEG_PER_MM BALL_KP_GO_PLUS_DEG_PER_MM

#define BALL_KD_GO_PLUS_DEG_PER_MM_S       0.025f
#define BALL_KD_GO_MINUS_DEG_PER_MM_S      0.025f

#define BALL_KI_DEG_PER_MM_S               0.0f    /* 暂不启用 I 项 */

/* ── PID 输出限幅 (角度) ── */
#define BALL_THETA_LIMIT_DEG               3.0f
#define BALL_THETA_STEP_PER_20MS_DEG       1.0f

/* ── 积分限幅 (Ki=0 时无实际作用, 保留框架) ── */
#define BALL_INTEGRAL_LIMIT_DEG            0.3f
#define BALL_INTEGRAL_WINDOW_MM            12.0f
#define BALL_INTEGRAL_SPEED_WINDOW_MM_S    30.0f

/* ── 速度估计限幅 ── */
#define BALL_SPEED_LIMIT_MM_S              1500.0f

#define BALL_KD_DEG_PER_MM_S  BALL_KD_GO_PLUS_DEG_PER_MM_S

/* ── 原点等待 (球在 ±20mm 内稳定 500ms 后自动开始) ── */
#define BALL_ORIGIN_WAIT_MS                500U
#define BALL_ORIGIN_TOL_MM                 20.0f

/*
 * ═══════════════════════════════════════════════════════════════════
 *  舵机 5 点标定 (上车前必须用水平仪重新测量!)
 *
 *  TIMG7: 100kHz计数, 20ms周期 (count=2000)
 *  PWM增大 → 舵机端降低 → 球向正方向滚
 *  PWM减小 → 舵机端升高 → 球向负方向滚
 * ═══════════════════════════════════════════════════════════════════
 */
#define BALL_SERVO_NEG_4P5_PULSE_US 2410U
#define BALL_SERVO_NEG_2_PULSE_US   2370U
#define BALL_SERVO_LEVEL_PULSE_US   2375U
#define BALL_SERVO_POS_2_PULSE_US   2290U
#define BALL_SERVO_POS_4P5_PULSE_US 2250U

/* ── 调试串口 (UART1 PRINT_INST, PB6/TX) ── */
#define DEBUG_UART                         PRINT_INST

/* ── 板载 LED (PB22, 高电平点亮) ── */
#define BANG_LED_PORT                      GPIOB
#define BANG_LED_PIN                DL_GPIO_PIN_22

/* ── 坐标系方向符号 (1.0 = 正向不变, -1.0 = 翻转) ── */
#define VISION_POSITION_SIGN               1.0f
#define TASK_POSITION_SIGN                 1.0f

/* ── 目标位置 ── */
#define BALL_TARGET_PLUS_MM                50.0f
#define BALL_TARGET_MINUS_MM              -50.0f

/* ── 状态切换判断阈值 ── */
#define BALL_PLUS_POSITION_TOL_MM          15.0f
#define BALL_PLUS_SPEED_TOL_MM_S           1000.0f
#define BALL_PLUS_HOLD_MS                   0U

#define BALL_MINUS_POSITION_TOL_MM          5.0f
#define BALL_MINUS_SPEED_TOL_MM_S          15.0f
#define BALL_MINUS_HOLD_MS                 400U

/* ── 故障检测 ── */
#define BALL_VISION_TIMEOUT_MS             100U
#define BALL_DANGER_POSITION_MM            115.0f
#define BALL_TASK_TIMEOUT_MS              15000U

/* ── K230 协议参数 ── */
#define VISION_CONFIDENCE_MIN               35U
#define VISION_FLAG_VALID                 0x01U
#define VISION_FRAME_SIZE                   15U

#endif
