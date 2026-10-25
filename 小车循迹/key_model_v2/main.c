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
#include "hardware/keypad.h"
#include "delay.h"

#include "Chassis/vehicle_param.h"
#include "Chassis/vehicle.h"
#include "Chassis/vehicle_track.h"
#include "Chassis/line_sensor.h"
#include "Chassis/motor_pid.h"
#include "Chassis/lap_detect.h"

volatile uint32_t g_msTick = 0;
volatile uint8_t  g_lap_done = 0;   /* 圈数达标标志, 主循环处理停车 */

float   Basic_Speed     = 75.0f;  /* x2.5 */
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
static void uart_print_hex8(uint8_t v) {
    static const char hex[] = "0123456789ABCDEF";
    DL_UART_transmitDataBlocking(UART_0_INST, hex[v >> 4]);
    DL_UART_transmitDataBlocking(UART_0_INST, hex[v & 0xF]);
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

    /* Step 1.2: 5 路黑检测 — 第一次记录, 第二次急刹 */
    {
        static uint8_t mark_enter = 0;   /* 进入胶布次数 */
        static uint8_t was_on    = 0;    /* 上一周期是否在胶布上 */
        static uint8_t debounce  = 0;    /* 消抖计数 */

        uint8_t ir = LineSensor_GetAllChannels();
        uint8_t black_cnt = 0;
        for (int i = 0; i < 8; i++) {
            if (!(ir & (1 << (7 - i)))) black_cnt++;
        }

        if (black_cnt >= 5) {
            if (debounce < 5) debounce++;        /* 需连续 5 次确认 */
            if (debounce == 5 && !was_on) {      /* 上升沿: 刚进入胶布 */
                was_on = 1;
                mark_enter++;
                if (mark_enter >= 2) {           /* 第二次进入 → 刹! */
                    MOTORS_DISABLE();
                    g_lap_done = 1;
                }
            }
        } else {
            debounce = 0;
            was_on  = 0;                         /* 离开胶布, 复位 */
        }
    }

    /* Step 1.3: 圈数统计 (仅串口显示用) */
    LapDetect_Task();

    /* Step 1.5: 状态机 */
    Vehicle_UpdateState();

    /* Step 2+3+4: PD转向 → 降速 → 差速 */
    Vehicle_Control();

    /* Step 4.5: 目标传给电机 */
    Vehicle_ApplyTarget();

    /* Step 5: 前馈+PI → PWM */
    Motor_PID_Update();

    /* Step 6: 矩阵键盘扫描 (10ms间隔, 20ms消抖) */
    Keypad_Scan();
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
    LapDetect_Reset();

    /* 键盘初始化 (放在所有硬件初始化之后) */
    Keypad_Init();

    /* 启动时静止, 按 key4 才走 */
    uart_print("WHEEL_bige Ready - press key4 to start\r\n");

    /* 天猛星板子 PB25 连接电机驱动使能, 上电需 LOW 脉冲激活 */
    DL_GPIO_clearPins(GPIOB, DL_GPIO_PIN_25);
    for (volatile int _d = 0; _d < 200; _d++) __asm volatile ("nop");
    DL_GPIO_setPins(GPIOB, DL_GPIO_PIN_25);

    while (1)
    {
        /* 每 10ms 一轮: 传感器 + 状态机 + 电机控制 + 键盘扫描 */
        App_Task10ms();
        delay_ms(10);

        /* 圈数达标 → 急刹停车 */
        if (g_lap_done) {
            MOTORS_DISABLE();
            uart_print(">>> LAP DONE - STOP <<<\r\n");
            g_lap_done = 0;
        }

        /* 每 200ms 键盘处理 + 数据显示 */
        static uint8_t tick200 = 0;
        if (++tick200 >= 20) {
            tick200 = 0;

            /* LED */
            if (g_line.valid)
                DL_GPIO_setPins(LED_PORT, LED_PIN_0_PIN);
            else
                DL_GPIO_clearPins(LED_PORT, LED_PIN_0_PIN);

            /* 键盘 */
            {
                static uint8_t prev_key = KEYPAD_NO_KEY;
                uint8_t k = Keypad_GetKey();

                if (k != prev_key) {
                    prev_key = k;

                    if (k != KEYPAD_NO_KEY) {
                        uart_print(" >>> key");
                        uart_print_int(k);
                        uart_print(" down");
                    }

                    switch (k) {
                    case 1: Basic_Speed += 5.0f;
                        if (Basic_Speed > 100.0f) Basic_Speed = 100.0f;
                        break;
                    case 2: Basic_Speed -= 5.0f;
                        if (Basic_Speed < 10.0f) Basic_Speed = 10.0f;
                        break;
                    case 3: MOTORS_DISABLE(); break;
                    case 4: MOTORS_ENABLE();
                        uart_print(" START!");
                        break;
                    case 5: Car_Mode = (Car_Mode + 1) % 5; break;
                    default: break;
                    }
                    uart_print("\r\n");
                }
            }

            uart_print("[");
            uart_print(StateName(g_vehicle.state));
            uart_print("] ");
            for (int i = 0; i < 8; i++)
                uart_print(LineSensor_GetChannel(i) ? "." : "#");
            uart_print(" ir=0x");
            uart_print_hex8(LineSensor_GetAllChannels());
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
            uart_print(" S:");
            uart_print_int((int)Basic_Speed);
            uart_print(" Lap:");
            uart_print_int(LapDetect_GetCount());
            uart_print("\r\n");
        }
    }
}
