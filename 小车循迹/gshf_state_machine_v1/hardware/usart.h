/**
 * @file    usart.h
 * @brief   UART 驱动头文件 (UART0, PA10/PA11, 115200bps)
 */

#ifndef __USART_H__
#define __USART_H__

#include "main.h"

void uart0_send_char(char ch);
void uart0_send_string(char *str);
void usart0_send_byte(unsigned char byte);
void usart0_send_bytes(unsigned char *buf, int len);
uint8_t HAL_UART_Transmit(uint8_t *pData, uint16_t Size, uint32_t Timeout);

/* printf 重定向 */
int fputc(int ch, FILE *f);

/* VOFA+ JustFloat 协议 */
void JustFloat_SendArray(uint8_t *string, uint8_t length);
void Float_to_Byte(float f, unsigned char byte[]);
void vofa_sendData(float a, float b, float c, float d);

#endif /* __USART_H__ */
