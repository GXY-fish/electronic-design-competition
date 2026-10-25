#include "bsp_rgb.h"

#define TIMING_ONE           0xF8
#define TIMING_ZERO          0x80
#define BIT_LEN              24
#define BUFF_SIZE            (MAX_RGB * BIT_LEN + 2)


// 存储每颗灯的颜色值，范围：[0, 0xffffff].  Stores the color value of each lamp, range: [0, 0xffffff].
uint32_t led_buf[MAX_RGB] = {0};
uint8_t RGB_Byte_Buffer[BUFF_SIZE] = {0};


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
    
     for (uint16_t k = 0; k < BUFF_SIZE; k++) {
        DL_SPI_transmitData8(SPI_0_INST, RGB_Byte_Buffer[k]);
        while (DL_SPI_isBusy(SPI_0_INST));
    }
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
