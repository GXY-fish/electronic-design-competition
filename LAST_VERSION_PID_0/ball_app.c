/*
 * ==================== PD 闭环测试 — 固定目标 -50mm ====================
 *
 * 每 20ms 周期:
 *   1. 从 K230 获取球位置 (VisionProtocol)
 *   2. Alpha-Beta 滤波器估计位置/速度
 *   3. PD: theta = Kp * (x_est - (-50)) + Kd * v_est
 *   4. 线性映射: PWM = 2375 - theta * 30
 *   5. 输出 PWM 驱动舵机
 *
 * LED (PB22):
 *   慢闪 ~1Hz  = 等 K230 数据
 *   常亮       = PD 控制运行中
 *   快闪 ~5Hz  = 视觉丢失 (>100ms)
 *
 * 串口输出 (每 500ms):
 *   "x= -25.3 T=-50.0 err=+24.7 v=+120.3 th=+0.7 PWM=2354us"
 * ============================================================
 */

#include "ball_app.h"

#include "ball_config.h"
#include "platform_port.h"
#include "uart.h"
#include "vision_protocol.h"

#include <stdbool.h>
#include <stdint.h>
#include <math.h>

/* ═══════════════════════════════════════════════════════════════════
 *  Alpha-Beta + PD 状态 (自包含, 不依赖 ball_control.h)
 * ═══════════════════════════════════════════════════════════════════ */

#define TEST_TARGET_MM         (0.0f)    /* 目标: 原点 */

/* ── 三段 KP (deg/mm) ── */
#define TEST_KP_NEAR            0.050f   /* |误差| ≤ 10mm, P@10mm=0.50° */
#define TEST_KP_MID             0.040f   /* 10mm < |误差| ≤ 50mm, P@30mm=1.20° */
#define TEST_KP_FAR             0.060f   /* |误差| > 50mm, P@60mm=3.60° */

/* ── 三段角度限幅 (deg): 近<中<远 ── */
#define TEST_LIMIT_NEAR_DEG     1.0f     /* |误差| ≤ 10mm */
#define TEST_LIMIT_MID_DEG      1.5f     /* 10mm < |误差| ≤ 50mm */
#define TEST_LIMIT_FAR_DEG      3.0f     /* |误差| > 50mm */

/* ── 分界线 ── */
#define TEST_THRESH_NEAR_MM     10.0f
#define TEST_THRESH_FAR_MM      50.0f

#define TEST_KD                0.045f    /* deg·s/mm 阻尼 */
#define TEST_KFF               0.005f    /* 速度前馈 deg·s/mm */

#define TEST_ALPHA             0.70f     /* 位置平滑 (稍增) */
#define TEST_BETA              0.07f     /* 速度估计 (再降, 减少D项噪声) */
#define TEST_SPEED_LIMIT_MM_S  1500.0f   /* 速度限幅 */
#define TEST_PWM_LEVEL         2375      /* 水平 PWM */
#define TEST_PWM_SLOPE         22.0f     /* PWM变化率 us/deg */

/* ── PID I 项 (慢速积分, 只消除稳态误差, 不参与动态) ── */
#define TEST_KI                  0.04f   /* 积分增益 */
#define TEST_INTEGRAL_LIMIT_DEG  1.0f    /* I 项上限, 不超过NEAR限幅 */
#define TEST_INTEGRAL_WINDOW_MM  30.0f   /* |误差| < 30mm 才积分 */

/* ── 滤波器状态 ── */
static float    g_x_est = 0.0f;
static float    g_v_est = 0.0f;
static bool     g_filter_init = false;
static float    g_i_angle_deg = 0.0f;      /* I 项输出角度 (直接存度, 非 mm·s) */

/* ── 视觉数据 ── */
static VisionProtocol g_vision_protocol;

volatile uint32_t g_vision_valid_frame_count = 0U;
volatile float    g_vision_x_mm = 0.0f;
volatile uint8_t  g_vision_confidence = 0U;
volatile uint8_t  g_vision_sequence = 0U;
volatile uint8_t  g_vision_flags = 0U;

/* ── 调试变量 ── */
volatile uint8_t  g_debug_task_state = 0U;
volatile uint16_t g_debug_fault_flags = 0U;
volatile float    g_debug_target_mm = 0.0f;
volatile float    g_debug_error_mm = 0.0f;
volatile float    g_debug_theta_cmd_deg = 0.0f;
volatile float    g_debug_x_est_mm = 0.0f;
volatile float    g_debug_v_est_mm_s = 0.0f;
volatile uint16_t g_debug_servo_pulse_us = 0U;

/* ── 兼容旧代码的空桩 ── */
volatile bool     g_result_ready = false;
volatile float    g_result_plus_max_mm = 0.0f;
volatile float    g_result_minus_min_mm = 0.0f;
volatile float    g_result_final_mm = 0.0f;
volatile float    g_result_plus_error_mm = 0.0f;
volatile float    g_result_minus_error_mm = 0.0f;
volatile float    g_result_final_error_mm = 0.0f;
volatile uint32_t g_result_elapsed_ms = 0U;
volatile float    g_result_elapsed_s = 0.0f;

/* ── LED 状态枚举 ── */
typedef enum {
    LED_WAIT_VISION = 0,  /* 等 K230 数据 */
    LED_PD_ACTIVE,        /* PD 运行 */
    LED_VISION_LOST,      /* 视觉丢失 */
} LedMode;

/* ═══════════════════════════════════════════════════════════════════
 *  辅助函数
 * ═══════════════════════════════════════════════════════════════════ */

static float clampf(float v, float lo, float hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

/* ═══════════════════════════════════════════════════════════════════
 *  BallBalanceApp_Init
 * ═══════════════════════════════════════════════════════════════════ */
void BallBalanceApp_Init(void)
{
    VisionProtocol_Init(&g_vision_protocol);
    g_filter_init = false;
    g_x_est = 0.0f;
    g_v_est = 0.0f;
    g_i_angle_deg = 0.0f;

    Platform_ServoWriteUs(TEST_PWM_LEVEL);

    g_debug_task_state = 0U;
    g_debug_target_mm = TEST_TARGET_MM;
}

/* ═══════════════════════════════════════════════════════════════════
 *  BallBalanceApp_OnUartRxByte
 * ═══════════════════════════════════════════════════════════════════ */
void BallBalanceApp_OnUartRxByte(uint8_t byte)
{
    VisionMeasurement m;
    uint32_t now = Platform_GetMillis();

    if (VisionProtocol_PushByte(&g_vision_protocol, byte, now)) {
        if (VisionProtocol_GetLatest(&g_vision_protocol, &m)) {
            g_vision_valid_frame_count++;
            g_vision_x_mm    = m.x_mm;
            g_vision_confidence = m.confidence;
            g_vision_sequence   = m.sequence;
            g_vision_flags      = m.flags;
        }
    }
}

/* ═══════════════════════════════════════════════════════════════════
 *  BallBalanceApp_Update20ms — 每 20ms 被 main 调用
 * ═══════════════════════════════════════════════════════════════════ */
void BallBalanceApp_Update20ms(void)
{
    VisionMeasurement m;
    uint32_t now = Platform_GetMillis();
    bool has = VisionProtocol_GetLatest(&g_vision_protocol, &m);
    bool vision_ok = has && VisionMeasurement_IsUsable(&m, now);

    float theta = 0.0f;
    uint16_t pulse = TEST_PWM_LEVEL;
    LedMode led_mode = LED_WAIT_VISION;

    /* ──── 1. Alpha-Beta 滤波器 ──── */
    if (vision_ok) {
        if (!g_filter_init) {
            g_x_est = m.x_mm;
            g_v_est = 0.0f;
            g_filter_init = true;
        } else {
            float pred = g_x_est + g_v_est * BALL_CONTROL_PERIOD_S;
            float residual = m.x_mm - pred;
            g_x_est = pred + TEST_ALPHA * residual;
            g_v_est += (TEST_BETA / BALL_CONTROL_PERIOD_S) * residual;
            g_v_est = clampf(g_v_est, -TEST_SPEED_LIMIT_MM_S,
                                      TEST_SPEED_LIMIT_MM_S);
        }
    } else if (g_filter_init) {
        /* 视觉丢帧 → 纯预测 (不修正) */
        g_x_est = g_x_est + g_v_est * BALL_CONTROL_PERIOD_S;
    }

    /* ──── 2. PID 控制 (三段 KP + 三段限幅 + 速度前馈 + I 积分) ──── */
    if (g_filter_init) {
        float error = g_x_est - TEST_TARGET_MM;
        float abs_err = fabsf(error);

        /* ── I 积分 (直接累积为角度°, 条件抗饱和) ── */
        if (vision_ok && abs_err < TEST_INTEGRAL_WINDOW_MM) {
            /* KI * error * dt 直接得到角度增量 */
            g_i_angle_deg += TEST_KI * error * BALL_CONTROL_PERIOD_S;
            g_i_angle_deg = clampf(g_i_angle_deg,
                                   -TEST_INTEGRAL_LIMIT_DEG,
                                    TEST_INTEGRAL_LIMIT_DEG);
        }
        /* 误差大或丢帧 → 积分保持, 不清零 (避免丢失累积的补偿量) */

        /* 三段 KP + 三段限幅 */
        float kp, limit;
        if (abs_err <= TEST_THRESH_NEAR_MM) {
            kp = TEST_KP_NEAR;   limit = TEST_LIMIT_NEAR_DEG;
        } else if (abs_err <= TEST_THRESH_FAR_MM) {
            kp = TEST_KP_MID;    limit = TEST_LIMIT_MID_DEG;
        } else {
            kp = TEST_KP_FAR;    limit = TEST_LIMIT_FAR_DEG;
        }

        theta = (kp * error)                    /* P */
              + ((TEST_KD + TEST_KFF) * g_v_est) /* D + 前馈 */
              + g_i_angle_deg;                   /* I (已是角度) */
        theta = clampf(theta, -limit, limit);

        /* 线性 PWM 映射: theta>0 → 舵机端抬高 → 球向负方向 */
        pulse = (uint16_t)((float)TEST_PWM_LEVEL - theta * TEST_PWM_SLOPE);

        if (vision_ok) {
            led_mode = LED_PD_ACTIVE;
        } else {
            led_mode = LED_VISION_LOST;
        }
    } else {
        /* 还没收到第一帧 → 保持水平 */
        theta = 0.0f;
        pulse = TEST_PWM_LEVEL;
        led_mode = LED_WAIT_VISION;
    }

    /* ──── 3. 输出 PWM ──── */
    Platform_ServoWriteUs(pulse);

    /* ──── 4. 更新调试变量 ──── */
    g_debug_task_state     = (led_mode == LED_PD_ACTIVE) ? 2U : led_mode;
    g_debug_x_est_mm       = g_x_est;
    g_debug_v_est_mm_s     = g_v_est;
    g_debug_target_mm      = TEST_TARGET_MM;
    g_debug_error_mm       = g_x_est - TEST_TARGET_MM;
    g_debug_theta_cmd_deg  = theta;
    g_debug_servo_pulse_us = pulse;

    /* ──── 5. LED + 串口 ──── */
    {
        static uint8_t led_tick;
        static uint8_t prn_tick;
        static bool    led_state;

        led_tick++;

        switch (led_mode) {

        case LED_WAIT_VISION:
            /* 慢闪 500ms ON / 500ms OFF → 等 K230 数据 */
            if (led_tick >= 25U) {
                led_tick = 0U;
                led_state = !led_state;
                if (led_state)
                    DL_GPIO_setPins(BANG_LED_PORT, BANG_LED_PIN);
                else
                    DL_GPIO_clearPins(BANG_LED_PORT, BANG_LED_PIN);
            }
            break;

        case LED_PD_ACTIVE:
            /* 常亮 → PD 控制运行中 */
            DL_GPIO_setPins(BANG_LED_PORT, BANG_LED_PIN);
            led_tick = 0U;
            led_state = true;
            break;

        case LED_VISION_LOST:
            /* 快闪 100ms ON / 100ms OFF → 视觉丢失 */
            if (led_tick >= 5U) {
                led_tick = 0U;
                led_state = !led_state;
                if (led_state)
                    DL_GPIO_setPins(BANG_LED_PORT, BANG_LED_PIN);
                else
                    DL_GPIO_clearPins(BANG_LED_PORT, BANG_LED_PIN);
            }
            break;
        }

        /* 串口打印: 每 500ms */
        prn_tick++;
        if (prn_tick >= 25U) {
            prn_tick = 0U;

            UART_send_string(DEBUG_UART, "x=");
            UART_print_float1(DEBUG_UART, g_x_est);
            UART_send_string(DEBUG_UART, " T=");
            UART_print_float1(DEBUG_UART, TEST_TARGET_MM);
            UART_send_string(DEBUG_UART, " err=");
            UART_print_float1(DEBUG_UART, g_x_est - TEST_TARGET_MM);
            UART_send_string(DEBUG_UART, " v=");
            UART_print_float1(DEBUG_UART, g_v_est);
            UART_send_string(DEBUG_UART, " th=");
            UART_print_float1(DEBUG_UART, theta);
            UART_send_string(DEBUG_UART, " I=");
            UART_print_float1(DEBUG_UART, g_i_angle_deg);
            UART_send_string(DEBUG_UART, " PWM=");
            UART_print_int(DEBUG_UART, (int32_t)pulse);
            UART_send_string(DEBUG_UART, "us\r\n");
        }
    }
}
