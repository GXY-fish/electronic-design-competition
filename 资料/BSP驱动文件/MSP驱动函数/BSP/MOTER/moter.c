#include "board.h"
#include "moter.h"
#include "ti_msp_dl_config.h"


/**************************************************************************
*  函数功能：绝对值函数
*  入口参数：int
*  返回  值：unsigned int
**************************************************************************/
static uint16_t myabs(int16_t a)
{ 		   
	int16_t temp;
	if(a<0)  temp=-a;  
	else temp=a;
	return temp;
}

void PWM_Xianfu(int max,int *PWM)
{
	if(*PWM>max)  *PWM = max;
	if(*PWM<-max) *PWM =-max;
}

/**************************************************************************
函数功能：赋值给PWM寄存器
入口参数：左轮pwm，右轮pwm
返回  值：无
**************************************************************************/
void Set_Pwm(int a,int b)
{
  uint32_t PWMA,PWMB; 
   if(b<0)  
     Zuo_1_ON,Zuo_2_OFF;
	else 
	Zuo_1_OFF,Zuo_2_ON;
     PWMA=myabs(b);
   if(a<0)   
     Yuo_1_ON,Yuo_2_OFF;
	else 
     Yuo_1_OFF,Yuo_2_ON;
     PWMB=myabs(a);	
   
      DL_TimerA_setCaptureCompareValue(PWMAB_INST, PWMA, GPIO_PWMAB_C0_IDX);
      DL_TimerA_setCaptureCompareValue(PWMAB_INST, PWMB, GPIO_PWMAB_C1_IDX);


       

   
//    DL_TimerA_setCaptureCompareValue(PWM_A0_INST, PWMD, DL_TIMER_CC_3_INDEX);//右后轮PWM,PA12


//     TA0CCR1 = PWMA; // PWM1的工作周期
//     TA0CCR2 = PWMB; // PWM2的工作周期   
//     TA0CCR3 = PWMC; // PWM3的工作周期
//     TA0CCR4 = PWMD; // PWM4的工作周期 
//         OLED_ShowSNum(16,6,PWMB,2);
//         OLED_ShowSNum(24,6,PWMC,2);
//         OLED_ShowSNum(32,6,PWMD,2);
//         OLED_ShowSNum(40,6,R2,2);
//         OLED_ShowSNum(48,6,R3,2);
}
















