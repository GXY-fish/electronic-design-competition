#include "bsp_uart.h"
#include "bsp_k230_protocol.h"

/* ============================================================
 * UART0: 调试串口 (板载 CH340, PA10=TX, PA11=RX, 115200)
 * USB 线直连电脑, printf 重定向在 board.c 的 fputc 中实现
 *
 * 中断策略:
 *   uart0_init() 默认不开启 RX 中断
 *   需要回显/接收时调用 uart0_enable_rx_irq()
 *   这样测试程序不会误触发中断
 * ============================================================ */

/* UART0 接收环形缓冲区: ISR 写入, 主循环读取
 * 16 字节足够存放一条命令 + 换行符 */
#define UART0_RX_BUF_SIZE 16
volatile uint8_t g_uart0_rx_buf[UART0_RX_BUF_SIZE];
volatile uint8_t g_uart0_rx_head = 0;   /* ISR 写入位置 */
volatile uint8_t g_uart0_rx_tail = 0;   /* 主循环读取位置 */

/* 兼容旧接口 */
volatile uint8_t g_uart0_rx_flag = 0;
volatile uint8_t g_uart0_rx_data = 0;

void uart0_init(void)
{
    /* 默认不开启 RX 中断, 避免悬空引脚噪声导致死机
     * 需要接收功能时调用 uart0_enable_rx_irq() */
}

void uart0_enable_rx_irq(void)
{
    DL_UART_Main_enableInterrupt(UART_0_INST, DL_UART_MAIN_INTERRUPT_RX);
    NVIC_ClearPendingIRQ(UART_0_INST_INT_IRQN);
    NVIC_EnableIRQ(UART_0_INST_INT_IRQN);
}

void uart0_send_char(unsigned char data)
{
    uint32_t timeout = 10000;
    while (DL_UART_isBusy(UART_0_INST) == true && timeout-- > 0) {}
    DL_UART_Main_transmitData(UART_0_INST, data);
}

void uart0_send_string(char *str)
{
    while (*str != 0 && str != 0)
    {
        uart0_send_char(*str++);
    }
}

/* UART0 中断: 调试接收 (回显)
 * 只有调用了 uart0_enable_rx_irq() 后才会触发 */
void UART_0_INST_IRQHandler(void)
{
    uint8_t receivedData = 0;
    switch (DL_UART_getPendingInterrupt(UART_0_INST))
    {
        case DL_UART_IIDX_RX:
            receivedData = DL_UART_Main_receiveData(UART_0_INST);
            /* 回显: 中断里直接写 TX 寄存器, 不调 uart0_send_char (避免 isBusy 死锁) */
            DL_UART_Main_transmitData(UART_0_INST, receivedData);
            /* 写入环形缓冲区 */
            {
                uint8_t next = (g_uart0_rx_head + 1) % UART0_RX_BUF_SIZE;
                if (next != g_uart0_rx_tail)  /* 缓冲未满 */
                {
                    g_uart0_rx_buf[g_uart0_rx_head] = receivedData;
                    g_uart0_rx_head = next;
                }
            }
            g_uart0_rx_flag = 1;
            break;
        default:
            break;
    }
}

/* ============================================================
 * UART3: K230 通信串口 (PA26=TX, PA25=RX, 115200)
 * K230 TX(IO9) -> MSPM0 PA25(RX)
 * K230 RX(IO10) <- MSPM0 PA26(TX)
 * RX 中断接收 K230 检测数据, 喂入协议解析状态机
 *
 * 中断策略:
 *   uart3_init() 默认不开启 RX 中断
 *   必须在 K230 确认连接后调用 uart3_enable_rx_irq()
 *   避免PA25悬空时中断风暴死机
 * ============================================================ */

void uart3_init(void)
{
    /* 默认不开启 RX 中断
     * SysConfig 已配置 UART3 硬件, 但不自动使能 RX 中断
     * K230 连接确认后调用 uart3_enable_rx_irq() */
}

void uart3_enable_rx_irq(void)
{
    DL_UART_Main_enableInterrupt(UART_3_INST, DL_UART_MAIN_INTERRUPT_RX);
    NVIC_ClearPendingIRQ(UART_3_INST_INT_IRQN);
    NVIC_EnableIRQ(UART_3_INST_INT_IRQN);
}

void uart3_disable_rx_irq(void)
{
    NVIC_DisableIRQ(UART_3_INST_INT_IRQN);
    DL_UART_Main_disableInterrupt(UART_3_INST, DL_UART_MAIN_INTERRUPT_RX);
}

void uart3_send_char(unsigned char data)
{
    uint32_t timeout = 10000;
    while (DL_UART_isBusy(UART_3_INST) == true && timeout-- > 0) {}
    DL_UART_Main_transmitData(UART_3_INST, data);
}

void uart3_send_string(char *str)
{
    while (*str != 0 && str != 0)
    {
        uart3_send_char(*str++);
    }
}

/* UART3 中断: 接收 K230 数据，喂入协议解析状态机
 * 只有调用了 uart3_enable_rx_irq() 后才会触发 */
void UART_3_INST_IRQHandler(void)
{
    uint8_t received = 0;
    switch (DL_UART_getPendingInterrupt(UART_3_INST))
    {
        case DL_UART_IIDX_RX:
            received = DL_UART_Main_receiveData(UART_3_INST);
            Pto_Data_Receive(received);
            break;
        default:
            break;
    }
}
