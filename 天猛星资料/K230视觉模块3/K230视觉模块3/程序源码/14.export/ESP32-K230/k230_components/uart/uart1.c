#include "uart1.h"

#include "stdio.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"


#include "esp_system.h"
#include "esp_log.h"
#include "driver/uart.h"
#include "driver/gpio.h"


#include "ring_buffer.h"

#define ENABLE_DEBUG_UART1        0

static const char *TAG = "UART1";

Ring_Buffer_t uart1_ringbuf;


// 串口1接收任务
static void Uart1_Rx_Task(void *arg)
{
    ESP_LOGD(TAG, "Start Uart1_Rx_Task with core:%d", xPortGetCoreID());
    uint16_t temp_len = 255;
    uint8_t* temp_data = (uint8_t*) malloc(temp_len);
    while (1)
    {
        const int rxBytes = uart_read_bytes(UART_NUM_1, temp_data, temp_len, 1 / portTICK_PERIOD_MS);
        if (rxBytes > 0) 
        {
            #if ENABLE_DEBUG_UART1
            ESP_LOGI(TAG, "Uart1 Recv:%d, %d", rxBytes, Uart1_Available());
            for (int i = 0; i < rxBytes; i++)
            {
                RingBuffer_Push(&uart1_ringbuf, temp_data[i]);
                printf("0x%02x ", temp_data[i]);
            }
            printf("\n");
            #else
            for (int i = 0; i < rxBytes; i++)
            {
                RingBuffer_Push(&uart1_ringbuf, temp_data[i]);
            }
            #endif
        }
        vTaskDelay(pdMS_TO_TICKS(1));
    }

    free(temp_data);
    vTaskDelete(NULL);
}


// 初始化串口1
void Uart1_Init(void)
{
    const uart_config_t uart_config = {
        .baud_rate = UART1_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };

    uart_driver_install(UART_NUM_1, RX1_BUF_SIZE * 2, 0, 0, NULL, 0);
    uart_param_config(UART_NUM_1, &uart_config);
    uart_set_pin(UART_NUM_1, UART1_GPIO_TXD, UART1_GPIO_RXD, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);

    RingBuffer_Init(&uart1_ringbuf, RX1_BUF_SIZE);
    xTaskCreate(Uart1_Rx_Task, "Uart1_Rx_Task", 5*1024, NULL, 10, NULL);
}

// 发送一串数据
int Uart1_Send_Data(uint8_t* data, uint16_t len)
{
    const int txBytes = uart_write_bytes(UART_NUM_1, data, len);
    return txBytes;
}

// 发送一个字节
int Uart1_Send_Byte(uint8_t data)
{
    uint8_t data1 = data;
    const int txBytes = uart_write_bytes(UART_NUM_1, &data1, 1);
    return txBytes;
}


// 返回接收缓冲区有多少个数据
uint16_t Uart1_Available(void)
{
    return RingBuffer_Get_Used_Count(&uart1_ringbuf);
}

// 从接收缓冲区读取一个字节数据
uint8_t Uart1_Read(void)
{
    return RingBuffer_Pop(&uart1_ringbuf);
}

// 清空接收缓冲区的数据
void Uart1_Clean_Buffer(void)
{
    RingBuffer_Clean_Queue(&uart1_ringbuf);
}


