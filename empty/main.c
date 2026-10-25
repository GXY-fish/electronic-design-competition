/*
 * H题 Ball-and-Beam PD Control (v5)
 * ===================================
 * 接收 K230 15字节二进制帧 → PD 控制器 → 舵机 PWM
 *
 * 坐标系: 中心 O=0mm, 右侧正, 左侧负
 * 舵机:   Servo_SetAngle(10) = 水管水平
 *         Servo_SetAngle(40) → 球往负方向
 *         Servo_SetAngle(80) → 球往正方向
 *
 * !!! 完全不使用 printf, 避免栈溢出 HardFault
 *
 * 硬件:
 *   UART3 (PA25=RX) <- K230 TXD (IO9)
 *   UART0 (PA10=TX) -> CH340 -> PC
 *   TIMG7 (PA24)     -> 舵机 PWM 50Hz
 *   PB22 = LED (心跳)
 */

#include "ti_msp_dl_config.h"
#include <string.h>
#include "board.h"
#include "bsp_uart.h"
#include "bsp_k230_protocol.h"
#include "servo.h"
#include "ball.h"

/* ====== PD 调参 (可在这里改) ====== */
#define KP  3.0f    // 比例增益
#define KD  0.5f    // 微分增益
#define BASELINE_ANGLE  165  // 水管水平时的舵机角度

/* ====== 自定义打印 (无 printf, 栈安全) ====== */

static void print_str(const char *s)
{
    uart0_send_string((char *)s);
}

static void print_int(int val)
{
    char buf[12];
    int i = 0, neg = 0;
    unsigned int uval;

    if (val < 0) { neg = 1; uval = (unsigned int)(-val); }
    else         { uval = (unsigned int)val; }

    if (uval == 0) buf[i++] = '0';
    else {
        while (uval > 0) { buf[i++] = '0' + (uval % 10); uval /= 10; }
    }
    if (neg) buf[i++] = '-';

    for (int j = 0; j < i / 2; j++) {
        char tmp = buf[j]; buf[j] = buf[i-1-j]; buf[i-1-j] = tmp;
    }
    buf[i] = '\0';
    print_str(buf);
}

/* ====== LED (PB22) ====== */
static void led_on(void)  { DL_GPIO_setPins(LED_PORT, LED_PIN_22_PIN); }
static void led_off(void) { DL_GPIO_clearPins(LED_PORT, LED_PIN_22_PIN); }
static void led_toggle(void) {
    static uint8_t s = 0;
    if (s) { led_off(); s = 0; } else { led_on(); s = 1; }
}

/* ====== 主程序 ====== */
int main(void)
{
    SYSCFG_DL_init();
    uart0_init();
    uart3_init();
    uart3_enable_rx_irq();

    /* 舵机初始化 + 水管水平 */
    Servo_Init();
    Servo_SetAngle(BASELINE_ANGLE);

    /* PD 控制初始化 */
    BallControl g_ball;
    Ball_Init(&g_ball, KP, KD, BASELINE_ANGLE);
    Ball_SetReference(&g_ball, 0);  // 目标 = 原点

    delay_ms(200);
    led_on();

    /* Banner */
    print_str("\r\n==============================================\r\n");
    print_str("  H  Ball-and-Beam PD Control v5\r\n");
    print_str("  KP="); print_int((int)KP);
    print_str(" KD="); print_int((int)(KD*10));
    print_str("/10  baseline="); print_int(BASELINE_ANGLE);
    print_str("deg\r\n");
    print_str("  Target: 0mm (origin)\r\n");
    print_str("  >>> Pipe is level. Place the ball. <<<\r\n");
    print_str("==============================================\r\n\r\n");

    delay_ms(100);
    led_off();

    int sys_tick = 0;
    int frame_count = 0;
    int fps = 0;
    int fps_count = 0;
    int fps_timer = 0;

    while (1)
    {
        sys_tick++;
        delay_ms(1);

        /* 协议解析 */
        Pto_Loop();

        BallVision_t ball;
        if (BallVision_Read(&ball))
        {
            frame_count++;
            fps_count++;

            int valid = (ball.flags & 0x01);

            /* 更新位置 + PD 计算 + 驱动舵机 */
            Ball_UpdatePosition(&g_ball, ball.x_mm, ball.v_ab_mm_s, valid);

            if (valid) {
                /* 球可见: PD 使能 + 计算舵机角度 */
                g_ball.pd_enabled = 1;
                int servo_out = Ball_Compute(&g_ball);
                Servo_SetAngle(servo_out);
            } else {
                /* 球丢: 丢球保护 */
                Ball_LostProtect(&g_ball);
                Servo_SetAngle(g_ball.servo_angle);
            }
        }

        /* 1Hz: LED + 状态输出 */
        if (sys_tick % 1000 == 0)
        {
            led_toggle();

            if (sys_tick - fps_timer >= 1000) {
                fps = fps_count;
                fps_count = 0;
                fps_timer = sys_tick;
            }

            print_str("[PD] target=");
            print_int((int)g_ball.target_mm);
            print_str("mm  pos=");
            print_int(g_ball.current_mm);
            print_str("mm  vel=");
            print_int(g_ball.current_v);
            print_str("mm/s  servo=");
            print_int(g_ball.servo_angle);
            print_str("deg  fps=");
            print_int(fps);
            if (!g_ball.ball_valid) print_str("  [LOST]");
            if (!g_ball.pd_enabled) print_str("  [PD OFF]");
            print_str("\r\n");
        }
    }
}
