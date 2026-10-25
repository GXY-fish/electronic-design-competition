#include "ti_msp_dl_config.h"
#include "delay.h"
#include "usart.h"
#include "app_motor_usart.h"

#define UPLOAD_DATA 3  //0:不接受数据 1:接收总的编码器数据 2:接收实时的编码器 3:接收电机当前速度 mm/s
                       //0: Do not receive data 1: Receive total encoder data 2: Receive real-time encoder 3: Receive current motor speed mm/s

#define MOTOR_TYPE 1   //1:520电机 2:310电机 3:测速码盘TT电机 4:TT直流减速电机 5:L型520电机
                       //1:520 motor 2:310 motor 3:speed code disc TT motor 4:TT DC reduction motor 5:L type 520 motor

// 屏幕中心点坐标
#define SCREEN_CENTER 320

uint8_t times = 0;

// 定义串口接收缓冲区和相关变量
#define RX_BUFFER_SIZE 50
char rx_buffer[RX_BUFFER_SIZE];
uint8_t rx_index = 0;
uint8_t rx_complete = 0;

// 接收到的PID输出
int left_speed = 0;
int right_speed = 0;

void Car_Move(void)
{
    // 根据接收到的速度控制小车
    #if MOTOR_TYPE == 4
    Contrl_Pwm(left_speed * 5, left_speed * 5, right_speed * 5, right_speed * 5);
    #else
    Contrl_Speed(left_speed, left_speed, right_speed, right_speed);
    #endif
}

void Car_Move_PWM(void)
{
    // 根据接收到的速度控制小车
    #if MOTOR_TYPE == 4
    Contrl_Pwm(left_speed * 5, left_speed * 5, right_speed * 5, right_speed * 5);
    #else
    Contrl_Speed(left_speed, left_speed, right_speed, right_speed);
    #endif
}

// 前进函数
void Car_Forward(void)
{
    #if MOTOR_TYPE == 4
    Contrl_Pwm(1500,1500,1500,1500);
    #else
    Contrl_Speed(300,300,300,300);
    #endif
}

// 后退函数
void Car_Backward(void)
{
    #if MOTOR_TYPE == 4
    Contrl_Pwm(-1500,-1500,-1500,-1500);
    #else
    Contrl_Speed(-300,-300,-300,-300);
    #endif
}

// 停车函数
void Car_Stop(void)
{
    #if MOTOR_TYPE == 4
    Contrl_Pwm(0,0,0,0);
    #else
    Contrl_Speed(0,0,0,0);
    #endif
}

// 解析串口命令
void Parse_Command(void)
{
    if (rx_complete) {
        rx_buffer[rx_index] = '\0'; // 添加字符串结束符
        
        // 检查是否是PID输出数据格式 $left,right#
        if (rx_buffer[0] == '$' && strchr(rx_buffer, '#') != NULL) {
            char *start = rx_buffer + 1;  // 跳过 '$'
            char *end = strchr(rx_buffer, '#');
            *end = '\0';  // 将 '#' 替换为字符串结束符
            
            // 解析两个数值
            char *token = strtok(start, ",");
            if (token != NULL) {
                left_speed = atoi(token);
                token = strtok(NULL, ",");
                if (token != NULL) {
                    right_speed = atoi(token);
                    
                    printf("Received PID output: left=%d, right=%d\r\n", left_speed, right_speed);
                } else {
                    printf("Invalid PID output data format\r\n");
                }
            } else {
                printf("Invalid PID output data format\r\n");
            }
        }
        // 重置接收缓冲区
        rx_index = 0;
        rx_complete = 0;
    }
}

int main(void)
{	
    USART_Init();
    
    printf("please wait...\r\n");
    Contrl_Pwm(0,0,0,0);
    delay_ms(100);
    //先关闭上报	Close the report first
    send_upload_data(false,false,false);
    delay_ms(10);
    
    // 配置电机相关参数
    // ...
    
    //给电机模块发送需要上报的数据	Send the data that needs to be reported to the motor module
    #if UPLOAD_DATA == 1
    send_upload_data(true,false,false);delay_ms(10);
    #elif UPLOAD_DATA == 2
    send_upload_data(false,true,false);delay_ms(10);
    #elif UPLOAD_DATA == 3
    send_upload_data(false,false,true);delay_ms(10);
    #endif
    
    //清除定时器中断标志	Clear the timer interrupt flag
    NVIC_ClearPendingIRQ(TIMER_0_INST_INT_IRQN);
    //使能定时器中断	Enable timer interrupt
    NVIC_EnableIRQ(TIMER_0_INST_INT_IRQN);

    SYSCFG_DL_init(); 
    //清除串口中断标志 Clear the serial port interrupt flag
    NVIC_ClearPendingIRQ(UART_3_INST_INT_IRQN);
    //使能串口中断 Enable serial port interrupt
    NVIC_EnableIRQ(UART_3_INST_INT_IRQN);
    
    printf("System ready, waiting for PID output data...\r\n");
    printf("Format: $left,right#\r\n");
    
    while(1)
    {
        // 解析串口数据并控制小车
        Parse_Command();
        Car_Move();
        
        // 降低控制频率
        delay_ms(50);
        
        if(g_recv_flag == 1)
        {
            g_recv_flag = 0;
            
            #if UPLOAD_DATA == 1
                Deal_data_real();
                printf("M1:%d,M2:%d,M3:%d,M4:%d\r\n",Encoder_Now[0],Encoder_Now[1],Encoder_Now[2],Encoder_Now[3]);
            #elif UPLOAD_DATA == 2
                Deal_data_real();
                printf("M1:%d,M2:%d,M3:%d,M4:%d\r\n",Encoder_Offset[0],Encoder_Offset[1],Encoder_Offset[2],Encoder_Offset[3]);
            #elif UPLOAD_DATA == 3
                Deal_data_real();
                printf("M1:%.2f,M2:%.2f,M3:%.2f,M4:%.2f\r\n",g_Speed[0],g_Speed[1],g_Speed[2],g_Speed[3]);
            #endif
        }
    }
}

//定时器的中断服务函数,每100ms读取数据并打印
//The timer interrupt service function reads and prints data every 100ms
void TIMER_0_INST_IRQHandler(void)
{
    //如果产生了定时器中断	If a timer interrupt occurs
    switch( DL_TimerG_getPendingInterrupt(TIMER_0_INST) )
    {
        case DL_TIMER_IIDX_ZERO://如果是0溢出中断	If it is 0 overflow interrupt
            times++;
            break;

        default:
            break;
    }
}

//串口的中断服务函数 Serial port interrupt service function
void UART_3_INST_IRQHandler(void)
{
    //如果产生了串口中断 If a serial port interrupt occurs
    switch( DL_UART_getPendingInterrupt(UART_3_INST) )
    {
        case DL_UART_IIDX_RX: //如果是接收中断 If it is a receive interrupt
            //接收数据 Receive data
            char rx_data = DL_UART_Main_receiveData(UART_3_INST);
            
            // 将接收到的数据存入缓冲区
            if (rx_index < RX_BUFFER_SIZE - 1) {
                rx_buffer[rx_index++] = rx_data;
                
                // 检查是否接收到'#'结束符
                if (rx_data == '#') {
                    rx_complete = 1;  // 标记接收完成
                }
            } else {
                // 缓冲区溢出,重置
                rx_index = 0;
            }

            // 回显接收的字符(可选)
            while( DL_UART_isBusy(UART_3_INST) == true );
            DL_UART_Main_transmitData(UART_3_INST, rx_data);

            break;
        default://其他的串口中断 Other serial port interrupts
            break;
    }
}