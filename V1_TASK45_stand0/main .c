/*
 * ==================== PD+I 闭环控制 ====================
 *
 * UART 分配:
 *   UART3 (PA25/RX, PA26/TX) — K230 视觉数据输入
 *   UART0 (PA11/TX)          — CH340 调试串口输出 (PC 串口助手)
 *
 *   SysTick 1kHz → 每 20ms 触发 ball_app 状态机
 * ============================================================
 */

#include "ti_msp_dl_config.h"

#include "uart.h"
#include "ball_app.h"
#include "ball_config.h"
#include "platform_port.h"

#include <stdbool.h>
#include <stdint.h>

static volatile uint32_t g_system_ms;
static volatile bool g_ball_20ms_due;

/* ── SysTick: 1kHz 时基 ── */
void SysTick_Handler(void)
{
    static uint8_t divider_20ms;

    g_system_ms++;
    divider_20ms++;
    if (divider_20ms >= 20U) {
        divider_20ms = 0U;
        g_ball_20ms_due = true;
    }
}

uint32_t Platform_GetMillis(void)
{
    return g_system_ms;
}

/* ── 舵机 PWM 输出 (500~2500μs 硬件钳位) ── */
void Platform_ServoWriteUs(uint16_t pulse_us)
{
    uint32_t compare_value;

    if (pulse_us < 500U) {
        pulse_us = 500U;
    } else if (pulse_us > 2500U) {
        pulse_us = 2500U;
    }

    compare_value =
        ((uint32_t)pulse_us * SERVO_INST_CLK_FREQ + 500000U) / 1000000U;
    DL_Timer_setCaptureCompareValue(
        SERVO_INST, compare_value, GPIO_SERVO_C1_IDX);
}

void Platform_DisplayResult(uint32_t elapsed_ms,
                            float error_mm,
                            uint16_t fault_flags)
{
    (void)elapsed_ms;
    (void)error_mm;
    (void)fault_flags;
}

/* ═══════════════════════════════════════════════════════════════════
 *  main
 *
 *  调试串口: UART1 TX (PB6) → CH340 RXD → PC 串口助手
 *  SysConfig 已初始化 UART1, 无需手动配置.
 * ═══════════════════════════════════════════════════════════════════ */
int main(void)
{
    /* ── 硬件初始化 ── */
    SYSCFG_DL_init();

    /* PB22 (IOMUX_PINCM50) → 板载 LED */
    DL_GPIO_initDigitalOutput(IOMUX_PINCM50);
    DL_GPIO_clearPins(BANG_LED_PORT, BANG_LED_PIN);

    /* SysTick 1kHz */
    g_system_ms = 0U;
    g_ball_20ms_due = false;
    (void)SysTick_Config(CPUCLK_FREQ / 1000U);

    /* ── 应用初始化 (先设 PWM=2375, 初始化 vision 协议, 再启定时器) ── */
    BallBalanceApp_Init();
    DL_Timer_startCounter(SERVO_INST);

    /* UART3 RX 中断 — 必须在 VisionProtocol_Init() 之后使能! */
    NVIC_EnableIRQ(PRINT_INST_INT_IRQN);

    /* ── 启动提示 ── */
    UART_send_string(DEBUG_UART,
        "\r\n=== PD Test: Target = -5cm ===\r\n");

    /* ── 主循环: 20ms 周期运行 PD 闭环控制 ── */
    while (1) {
        if (g_ball_20ms_due) {
            __disable_irq();
            g_ball_20ms_due = false;
            __enable_irq();
            BallBalanceApp_Update20ms();
        }
    }
}
