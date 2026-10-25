#ifndef __BSP_RGB_H__
#define __BSP_RGB_H__

#include "AllHeader.h"

#define RGB_CTRL_ALL    0xFF
#define MAX_RGB         14

#define Colorful_PORT   GPIOA
#define Colorful_PIN    GPIO_Pin_7
#define Colorful_RCC    RCC_APB2Periph_GPIOA


void RGB_Init(void);
void RGB_Update(void);

void RGB_Set_Color(uint8_t index, uint8_t r, uint8_t g, uint8_t b);
void RGB_Set_Color_U32(uint8_t index, uint32_t color);
void RGB_Clear(void);

#endif /* __BSP_RGB_H__ */
