/**
 * @file    main.c
 * @brief   wheel_4 — 四驱小车控制程序
 *          MSPM0G3507 天猛星 LQFP-64
 *          TIMER_0 (TIMA1): 1ms 周期中断
 *          PWM_0  (TIMA0): 4ch PWM → M1~M4
 *          Encoder: GPIOB 8ch → GROUP1_IRQHandler
 */

#include "main.h"
#include "hardware/Encoder.h"
#include "hardware/motor_ctrl.h"
#include "hardware/usart.h"
#include "hardware/protocol.h"
#include "hardware/xunji.h"
#include "delay.h"

volatile uint32_t g_msTick = 0;  /* 1ms 计数器 */

/* 简单整数→串口打印 (绕过 printf) */
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

/* ---- 全局变量 ---- */
float   Basic_Speed     = 0;
float   Target_Distance = 0;
uint8_t Car_Mode        = Xunji_Mode;

/* ---- 定时器中断 (TIMER_0, TIMA1, 1ms) ---- */
void TIMER_0_INST_IRQHandler(void)
{
    static uint16_t count_10ms = 0;
    static uint16_t t_1s       = 0;

    g_msTick++;                 /* 全局毫秒计数 */
    delay_tick_inc();           /* delay 模块计数 */

    switch (DL_TimerA_getPendingInterrupt(TIMER_0_INST))
    {
    case DL_TIMERA_IIDX_ZERO:
    {
        if (++count_10ms >= 10)
        {
            count_10ms = 0;

            /* 10ms 控制周期 */
            MEASURE_MOTORS_SPEED();

            if (Car_Mode == Xunji_Mode && xj_enable)
            {
                /* 巡线模式: PD 控制 (传感器数据由主循环 XJ_Update 更新) */
                XJ_LineFollowing_Update();
            }
            else
            {
                /* 速度 PID 控制 */
                int s1 = (int)PID_Calculate(&pid_Motor1_Speed, Motor1_Speed, Basic_Speed);
                int s2 = (int)PID_Calculate(&pid_Motor2_Speed, Motor2_Speed, Basic_Speed);
                int s3 = (int)PID_Calculate(&pid_Motor3_Speed, Motor3_Speed, Basic_Speed);
                int s4 = (int)PID_Calculate(&pid_Motor4_Speed, Motor4_Speed, Basic_Speed);

                SET_MOTORS_SPEED(s1, s2, s3, s4);
            }
        }

        /* 1s LED 心跳 */
        if (++t_1s >= 1000) {
            t_1s = 0;
            DL_GPIO_togglePins(LED_PORT, LED_PIN_0_PIN);
        }
        break;
    }
    default:
        break;
    }
}

/* ---- 中断初始化 ---- */
void NVIC_EnableIRQ_Init(void)
{
    /* 编码器中断 */
    NVIC_ClearPendingIRQ(Encoder_INT_IRQN);
    NVIC_EnableIRQ(Encoder_INT_IRQN);

    /* 定时器中断 */
    NVIC_ClearPendingIRQ(TIMER_0_INST_INT_IRQN);
    NVIC_EnableIRQ(TIMER_0_INST_INT_IRQN);
    DL_TimerA_startCounter(TIMER_0_INST);

    /* UART RX 中断 */
    NVIC_ClearPendingIRQ(UART_0_INST_INT_IRQN);
    NVIC_EnableIRQ(UART_0_INST_INT_IRQN);
}

/* ---- 协议数据处理 (仅响应上位机命令，不主动发送) ---- */
void Protocol_Datas_Proc(void)
{
    if (Car_Mode != Run_Mode)
    {
        receiving_process();  /* 处理收到的 UART 命令 */
    }
}

/* ---- 主函数 ---- */
int main(void)
{
    SYSCFG_DL_init();

    /* 硬件初始化 */
    protocol_init();
    NVIC_EnableIRQ_Init();

    /* 初始化速度 PID */
    Set_PID_Param(&pid_Motor1_Speed, 100, 20, 10);
    Set_PID_Param(&pid_Motor2_Speed, 100, 20, 10);
    Set_PID_Param(&pid_Motor3_Speed, 100, 20, 10);
    Set_PID_Param(&pid_Motor4_Speed, 100, 20, 10);

    /* 初始化巡线传感器 */
    XJ_Init();
    XJ_LineFollowing_Init();

    /* 默认使能电机，设置目标速度，轮子开始转动 */
    Basic_Speed = 30;    /* 目标速度 30 cm/s */
    MOTORS_ENABLE();

    /* 启动信息 (用自定义函数，不依赖 printf) */
    uart_print("wheel_4 + Xunji Start, CPR=");
    uart_print_int(CPR);
    uart_print(" Diam=65mm\r\n");

    while (1)
    {
        /* 传感器数据读取 (主循环中调用, 避免 ISR 中 I2C 阻塞) */
        XJ_Update();

        /* 每 200ms 打印调试信息 */
        static uint32_t last_print = 0;
        static int32_t  last_cpr[4] = {0, 0, 0, 0};
        if (delay_ms_gettick() - last_print >= 200) {
            last_print = delay_ms_gettick();

            if (Car_Mode == Xunji_Mode)
            {
                /* 巡线模式: 打印传感器 + 偏差 + I2C状态 */
                uart_print("XJ:");
                for (int i = 0; i < 8; i++) {
                    uart_print(XJ_GetValue(i) ? "." : "#");
                }
                uart_print(" err:"); uart_print_int((int)xj_error);
                uart_print(" M1:");  uart_print_int((int)Motor1_Speed);
                uart_print(" M2:");  uart_print_int((int)Motor2_Speed);
                uart_print(" M3:");  uart_print_int((int)Motor3_Speed);
                uart_print(" M4:");  uart_print_int((int)Motor4_Speed);
                uart_print("\r\n");
            }
            else
            {
                /* 计算 200ms 内的编码器增量 */
                int32_t d[4];
                d[0] = Motor1_Encoder_Value - last_cpr[0]; last_cpr[0] = Motor1_Encoder_Value;
                d[1] = Motor2_Encoder_Value - last_cpr[1]; last_cpr[1] = Motor2_Encoder_Value;
                d[2] = Motor3_Encoder_Value - last_cpr[2]; last_cpr[2] = Motor3_Encoder_Value;
                d[3] = Motor4_Encoder_Value - last_cpr[3]; last_cpr[3] = Motor4_Encoder_Value;

                uart_print("dCPR:"); uart_print_int(d[0]);
                uart_print(" ");      uart_print_int(d[1]);
                uart_print(" ");      uart_print_int(d[2]);
                uart_print(" ");      uart_print_int(d[3]);
                uart_print(" | Spd:");uart_print_int((int)Motor1_Speed);
                uart_print(" ");      uart_print_int((int)Motor2_Speed);
                uart_print(" ");      uart_print_int((int)Motor3_Speed);
                uart_print(" ");      uart_print_int((int)Motor4_Speed);
                uart_print(" | ISR:");uart_print_int((int)g_enc_isr_cnt[0]);
                uart_print(" ");       uart_print_int((int)g_enc_isr_cnt[1]);
                uart_print(" ");       uart_print_int((int)g_enc_isr_cnt[2]);
                uart_print(" ");       uart_print_int((int)g_enc_isr_cnt[3]);
                uart_print("\r\n");
            }
        }

        Protocol_Datas_Proc();
        delay_ms(5);
    }
}
