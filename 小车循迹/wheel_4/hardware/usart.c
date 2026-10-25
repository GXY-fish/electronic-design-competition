/**
 * @file    usart.c
 * @brief   UART 驱动 — UART0 PA10/PA11, 115200bps
 */

#include "usart.h"
#include "protocol.h"

void uart0_send_char(char ch)
{
    while (DL_UART_isBusy(UART_0_INST) == true);
    DL_UART_Main_transmitData(UART_0_INST, ch);
}

void uart0_send_string(char *str)
{
    while (*str != 0 && str != 0) {
        uart0_send_char(*str++);
    }
}

void usart0_send_byte(unsigned char byte)
{
    DL_UART_Main_transmitDataBlocking(UART_0_INST, byte);
}

void usart0_send_bytes(unsigned char *buf, int len)
{
    while (len--) {
        DL_UART_Main_transmitDataBlocking(UART_0_INST, *buf);
        buf++;
    }
}

uint8_t HAL_UART_Transmit(uint8_t *pData, uint16_t Size, uint32_t Timeout)
{
    (void)Timeout;
    uint8_t *pdata8bits = pData;
    uint16_t TxXferCount = Size;
    while (TxXferCount > 0U) {
        if (pdata8bits != NULL) {
            DL_UART_Main_transmitDataBlocking(UART_0_INST, *pdata8bits);
            pdata8bits++;
        }
        TxXferCount--;
    }
    return 1;
}

int fputc(int ch, FILE *f)
{
    (void)f;
    DL_UART_Main_transmitDataBlocking(UART_0_INST, (uint8_t)ch);
    return ch;
}

/* ---- VOFA+ JustFloat ---- */
typedef union {
    float fdata;
    unsigned long ldata;
} FloatLongType;

void JustFloat_SendArray(uint8_t *string, uint8_t length)
{
    while (length--) {
        DL_UART_Main_transmitDataBlocking(UART_0_INST, *string++);
    }
}

void Float_to_Byte(float f, unsigned char byte[])
{
    FloatLongType fl;
    fl.fdata = f;
    byte[0] = (unsigned char)fl.ldata;
    byte[1] = (unsigned char)(fl.ldata >> 8);
    byte[2] = (unsigned char)(fl.ldata >> 16);
    byte[3] = (unsigned char)(fl.ldata >> 24);
}

/* 发送 4 通道 float 数据到 VOFA+ */
void vofa_sendData(float a, float b, float c, float d)
{
    u8 byte[4] = {0};
    u8 tail[4] = {0x00, 0x00, 0x80, 0x7f};

    Float_to_Byte(a, byte);
    JustFloat_SendArray(byte, 4);
    Float_to_Byte(b, byte);
    JustFloat_SendArray(byte, 4);
    Float_to_Byte(c, byte);
    JustFloat_SendArray(byte, 4);
    Float_to_Byte(d, byte);
    JustFloat_SendArray(byte, 4);
    JustFloat_SendArray(tail, 4);
}

/* UART RX 中断 */
void UART_0_INST_IRQHandler(void)
{
    if (DL_UART_getEnabledInterruptStatus(UART_0_INST, DL_UART_INTERRUPT_RX)
        == DL_UART_INTERRUPT_RX)
    {
        uint8_t uart_data;
        uart_data = DL_UART_receiveData(UART_0_INST);
        protocol_data_recv(&uart_data, 1);
        DL_UART_clearInterruptStatus(UART_0_INST, DL_UART_INTERRUPT_RX);
    }
}
