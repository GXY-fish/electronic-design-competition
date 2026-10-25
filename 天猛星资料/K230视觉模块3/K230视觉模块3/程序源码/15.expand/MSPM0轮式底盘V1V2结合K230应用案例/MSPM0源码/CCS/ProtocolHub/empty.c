//K230 -> Borad     4Way Motor Board -> Borad	RGB Light -> Borad
//TXD  -> PA25                   RX2->PB6			 LED  -> PA18
//RXD  -> PA26                   TX2->PB7
#include "ti_msp_dl_config.h"
#include "delay.h"
#include "usart.h"
#include "bsp_motor_usart.h"
#include "yb_protocol.h"
#include "app_motor.h"
                    
#define MOTOR_TYPE 5   //1:520电机 2:310电机 3:测速码盘TT电机 4:TT直流减速电机 5:L型520电机
                       //1:520 motor 2:310 motor 3:speed code disc TT motor 4:TT DC reduction motor 5:L type 520 motor

//修改当前要运行的颜色案例	Modify the color case currently being run
ColorMode color_mode = 2;  //1:巡线、2:跟踪	1: Patrol, 2: Tracking

//选择是否在初始化完成后，小车自主向前走，0为否，1为是(自主避让案例使用)
//Select whether the car moves forward autonomously after initialization is completed, 0 for no, 1 for yes (used in autonomous avoidance cases)
int Car_Auto_Drive = 0;

int main(void)
{
    USART_Init();

	 //使能DMA通道，用于加快与四路电机驱动板串口的通讯  Enable DMA channel to speed up communication with the serial port of the four-way motor driver board
    NVIC_ClearPendingIRQ(UART_1_INST_INT_IRQN);
    DL_DMA_enableChannel(DMA, DMA_CH0_CHAN_ID);
    NVIC_EnableIRQ(UART_1_INST_INT_IRQN);
    
    //开启与K230串口通信的中断    Enable interrupts for communication with the K230 serial port
    NVIC_ClearPendingIRQ(UART_3_INST_INT_IRQN);
	NVIC_EnableIRQ(UART_3_INST_INT_IRQN);
    
    //设置电机类型    Set motor type
    Set_Motor(MOTOR_TYPE);

    if(Car_Auto_Drive)//K230上电初始化需要时间，等待初始化完成之后再开始前进。	It takes time for K230 to power on and initialize. Wait until the initialization is complete before moving forward.
	{
		delay_ms(1000);delay_ms(1000);delay_ms(1000);delay_ms(1000);delay_ms(1000);delay_ms(1000);delay_ms(1000);delay_ms(1000);delay_ms(1000);delay_ms(1000);
	}
    printf("init ok\r\n");
	while(1)
	{
        Pto_Loop();
        delay_ms(10);
	}
}

