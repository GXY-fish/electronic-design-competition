#include "xunji.h"
#include "ti_msp_dl_config.h"
#include "board.h"
volatile float xun; 
 volatile float last_xun = 4.5;
// 函数找到该位是哪位
static uint16_t find_set_bit(uint32_t num) 
{
    uint8_t bit_position = 0;
    while (!(num & 1)) {
        num >>= 1;
        bit_position++;
    }
    return bit_position;
}
uint8_t my_GPIO_readPin(GPIO_Regs * 	gpio,uint32_t 	pins )	
{
	uint16_t bit_position;
	uint32_t read_32;
	bit_position=find_set_bit(pins);
	read_32=DL_GPIO_readPins(gpio,pins);
	return ((read_32>>bit_position)&1);
}
void xunji_refresh()
{    
      float z = 0;   
     uint8_t l3=0,l2=0,Z0=0,l1=0,r1=0,r2=0,r3=0;
      if(0 < my_GPIO_readPin(GPIO_XUNJI_L3_PORT, GPIO_XUNJI_L3_PIN))  {l3=1;z++;}else{l3 = 0;}
      if(0 < my_GPIO_readPin(GPIO_XUNJI_L2_PORT, GPIO_XUNJI_L2_PIN))  {l2=1;z++;}else{l2 = 0;}
      if(0 < my_GPIO_readPin(GPIO_XUNJI_L1_PORT, GPIO_XUNJI_L1_PIN))  {l1=1;z++;}else{l1 = 0;}
	  if(0 < my_GPIO_readPin(GPIO_XUNJI_Z0_PORT, GPIO_XUNJI_Z0_PIN))  {Z0=1;z++;}else{Z0 = 0;}
      if(0 < my_GPIO_readPin(GPIO_XUNJI_R1_PORT, GPIO_XUNJI_R1_PIN))  {r1=1;z++;}else{r1 = 0;}
      if(0 < my_GPIO_readPin(GPIO_XUNJI_R2_PORT, GPIO_XUNJI_R2_PIN))  {r2=1;z++;}else{r2 = 0;}
      if(0 < my_GPIO_readPin(GPIO_XUNJI_R3_PORT, GPIO_XUNJI_R3_PIN))  {r3=1;z++;}else{r3 = 0;}      
         if(z==0)z=1;      
       xun =  (l3*1 + l2*2+ l1*3 + Z0*4 + r1*5 + r2*6 + r3*7)/z ;  
         if(xun!=0){ last_xun = xun; }
         else if(xun==0){ xun = last_xun; }
}
int xunji_sign()//测黑带的，有黑带返回1
{
     uint8_t l3=0,l2=0,l1=0,Z0=0,r1=0,r2=0,r3=0;   
      if(0 < my_GPIO_readPin(GPIO_XUNJI_L3_PORT, GPIO_XUNJI_L3_PIN))  {l3=1;}else{l3 = 0;}
      if(0 < my_GPIO_readPin(GPIO_XUNJI_L2_PORT, GPIO_XUNJI_L2_PIN))  {l2=1;}else{l2 = 0;}
      if(0 < my_GPIO_readPin(GPIO_XUNJI_L1_PORT, GPIO_XUNJI_L1_PIN))  {l1=1;}else{l1 = 0;}
	  if(0 < my_GPIO_readPin(GPIO_XUNJI_Z0_PORT, GPIO_XUNJI_Z0_PIN))  {Z0=1;}else{Z0 = 0;}
      if(0 < my_GPIO_readPin(GPIO_XUNJI_R1_PORT, GPIO_XUNJI_R1_PIN))  {r1=1;}else{r1 = 0;}
      if(0 < my_GPIO_readPin(GPIO_XUNJI_R2_PORT, GPIO_XUNJI_R2_PIN))  {r2=1;}else{r2 = 0;}
      if(0 < my_GPIO_readPin(GPIO_XUNJI_R3_PORT, GPIO_XUNJI_R3_PIN))  {r3=1;}else{r3 = 0;}      
      if( ( l3 || l2 || l1 ||Z0|| r1 || r2 || r3 ) == 1)//检测到黑线，返回0
         {return 0;} 
      else if( (l3 || l2 || l1 ||Z0|| r1 || r2 || r3 ) == 0)//检测到全白，返回1
         {return 1;}
	  else
	  {return 3;}//检测无效
}

