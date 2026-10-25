/**
* @par Copyright (C): 2010-2019, Shenzhen Yahboom Tech
* @file         bsp.c      
* @version      V1.0     
* @brief        驱动总入口
* @details      
* @par History  见如下说明
*                 
* version:	
*/


#include "AllHeader.h"
#include "pid.h"

/**
* Function       bsp_init  
* @brief         硬件设备初始化
* @param[in]     void
* @param[out]    void
* @retval        void
* @par History   无
*/
void bsp_init(void)
{
	SystemInit();
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2); 
	
	delay_init();


	USART1_init(115200);

	USART3_Init(115200);

		TIM1_Int_Init(4089,72);
		pid_timer_init();
		Servo_GPIO_Init();
		init_beep();

		Key_GPIO_Init();//按键初始化
	
	
#if	Battery_SW
	Adc_vol_init();  //检测电压
	J_Adc_init();//检测电流
#endif	

	
#if	PS_TWO
	PS2_Init();		//======ps2驱动端口初始化
	PS2_SetInit();	//======ps2配置初始化,配置“红绿灯模式”，并选择是否可以修改
	delay_ms(1000);
#endif
	
#if OLED_SW
	IIC_Init();
	i2c_scanf_addr();
	SSD1306_Init();
//		OLED_Draw_Line("OLED init sucess", 1 , false, true);
//	OLED_Draw_Line("Servo angle:90 ", 1 , false, true);
//	OLED_Draw_Line("current:0.03  A", 2 , false, true);
//	OLED_Draw_Line("Battery vol: 7.2 V", 3 , false, true);
	

#endif

	

}
