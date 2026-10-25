#include "bsp_K230_usart.h"

/*  串口中断接收处理 */
/* Serial port interrupt reception processing */
void UART_3_INST_IRQHandler(void)
{
	uint8_t Rx2_Temp = 0;
	
	switch( DL_UART_getPendingInterrupt(UART_3_INST) )
	{
		case DL_UART_IIDX_RX://如果是接收中断	If it is a receive interrupt
			// 接收发送过来的数据保存	Receive and save the data sent
			Rx2_Temp = DL_UART_Main_receiveData(UART_3_INST);
//        printf("%X",Rx2_Temp);
            Pto_Data_Receive(Rx2_Temp);//处理数据   Processing Data
			// 每次接收到数据时重置计数器	Reset the counter each time data is received
			lost_count = 50;
			break;

		default://其他的串口中断	Other serial port interrupts
			break;
	}	
    

}
