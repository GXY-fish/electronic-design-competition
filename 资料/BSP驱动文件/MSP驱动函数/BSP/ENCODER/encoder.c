#include "encoder.h"
#include "board.h"
#include <stdio.h>
#include "ti_msp_dl_config.h"

// 定义了两个编码器的计数器，用于计算编码器的旋转圈数
 volatile int _encoder_l_count = 0, _encoder_r_count = 0;
 int i=0;
static void encoder_function(void)
{
 //处理左编码器A相中断,A相上升沿
   //DL_GPIO_getEnabledInterruptStatus(ENCODER_PORT, ENCODER_Left_A_PIN)
    volatile unsigned int interruptMask = ENCODER_PORT->CPU_INT.MIS;
    volatile unsigned int state = ENCODER_PORT->DIN31_0;
    volatile unsigned int clearMask = ENCODER_PORT->DIN31_0;
    if( interruptMask &  ENCODER_Left_A_PIN ){
       _encoder_l_count += (state&ENCODER_Left_B_PIN)?-1:1;
       clearMask |= ENCODER_Left_A_PIN;
    }
      
    if( interruptMask &  ENCODER_Right_A_PIN ){
       _encoder_r_count += (state&ENCODER_Right_B_PIN)?-1:1;
       clearMask |= ENCODER_Right_A_PIN;
    }    
    
    ENCODER_PORT->CPU_INT.ICLR |= clearMask;
}



void encoder_function2(void)
{
 //处理左编码器A相中断,A相上升沿
    if (DL_GPIO_getEnabledInterruptStatus(ENCODER_PORT, ENCODER_Left_A_PIN))
    {
         if(DL_GPIO_readPins(ENCODER_PORT,ENCODER_Left_B_PIN)==0)  //B逻辑低
         {
               
              _encoder_l_count++; //计数增
         }
         else                                                                       //B逻辑高
         {
               _encoder_l_count--; //计数减
         }
        // 清除A相的中断状态
        DL_GPIO_clearInterruptStatus(ENCODER_PORT, ENCODER_Left_A_PIN);
    }  

//处理左编码器B相中断,B相下降沿
    if (DL_GPIO_getEnabledInterruptStatus(ENCODER_PORT, ENCODER_Left_B_PIN))
    {
         if(DL_GPIO_readPins(ENCODER_PORT,ENCODER_Left_A_PIN)==0)  //A逻辑低
         {
               
              _encoder_l_count++; //计数增
         }
         else                                                                     
         {
               _encoder_l_count--; //计数减
         }
        // 清除B相的中断状态
        DL_GPIO_clearInterruptStatus(ENCODER_PORT, ENCODER_Left_B_PIN);
    }
    
    
   
     //处理右编码器A相中断,A相上升沿
    if (DL_GPIO_getEnabledInterruptStatus(ENCODER_PORT, ENCODER_Right_A_PIN))
    {
         if(DL_GPIO_readPins(ENCODER_PORT,ENCODER_Right_B_PIN)==0)  //B逻辑低
         {
               
              _encoder_r_count--; //计数增
         }
         else                                                                       //B逻辑高
         {
               _encoder_r_count++; //计数减
         }
        // 清除A相的中断状态
        DL_GPIO_clearInterruptStatus(ENCODER_PORT, ENCODER_Right_A_PIN);
    }  

//处理右编码器B相中断,B相下降沿
    if (DL_GPIO_getEnabledInterruptStatus(ENCODER_PORT, ENCODER_Right_B_PIN))
    {
         if(DL_GPIO_readPins(ENCODER_PORT,ENCODER_Right_A_PIN)==0)  //A逻辑低
         {
               
              _encoder_r_count--; //计数增
         }
         else                                                                     
         {
               _encoder_r_count++; //计数减
         }
        // 清除B相的中断状态
        DL_GPIO_clearInterruptStatus(ENCODER_PORT, ENCODER_Right_B_PIN);
    }
}

void GROUP1_IRQHandler(void)
{
  
     
    // 确定中断源并进行相应的处理
    switch (DL_Interrupt_getPendingGroup(DL_INTERRUPT_GROUP_1))
    {
    case DL_INTERRUPT_GROUP1_IIDX_GPIOB: // 当中断源为编码器中断时
    {
        // 调用编码器中断处理函数
        encoder_function2();
    }
    break;
        break;
    }
}