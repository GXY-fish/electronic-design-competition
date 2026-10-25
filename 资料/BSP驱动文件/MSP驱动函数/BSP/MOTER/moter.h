#ifndef __MOTER_H__
#define __MOTER_H__


#define Zuo_1_ON   DL_GPIO_setPins(TB6612_PORT,TB6612_ZUO_IN1_PIN) 
#define Zuo_1_OFF  DL_GPIO_clearPins(TB6612_PORT, TB6612_ZUO_IN1_PIN)
#define Zuo_2_ON   DL_GPIO_setPins(TB6612_PORT,TB6612_ZUO_IN2_PIN)
#define Zuo_2_OFF  DL_GPIO_clearPins(TB6612_PORT, TB6612_ZUO_IN2_PIN)

#define Yuo_1_ON   DL_GPIO_setPins(TB6612_PORT,TB6612_YOU_IN1_PIN) 
#define Yuo_1_OFF  DL_GPIO_clearPins(TB6612_PORT, TB6612_YOU_IN1_PIN)
#define Yuo_2_ON   DL_GPIO_setPins(TB6612_PORT,TB6612_YOU_IN2_PIN)
#define Yuo_2_OFF  DL_GPIO_clearPins(TB6612_PORT, TB6612_YOU_IN2_PIN)

#define Zuo_Stop   Zuo_1_OFF;Zuo_2_OFF
#define Yuo_Stop   Yuo_1_OFF;Yuo_2_OFF

void Set_Pwm(int a,int b);

#endif