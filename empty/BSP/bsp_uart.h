#ifndef __BSP_UART_H__
#define __BSP_UART_H__

#include "board.h"

/* ====== UART0: 调试串口 (板载 CH340, PA10=TX, PA11=RX, 115200) ====== */

/* 初始化 (默认不开启 RX 中断, 只配置 TX 可用) */
void uart0_init(void);

/* 显式开启 UART0 RX 中断 (需要接收/回显时调用) */
void uart0_enable_rx_irq(void);

void uart0_send_char(unsigned char data);
void uart0_send_string(char *str);

/* UART0 接收环形缓冲区 (ISR 写入, 主循环读取) */
extern volatile uint8_t g_uart0_rx_flag;        /* 1=有新数据待处理 */
extern volatile uint8_t g_uart0_rx_data;        /* 兼容旧接口 */
extern volatile uint8_t g_uart0_rx_buf[];       /* 环形缓冲区 */
extern volatile uint8_t g_uart0_rx_head;        /* ISR 写入位置 */
extern volatile uint8_t g_uart0_rx_tail;        /* 主循环读取位置 */

/* 从环形缓冲区读取 1 字节, 返回 1=有数据, 0=空 */
static inline uint8_t uart0_read_byte(uint8_t *out)
{
    if (g_uart0_rx_head != g_uart0_rx_tail)
    {
        *out = g_uart0_rx_buf[g_uart0_rx_tail];
        g_uart0_rx_tail = (g_uart0_rx_tail + 1) % 16;
        return 1;
    }
    return 0;
}

/* ====== UART3: K230 通信串口 (PA26=TX, PA25=RX, 115200) ====== */

/* 初始化 (默认不开启 RX 中断, 只配置 TX 可用) */
void uart3_init(void);

/* 显式开启 UART3 RX 中断 (K230 确认连接后调用) */
void uart3_enable_rx_irq(void);

/* 显式关闭 UART3 RX 中断 */
void uart3_disable_rx_irq(void);

void uart3_send_char(unsigned char data);
void uart3_send_string(char *str);

#endif
