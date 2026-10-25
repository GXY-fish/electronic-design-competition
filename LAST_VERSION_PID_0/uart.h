#ifndef UART_H
#define UART_H

#include "ti_msp_dl_config.h"

void UART_send_string(UART_Regs *uart, const char *str);
void UART_send_char(UART_Regs *uart, const uint8_t chr);
void UART_print_int(UART_Regs *uart, int32_t val);
void UART_print_float1(UART_Regs *uart, float val);

#endif /* UART_H */
