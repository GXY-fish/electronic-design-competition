/**
 * @file    main.c
 * @brief   WHEEL_bige — 五步因果链 PID 巡线
 *          MSPM0G3507 天猛星 LQFP-64
 *
 *   Step1: 8路GPIO → e_line (权重法, line_sensor)
 *   Step2: PD → yaw_rate (无积分)
 *   Step3: 弯道自动降速
 *   Step4: 差速 → left/right target
 *   Step5: 前馈+PI → 每电机独立闭环 → PWM
 */

#include "main.h"
#include "hardware/Encoder.h"
#include "hardware/motor_ctrl.h"
#include "hardware/usart.h"
#include "delay.h"

#include "Chassis/vehicle_param.h"
#include "Chassis/vehicle.h"
#include "Chassis/vehicle_track.h"
#include "Chassis/line_sensor.h"
#include "Chassis/motor_pid.h"

volatile uint32_t g_msTick = 0;

float   Basic_Speed     = 30.0f;
float   Target_Distance = 0.0f;
uint8_t Car_Mode        = Xunji_Mode;

/* ================================================================
 * UART 打印
 * ================================================================ */

static void uart_print(const char *s) {
    while (*s) DL_UART_transmitDataBlocking(UART_0_INST, *s++);
}
static void uart_print_int(int n) {
    char buf[12]; int i = 0, neg = 0;
    if (n < 0) { neg = 1; n = -n; }
    do { buf[i++] = '0' + (n % 10); n /= 10; } while (n > 0);
    if (neg) buf[i++] = '-';
    while (i--) DL_UART_transmitDataBlocking(UART_0_INST, buf[i]);
}
static void uart_print_float(float f, int d)
{
    if (f < 0) { uart_print("-"); f = -f; }
    int ip = (int)f; uart_print_int(ip); uart_print(".");
    for (int i = 0; i < d; i++) { f = (f - ip) * 10; ip = (int)f; uart_print_int(ip); }
}

static const char *StateName(VehicleState_t s)
{
    switch (s) {
    case VEH_INIT:       return "INIT";
    case VEH_TRACK:      return "TRK";
    case VEH_LOST_HOLD:  return "HOLD";
    case VEH_SEARCH:     return "SRCH";
    case VEH_RECOVER:    return "RECV";
    case VEH_FAULT:      return "FAULT";
    default:             return "?";
    }
}

/* ================================================================
 * App_Task10ms — 五步核心
 * ================================================================ */

void App_Task10ms(void)
{
    /* Step 0: 编码器测速 */
    MEASURE_MOTORS_SPEED();

    /* Step 1: 8路GPIO → e_line */
    LineSensor_Update();

    /* Step 1.5: 状态机 */
    Vehicle_UpdateState();

    /* Step 2+3+4: PD转向 → 降速 → 差速 */
    Vehicle_Control();

    /* Step 4.5: 目标传给电机 */
    Vehicle_ApplyTarget();

    /* Step 5: 前馈+PI → PWM */
    Motor_PID_Update();
}

/* ================================================================
 * 定时器中断 (1ms)
 * ================================================================ */

void TIMER_0_INST_IRQHandler(void)
{
    static uint16_t count_10ms = 0;
    static uint16_t t_1s       = 0;

    g_msTick++;
    delay_tick_inc();

    switch (DL_TimerA_getPendingInterrupt(TIMER_0_INST))
    {
    case DL_TIMERA_IIDX_ZERO:
        if (++count_10ms >= 10) {
            count_10ms = 0;
            App_Task10ms();
        }
        /* LED = 读到线亮, 丢线灭 (每 100ms 更新) */
        if (++t_1s >= 100) {
            t_1s = 0;
            if (g_line.valid)
                DL_GPIO_setPins(LED_PORT, LED_PIN_0_PIN);
            else
                DL_GPIO_clearPins(LED_PORT, LED_PIN_0_PIN);
        }
        break;
    default:
        break;
    }
}

/* ================================================================
 * 中断初始化
 * ================================================================ */

void NVIC_EnableIRQ_Init(void)
{
    NVIC_ClearPendingIRQ(Encoder_INT_IRQN);
    NVIC_EnableIRQ(Encoder_INT_IRQN);

    NVIC_ClearPendingIRQ(TIMER_0_INST_INT_IRQN);
    NVIC_EnableIRQ(TIMER_0_INST_INT_IRQN);
    DL_TimerA_startCounter(TIMER_0_INST);
}

/* ================================================================
 * 主函数
 * ================================================================ */

int main(void)
{
    SYSCFG_DL_init();
    NVIC_EnableIRQ_Init();

    /* 框架初始化 (不碰 GPIO 传感器) */
    LineSensor_Init();
    Motor_PID_Init();
    Vehicle_Init();
    Ctrl_Track_Init();

    MOTORS_ENABLE();

    uart_print("WHEEL_bige Start\r\n");

    while (1)
    {
        static uint32_t last = 0;
        if (g_msTick - last >= 200) {
            last = g_msTick;

            /* 传感器可视化 */
            uart_print("[");
            uart_print(StateName(g_vehicle.state));
            uart_print("] ");
            for (int i = 0; i < 8; i++)
                uart_print(LineSensor_GetChannel(i) ? "." : "#");

            uart_print(" e=");
            uart_print_float(g_line.error, 1);

            uart_print(" L=");
            uart_print_int((int)g_vehicle.left_target);
            uart_print(" R=");
            uart_print_int((int)g_vehicle.right_target);

            uart_print(" M:");
            uart_print_int((int)Motor_GetSpeed(MOTOR_LF));
            uart_print(",");
            uart_print_int((int)Motor_GetSpeed(MOTOR_RF));

            uart_print("\r\n");
        }
        delay_ms(5);
    }
}
