#include "bsp_rgb.h"


#define TIMING_ONE           0xF8
#define TIMING_ZERO          0x80
#define BIT_LEN              24
#define BUFF_SIZE            (MAX_RGB * BIT_LEN + 2)


// 存储每颗灯的颜色值，范围：[0, 0xffffff].  Stores the color value of each lamp, range: [0, 0xffffff].
uint32_t led_buf[MAX_RGB] = {0};
uint8_t RGB_Byte_Buffer[BUFF_SIZE] = {0};

// GPIO初始化 GPIO Init
static void RGB_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    RCC_APB2PeriphClockCmd(Colorful_RCC, ENABLE);
    GPIO_InitStructure.GPIO_Pin = Colorful_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(Colorful_PORT, &GPIO_InitStructure);
}

// 初始化RGB灯条的DMA通道   Initialize the DMA channel for the RGB light strip
static void RGB_DMA_Init(void)
{
    DMA_InitTypeDef DMA_InitStructure;

    RCC_AHBPeriphClockCmd(RCC_AHBPeriph_DMA1, ENABLE);
    DMA_DeInit(DMA1_Channel3);
    DMA_InitStructure.DMA_PeripheralBaseAddr = (uint32_t)(&SPI1->DR);           // 外设地址： SPIx  DR   Peripheral address: SPIx DR
    DMA_InitStructure.DMA_MemoryBaseAddr = (uint32_t)RGB_Byte_Buffer;           // 待发送数据的地址 Address of data to be sent
    DMA_InitStructure.DMA_DIR = DMA_DIR_PeripheralDST;                          // 传送方向，从内存到寄存器 Transmission direction, from memory to register
    DMA_InitStructure.DMA_BufferSize = 0;                                       // 发送的数据长度，初始化可设置为0，发送时修改  Length of data to be sent, can be set to 0 for initialization, and modified when sending
    DMA_InitStructure.DMA_PeripheralInc = DMA_PeripheralInc_Disable;            // 外设地址不增加   Peripheral address does not increase
    DMA_InitStructure.DMA_MemoryInc = DMA_MemoryInc_Enable;                     // 内存地址自动增加1    Memory address automatically increases by 1
    DMA_InitStructure.DMA_PeripheralDataSize = DMA_PeripheralDataSize_Byte;     // 外设数据宽度 Peripheral data width
    DMA_InitStructure.DMA_MemoryDataSize = DMA_MemoryDataSize_Byte;             // 内存数据宽度 Memory data width
    DMA_InitStructure.DMA_Mode = DMA_Mode_Normal;                               // 发送模式，只发一次   Transmission mode, send only once
    DMA_InitStructure.DMA_Priority = DMA_Priority_High;                         // DMA传送优先级为高    DMA transmission priority is high
    DMA_InitStructure.DMA_M2M = DMA_M2M_Disable;                                // 关闭内存到内存   Disable memory to memory
    DMA_Init(DMA1_Channel3, &DMA_InitStructure);

}

// 初始化RGB灯条的SPI设备   Initialize the SPI device of the RGB light strip
static void RGB_Spi_Init(void)
{
    SPI_InitTypeDef SPIInitStructure;
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_SPI1, ENABLE);
    SPIInitStructure.SPI_Direction = SPI_Direction_1Line_Tx;
    SPIInitStructure.SPI_Mode = SPI_Mode_Master;
    SPIInitStructure.SPI_DataSize = SPI_DataSize_8b;
    SPIInitStructure.SPI_CPOL = SPI_CPOL_Low;
    SPIInitStructure.SPI_CPHA = SPI_CPHA_2Edge;
    SPIInitStructure.SPI_NSS = SPI_NSS_Soft;
    SPIInitStructure.SPI_BaudRatePrescaler = SPI_BaudRatePrescaler_8;
    SPIInitStructure.SPI_FirstBit = SPI_FirstBit_MSB;
    SPIInitStructure.SPI_CRCPolynomial = 7;
    SPI_Init(SPI1, &SPIInitStructure);
    SPI_Cmd(SPI1, ENABLE);
    SPI_I2S_DMACmd(SPI1, SPI_I2S_DMAReq_Tx, ENABLE);
}

// RGB灯条驱动初始化    RGB light strip driver initialization
static void RGB_Driver_Init(void)
{
    RGB_Spi_Init();
    RGB_DMA_Init();
}

// 初始化灯条   Initialize the light bar
void RGB_Init(void)
{
    RGB_GPIO_Init();
    RGB_Driver_Init();
}

// 更新RGB灯条  Updated RGB light bar
void RGB_Update(void)
{
    uint8_t i, j;
    for (j = 0; j < MAX_RGB; j++)
    {
        for (i = 0; i < BIT_LEN; i++)
        {
            RGB_Byte_Buffer[i + j * 24 + 1] = ((led_buf[j] >> (23 - i)) & 0x01) ? TIMING_ONE : TIMING_ZERO;
        }
    }

    DMA_SetCurrDataCounter(DMA1_Channel3, BUFF_SIZE); // 更新传输的数据量   Update the amount of data transferred
    DMA_Cmd(DMA1_Channel3, ENABLE);                   // 使能DMA通道，开始传输数据  Enable DMA channel and start transferring data
    while (!DMA_GetFlagStatus(DMA1_FLAG_TC3))         // 等待传输完成   Wait for the transfer to complete
        ;
    DMA_Cmd(DMA1_Channel3, DISABLE); // 关闭DMA通道 Close DMA channel
    DMA_ClearFlag(DMA1_FLAG_TC3);    // 清除DMA通道状态 Clear DMA channel status
}

// 设置颜色，index=[0, MAX_RGB]控制对应灯珠颜色, index=0xFF控制所有灯珠颜色。
//  Set the color, index=[0, MAX_RGB] to control the corresponding lamp bead color, index=0xFF to control all lamp bead color.
void RGB_Set_Color(uint8_t index, uint8_t r, uint8_t g, uint8_t b)
{
    uint32_t color = g << 16 | r << 8 | b;
    if (index < MAX_RGB)
    {
        led_buf[index] = color;
        return;
    }
    if (index == RGB_CTRL_ALL)
    {
        for (uint8_t i = 0; i < MAX_RGB; i++)
        {
            led_buf[i] = color;
        }
    }
}

// 设置RGB灯条颜色值，index=[0, 16]控制对应灯珠颜色, index=255控制所有灯珠颜色。color=0xggrrbb
//  Sets the color value of the RGB light bar, index=[0, 16] controls the corresponding light bead color, index=255 controls all light bead colors. color=0xggrrbb
void RGB_Set_Color_U32(uint8_t index, uint32_t color)
{
    if (index < MAX_RGB)
    {
        led_buf[index] = color;
        return;
    }
    if (index == RGB_CTRL_ALL)
    {
        for (uint8_t i = 0; i < MAX_RGB; i++)
        {
            led_buf[i] = color;
        }
    }
}

// 清除颜色（熄灭） Clear color (off)
void RGB_Clear(void)
{
    for (uint8_t i = 0; i < MAX_RGB; i++)
    {
        led_buf[i] = 0x0;
    }
}
