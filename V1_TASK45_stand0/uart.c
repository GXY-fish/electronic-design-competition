#include "uart.h"
#include "ball_app.h"
volatile uint32_t g_uart_rx_byte_count = 0U;
volatile uint8_t g_uart_last_byte = 0U;




void UART_send_char(UART_Regs *uart, const uint8_t chr)
{
    DL_UART_transmitDataBlocking(uart, chr);
}

void UART_send_string(UART_Regs *uart, const char *str)
{
    while (*str) {
        UART_send_char(uart, (uint8_t) *str);
        str++;
    }
}

void UART_print_int(UART_Regs *uart, int32_t val)
{
    char buf[12];
    uint32_t v;
    int i = 0;

    if (val < 0) {
        UART_send_char(uart, '-');
        v = (uint32_t)(-val);
    } else {
        v = (uint32_t)val;
    }

    do {
        buf[i++] = (char)('0' + (v % 10U));
        v /= 10U;
    } while (v > 0U);

    while (i > 0) {
        i--;
        UART_send_char(uart, (uint8_t)buf[i]);
    }
}

void UART_print_float1(UART_Regs *uart, float val)
{
    int32_t int_part;
    uint8_t frac;

    if (val < 0.0f) {
        UART_send_char(uart, '-');
        val = -val;
    }

    int_part = (int32_t)val;
    frac = (uint8_t)((val - (float)int_part) * 10.0f + 0.5f);
    if (frac >= 10U) {
        int_part++;
        frac = 0U;
    }

    UART_print_int(uart, int_part);
    UART_send_char(uart, '.');
    UART_send_char(uart, (uint8_t)('0' + frac));
}

void PRINT_INST_IRQHandler(void)
{
    switch (DL_UART_Main_getPendingInterrupt(PRINT_INST)) {
    case DL_UART_MAIN_IIDX_RX:
        while (!DL_UART_Main_isRXFIFOEmpty(PRINT_INST)) {
            uint8_t byte =
                (uint8_t)DL_UART_Main_receiveData(PRINT_INST);

            g_uart_last_byte = byte;
            g_uart_rx_byte_count++;

            BallBalanceApp_OnUartRxByte(byte);
        }
        break;

    default:
        break;
    }
}
