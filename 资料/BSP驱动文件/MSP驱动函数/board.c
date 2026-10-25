#include "board.h"
#include <stdint.h>
//__IO 本质上就是 C 语言中的 volatile 关键字，它是一个宏定义，作用是禁止编译器对该变量进行优化，确保每次读写都直接访问内存地址

//编码器函数需要的变量
__IO uint32_t uwTick = 0;
__IO uint32_t speed_Tick = 0;
__IO uint32_t oled_Tick = 0;
int filt_velocity_r = 0;     //滤波后的速度
int last_filt_velocitya_r = 0;
int filt_velocity_l = 0;     //滤波后的速度
int last_filt_velocitya_l = 0;
int filt_velocity_pingjun = 0; //滤波后的平均速度
extern int _encoder_l_count;
extern int _encoder_r_count;

//串口陀螺仪需要的变量
volatile unsigned char uart_data = 0;
extern volatile uint8_t gyro_rx_done;
extern volatile int16_t gyro_angle_raw;
extern volatile int16_t gyro_dps_raw;


void board_init(void)
{
	// SYSCFG初始化
	SYSCFG_DL_init();
//	//清除串口中断标志
//	NVIC_ClearPendingIRQ(UART_0_INST_INT_IRQN);
//	//使能串口中断
//	NVIC_EnableIRQ(UART_0_INST_INT_IRQN);
	
	printf("Board Init [[ ** LCKFB ** ]]\r\n");
}

//外部中断在encoder.c文件的最下面
////外部中断  dmp相关内容
//void GROUP1_IRQHandler(void)//Group1的中断服务函数
//{
//	
//}

//滴答定时器中断服务函数
void SysTick_Handler(void)
{
   float a=0.3;  
    uwTick++;
   
   if(uwTick - speed_Tick>5){//10ms更新一次速度
      speed_Tick = uwTick;
//	   oled_Tick++;      
//      velocity_r = _encoder_r_count;
//      velocity_l = _encoder_l_count;      
      filt_velocity_l = a*_encoder_l_count + (1-a)*last_filt_velocitya_l;//简单算法滤波，此次速度取30%的权重，过往速度取70%的权重，让速度更平滑
      last_filt_velocitya_l = filt_velocity_l; //此次速度记录为“上次速度”
      
      filt_velocity_r = a*_encoder_r_count + (1-a)*last_filt_velocitya_r;//简单算法滤波，此次速度取30%的权重，过往速度取70%的权重，让速度更平滑
      last_filt_velocitya_r = filt_velocity_r; //此次速度记录为“上次速度”
      
   
      filt_velocity_pingjun += (filt_velocity_l+filt_velocity_r)/2;
      
      _encoder_l_count = 0;
      _encoder_r_count = 0;   
   }
}

void UART_1_INST_IRQHandler(void)
{
    switch( DL_UART_getPendingInterrupt(UART_1_INST) )
    {
        case DL_UART_IIDX_RX:
                uart_data = DL_UART_Main_receiveData(UART_1_INST);
								Gyro_ParseFrame(uart_data);
     //           Modbus_ParseFrame(uart_data);
            break;

        default:
            break;
    }
}

//返回SysTick计数值
//搭配滴答定时器实现的精确us延时
void delay_us(unsigned long __us) 
{
    uint32_t ticks;
    uint32_t told, tnow, tcnt = 38;

    // 计算需要的时钟数 = 延迟微秒数 * 每微秒的时钟数
    ticks = __us * (32000000 / 1000000);

    // 获取当前的SysTick值
    told = SysTick->VAL;

    while (1)
    {
        // 重复刷新获取当前的SysTick值
        tnow = SysTick->VAL;

        if (tnow != told)
        {
            if (tnow < told)
                tcnt += told - tnow;
            else
                tcnt += SysTick->LOAD - tnow + told;

            told = tnow;

            // 如果达到了需要的时钟数，就退出循环
            if (tcnt >= ticks)
                break;
        }
    }
}

//搭配滴答定时器实现的精确ms延时
void delay_ms(unsigned long ms) 
{
	// 使用独立循环而非 delay_us * 1000，避免 SysTick 中断影响
	// 32MHz, 每个循环约 5 周期，32M/5 ≈ 6400000 loops/ms
	volatile uint32_t loops = ms * 6400;
	while (loops--) {
		__NOP();
	}
}

void delay_1us(unsigned long __us){ delay_us(__us); }
void delay_1ms(unsigned long ms){ delay_ms(ms); }


// ========== ARM Compiler 6 标准库 printf 重定向 ==========
// ARM Compiler 6 (armclang) 不使用 fputc()，而是使用 _write()
int _write(int fd, char *buf, int len)
{
    for (int i = 0; i < len; i++)
    {
        while (DL_UART_isBusy(UART_0_INST) == true);
        DL_UART_Main_transmitDataBlocking(UART_0_INST, buf[i]);
    }
    return len;
}

// 避免链接器报告 semihosting 相关错误
int _read(int fd, char *buf, int len)
{
    return 0;
}

void _ttywrch(int ch)
{
    while (DL_UART_isBusy(UART_0_INST) == true);
    DL_UART_Main_transmitDataBlocking(UART_0_INST, ch);
}

// ARM Compiler 5 (armcc) 的 printf 重定向（保留兼容）
int fputc(int ch, FILE *stream)
{
	while( DL_UART_isBusy(UART_0_INST) == true );
	DL_UART_Main_transmitDataBlocking(UART_0_INST, ch);
	return ch;
}

int fputs(const char* restrict s,FILE* restrict stream)
{
   uint16_t i,len;
   len = strlen(s);
   for(i=0;i<len;i++)
   {
        while( DL_UART_isBusy(UART_0_INST) == true ){}
       DL_UART_Main_transmitDataBlocking(UART_0_INST,s[i]);
   }
   return len;
}

int puts(const char *_ptr)
{
    int count = fputs(_ptr,stdout);
    count += fputs("\n",stdout);
    return count;
}
