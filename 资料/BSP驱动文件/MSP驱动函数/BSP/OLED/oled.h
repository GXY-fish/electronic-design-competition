#ifndef __OLED_H
#define __OLED_H 
#include "ti_msp_dl_config.h" // ����ļ�������� GPIO �ĺ��������Ͷ���
#include "board.h"
#include "stdlib.h"	
#include <stdint.h>

#define u8 uint8_t
#define u16 uint16_t
#define u32 uint32_t


#define OLED_ADDR 0x3C
#define OLED_MODE 0
#define SIZE 8
#define XLevelL		0x00
#define XLevelH		0x10
#define Max_Column	128
#define Max_Row		64
#define	Brightness	0xFF 
#define X_WIDTH 	128
#define Y_WIDTH 	64	  

//-----------------OLED�˿ڶ���----------------

#define OLED_SCL_Clr() DL_GPIO_clearPins(OLED_PORT,OLED_SCL_PIN)//SCL
#define OLED_SCL_Set() DL_GPIO_setPins(OLED_PORT,OLED_SCL_PIN)

#define OLED_SDA_Clr() DL_GPIO_clearPins(OLED_PORT,OLED_SDA_PIN)//DIN
#define OLED_SDA_Set() DL_GPIO_setPins(OLED_PORT,OLED_SDA_PIN)

//#define OLED_RES_Clr() GPIO_ResetBits(GPIOA,GPIO_Pin_2)//RES
//#define OLED_RES_Set() GPIO_SetBits(GPIOA,GPIO_Pin_2)

#define OLED_CMD  0	//д����
#define OLED_DATA 1	//д����

void OLED_ClearPoint(u8 x,u8 y);
void OLED_ColorTurn(u8 i);
void OLED_DisplayTurn(u8 i);
void I2C_Start(void);
void I2C_Stop(void);
void I2C_WaitAck(void);
void Send_Byte(u8 dat);
void OLED_WR_Byte(u8 dat,u8 mode);
void OLED_DisPlay_On(void);
void OLED_DisPlay_Off(void);
void OLED_Refresh(void);
void OLED_Clear(void);
void OLED_DrawPoint(u8 x,u8 y,u8 t);
void OLED_DrawLine(u8 x1,u8 y1,u8 x2,u8 y2,u8 mode);
void OLED_DrawCircle(u8 x,u8 y,u8 r);
void OLED_ShowChar(u8 x,u8 y,u8 chr,u8 size1,u8 mode);
void OLED_ShowChar6x8(u8 x,u8 y,u8 chr,u8 mode);
void OLED_ShowString(u8 x,u8 y,u8 *chr,u8 size1,u8 mode);
void OLED_ShowNum(u8 x,u8 y,u32 num,u8 len,u8 size1,u8 mode);
void OLED_ShowChinese(u8 x,u8 y,u8 num,u8 size1,u8 mode);
void OLED_ScrollDisplay(u8 num,u8 space,u8 mode);
void OLED_ShowPicture(u8 x,u8 y,u8 sizex,u8 sizey,u8 BMP[],u8 mode);
void OLED_ShowAngle(int roll,int yaw);
void OLED_Shownum3(unsigned char x, unsigned char y, unsigned int num);
void OLED_ShowNum_nb_1(u8 x,u8 y,int num1,u8 size1,u8 mode);
void OLED_ShowNum_nb_3(u8 x,u8 y,int num1,int num2,int num3,u8 size1,u8 mode);
void OLED_ShowNum_nb_2(u8 x,u8 y,float num1,int num2,u8 size1,u8 mode);
   void OLED_ShowNum_nb(u8 x,u8 y,int num1,int num2,int num3,u8 size1,u8 mode);
void OLED_Init(void);

//    delay_ms(500);    
//    OLED_Init();
//    OLED_DisPlay_On();
//    OLED_Clear();
//		OLED_ShowString(12,0,(uint8_t *)"1.mode1",16,1);
//		OLED_ShowString(12,16,(uint8_t *)"2.mode2",16,1);
//		OLED_ShowString(12,32,(uint8_t *)"3.mode3",16,1);
//		OLED_ShowString(12,48,(uint8_t *)"4.mode4",16,1);
//		OLED_Refresh();

#endif

