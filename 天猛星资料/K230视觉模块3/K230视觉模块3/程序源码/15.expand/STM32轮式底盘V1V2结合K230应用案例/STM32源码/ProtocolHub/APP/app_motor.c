#include "app_motor.h"
#include <string.h>

#define DEBUG 0
#if DEBUG
    #define DEBUG_PRINT(fmt, ...) printf(fmt, ##__VA_ARGS__)
#else
    #define DEBUG_PRINT(fmt, ...) // 定义为空，编译器会优化掉   Define it as empty, the compiler will optimize it away
#endif

#define KP (12)
#define KI (0) 
#define KD (0.1) 

int pid_output,pid_output1 = 0;
int PWM_Car_Flag = 0;//使用无编码器电机的标志位 Flag for using encoderless motor
int Wait_Flag = 0;//等待识别稳定的标志位    Waiting for identification of stable flag
int SetTarget_Flag = 0;//记录追踪目标的面积的标志位 A flag that records the area of ??the tracking target
int target_area = 0;//目标面积  Target area

static float speed_lr = 0;
static float speed_fb = 0;
static float speed_spin = 0;
static int speed_L1_setup = 0;
static int speed_L2_setup = 0;
static int speed_R1_setup = 0;
static int speed_R2_setup = 0;

float PID_Calc(float actual_value)
{
	float output = 0;
	float error = actual_value;
	static float error_last;
	static float Integral;//积分  Integral
	
	Integral +=error;
	
	//位置式pid    Positional pid
	output=error*KP + KI*Integral + (error - error_last)*KD;
    
    error_last = error;
    
	return output;
}


// 返回当前小车轮子轴间距和的一半  Returns half of the current sum of the wheel axle distances
static float Motion_Get_APB(void)
{
    return Car_APB;
}

void Set_Motor(int MOTOR_TYPE)
{
    if(MOTOR_TYPE == 1)
    {
        Set_motor_type(1);//配置电机类型	Configure motor type
        delay_ms(100);
        Set_Pluse_Phase(30);//配置减速比 查电机手册得出	Configure the reduction ratio. Check the motor manual to find out
        delay_ms(100);
        Set_Pluse_line(11);//配置磁环线 查电机手册得出	Configure the magnetic ring wire. Check the motor manual to get the result.
        delay_ms(100);
        Set_Wheel_dis(67.00);//配置轮子直径,测量得出		Configure the wheel diameter and measure it
        delay_ms(100);
        Set_motor_deadzone(1900);//配置电机死区,实验得出	Configure the motor dead zone, and the experiment shows
        delay_ms(100);
    }
    
    else if(MOTOR_TYPE == 2)
    {
        Set_motor_type(2);
        delay_ms(100);
        Set_Pluse_Phase(20);
        delay_ms(100);
        Set_Pluse_line(13);
        delay_ms(100);
        Set_Wheel_dis(48.00);
        delay_ms(100);
        Set_motor_deadzone(1600);
        delay_ms(100);
    }
    
    else if(MOTOR_TYPE == 3)
    {
        Set_motor_type(3);
        delay_ms(100);
        Set_Pluse_Phase(45);
        delay_ms(100);
        Set_Pluse_line(13);
        delay_ms(100);
        Set_Wheel_dis(68.00);
        delay_ms(100);
        Set_motor_deadzone(1250);
        delay_ms(100);
    }
    
    else if(MOTOR_TYPE == 4)
    {
        Set_motor_type(4);
        delay_ms(100);
        Set_Pluse_Phase(48);
        delay_ms(100);
        Set_motor_deadzone(1000);
        delay_ms(100);
        PWM_Car_Flag = 1;
    }
    
    else if(MOTOR_TYPE == 5)
    {
        Set_motor_type(1);
        delay_ms(100);
        Set_Pluse_Phase(40);
        delay_ms(100);
        Set_Pluse_line(11);
        delay_ms(100);
        Set_Wheel_dis(67.00);
        delay_ms(100);
        Set_motor_deadzone(1900);
        delay_ms(100);
    }
}

//控制小车运行，输入的参数分别为x、y、z三个轴上的速度值
//Control the movement of the car. The input parameters are the speed values ??on the x, y, and z axes.
void Motion_Car_Control(int16_t V_x, int16_t V_y, int16_t V_z)
{
	float robot_APB = Motion_Get_APB();
	speed_lr = 0;
    speed_fb = V_x;
    speed_spin = (V_z / 1000.0f) * robot_APB;
    if (V_x == 0 && V_y == 0 && V_z == 0)
    {
        control_pwm(0,0,0,0);
        return;
    }

    speed_L1_setup = speed_fb - speed_spin;
    speed_L2_setup = speed_fb - speed_spin;
    speed_R1_setup = speed_fb  + speed_spin;
    speed_R2_setup = speed_fb  + speed_spin;
		
    if (speed_L1_setup > 1000) speed_L1_setup = 1000;
    if (speed_L1_setup < -1000) speed_L1_setup = -1000;
    if (speed_L2_setup > 1000) speed_L2_setup = 1000;
    if (speed_L2_setup < -1000) speed_L2_setup = -1000;
    if (speed_R1_setup > 1000) speed_R1_setup = 1000;
    if (speed_R1_setup < -1000) speed_R1_setup = -1000;
    if (speed_R2_setup > 1000) speed_R2_setup = 1000;
    if (speed_R2_setup < -1000) speed_R2_setup = -1000;
    
    //DEBUG_PRINT("L1:%d, L2:%d, L3:%d, L4:%d\r\n",speed_L1_setup,speed_L2_setup,speed_R1_setup,speed_R2_setup);
    //DEBUG_PRINT("\r\n");
    if(PWM_Car_Flag)//如果小车是无编码器类型的，就直接控制pwm，否则控制速度 If the car is encoderless, it controls PWM directly, otherwise it controls the speed
    {
        control_pwm(speed_L1_setup, speed_L2_setup, speed_R1_setup, speed_R2_setup);
    }
    else
    {
        control_speed(speed_L1_setup, speed_L2_setup, speed_R1_setup, speed_R2_setup);
    }
}


void Visual_Line_Track(int x)
{
    if(!Wait_Flag)
    {
        delay_ms(1000);delay_ms(1000);delay_ms(1000);//delay 3s
        Wait_Flag = 1;
        return;
    }
    
    int16_t err = 300 - (x + w/2);//获取x轴上的差值 Get the difference on the x-axis
    DEBUG_PRINT("x:%d, CENTER:%d\r\n", x, 300);
    DEBUG_PRINT("err:%d\r\n", err);
    if(err<5 && err>-5)err=0;
    
    pid_output = PID_Calc(err);//计算差值的PID  PID to calculate the difference
    DEBUG_PRINT("pid_output:%d\r\n", pid_output);
    
    Motion_Car_Control(300, 0, pid_output);
}

void Color_Trace(int x,int w,int h)
{
    if(!Wait_Flag)
    {
        delay_ms(1000);delay_ms(1000);delay_ms(1000);//delay 3s
        Wait_Flag = 1;
        return;
    }
    
    if(Wait_Flag && !SetTarget_Flag)
    {
        SetTarget_Flag = 1;
        target_area = w*h/100;
    }

    int now_area = w*h/100;
    
    int16_t err = 280 - x;
    DEBUG_PRINT("x:%d, CENTER:%d\r\n", x, 280);
    DEBUG_PRINT("err:%d\r\n", err);
    
    pid_output = PID_Calc(err);
    DEBUG_PRINT("pid_output:%d\r\n", pid_output);
    if(pid_output>500) pid_output=500;//对pid输出值进行限幅，防止小车跑过头   Limit the pid output value to prevent the car from running too far
    if(pid_output<-500) pid_output=-500;
    
    DEBUG_PRINT("\r\n");
    
    int16_t err_area = target_area - now_area;//计算要追踪的面积差值    Calculate the difference in area to be tracked
    DEBUG_PRINT("now_area:%d, target_area:%d\r\n", now_area, target_area);
    DEBUG_PRINT("err_area:%d\r\n", err_area);
    
    if(err_area<10 && err_area>-10)err_area=0;//设置要追踪的面积限幅，减少因为微弱变化而引起小车频繁的抖动  Set the area limit to be tracked to reduce the frequent shaking of the car caused by slight changes
    pid_output1 = PID_Calc(err_area);
    DEBUG_PRINT("pid_output1:%d\r\n", pid_output1);
    if(pid_output1>200) pid_output1=200;//对pid输出值进行限幅，防止小车跑过头   Limit the pid output value to prevent the car from running too far
    if(pid_output1<-200) pid_output1=-200;
    
    DEBUG_PRINT("\r\n");
        
    Motion_Car_Control(pid_output1, 0, pid_output);
}

void QRCode_Action(const char* msg)
{
    if(strcmp(msg,"FORWARD")==0 || strcmp(msg,"forward")==0)//如果识别到的内容为forward或者FORWARD  If the recognized content is forward or FORWARD
    {
        DEBUG_PRINT("FORWARD!\r\n");
        Motion_Car_Control(200,0,0);//前进两秒后停下    Go forward for two seconds and then stop
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else if(strcmp(msg,"BACKWARD")==0 || strcmp(msg,"backward")==0)
    {
        DEBUG_PRINT("BACKWARD!\r\n");
        Motion_Car_Control(-200,0,0);
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else if (strcmp(msg, "LEFT") == 0 || strcmp(msg, "left") == 0) 
    {
        DEBUG_PRINT("LEFT!\r\n");
        Motion_Car_Control(200,0,500);
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else if (strcmp(msg, "RIGHT") == 0 || strcmp(msg, "right") == 0) 
    {
        DEBUG_PRINT("RIGHT!\r\n");
        Motion_Car_Control(200,0,-500);
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else if (strcmp(msg, "ROTATE LEFT") == 0 || strcmp(msg, "rotate left") == 0) 
    {
        DEBUG_PRINT("ROTATE LEFT!\r\n");
        Motion_Car_Control(0,0,700);
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else if (strcmp(msg, "ROTATE RIGHT") == 0 || strcmp(msg, "rotate right") == 0) 
    {
        DEBUG_PRINT("ROTATE RIGHT!\r\n");
        Motion_Car_Control(0,0,-700);
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else {
        DEBUG_PRINT("Unknown command: %s\n", msg);
    }
}

void Human_Face_Track(int x,int w,int h)
{
    if(!Wait_Flag)
    {
        delay_ms(1000);delay_ms(1000);delay_ms(1000);//delay 3s
        Wait_Flag = 1;
        return;
    }
    
    if(Wait_Flag && !SetTarget_Flag)
    {
        SetTarget_Flag = 1;
        target_area = w*h/100;
    }

    int now_area = w*h/100;
    
    int16_t err = 280 - x;
    DEBUG_PRINT("x:%d, CENTER:%d\r\n", x, 280);
    DEBUG_PRINT("err:%d\r\n", err);
    
    pid_output = PID_Calc(err);
    DEBUG_PRINT("pid_output:%d\r\n", pid_output);
    
    DEBUG_PRINT("\r\n");
    
    int16_t err_area = target_area - now_area;
    DEBUG_PRINT("now_area:%d, target_area:%d\r\n", now_area, target_area);
    DEBUG_PRINT("err_area:%d\r\n", err_area);
    
    if(err_area<30 && err_area>-30)err_area=0;
    pid_output1 = PID_Calc(err_area);
    DEBUG_PRINT("pid_output1:%d\r\n", pid_output1);
    if(pid_output1>300) pid_output1=300;
    if(pid_output1<-300) pid_output1=-300;
    
    DEBUG_PRINT("\r\n");
        
    Motion_Car_Control(pid_output1, 0, pid_output);
}

void AprilTag_Track(int x,int w,int h)
{
    if(!Wait_Flag)
    {
        delay_ms(1000);delay_ms(1000);delay_ms(1000);//delay 3s
        Wait_Flag = 1;
        return;
    }
    
    if(Wait_Flag && !SetTarget_Flag)
    {
        SetTarget_Flag = 1;
        target_area = w*h/100;
    }
    int now_area = w*h/100;
    
    int16_t err = 200 - x;
    DEBUG_PRINT("x:%d, CENTER:%d\r\n", x, 200);
    DEBUG_PRINT("err:%d\r\n", err);
    
    pid_output = PID_Calc(err);
    DEBUG_PRINT("pid_output:%d\r\n", pid_output);
    
    DEBUG_PRINT("\r\n");
    
    int16_t err_area = target_area - now_area;
    DEBUG_PRINT("now_area:%d, target_area:%d\r\n", now_area, target_area);
    DEBUG_PRINT("err_area:%d\r\n", err_area);
    
    if(err_area<2 && err_area>-2)err_area=0;
    pid_output1 = PID_Calc(err_area);
    DEBUG_PRINT("pid_output1:%d\r\n", pid_output1);
    if(pid_output1>300) pid_output1=300;
    if(pid_output1<-300) pid_output1=-300;
    
    DEBUG_PRINT("\r\n");
        
    Motion_Car_Control(pid_output1, 0, pid_output);
}

void Licence_Track(int x1,int y1,int x2,int y2,int x3)
{
    if(!Wait_Flag)
    {
        delay_ms(1000);delay_ms(1000);delay_ms(1000);//delay 3s
        Wait_Flag = 1;
        return;
    }
    
    if(Wait_Flag && !SetTarget_Flag)
    {
        SetTarget_Flag = 1;
        target_area = (x3-x1)*(y2-y1)/100;
    }
    
    int now_area = (x3-x1)*(y2-y1)/100;
    
    int16_t err = 240 - x1;
    DEBUG_PRINT("x1:%d, CENTER:%d\r\n", x1, 240);
    DEBUG_PRINT("err:%d\r\n", err);
    if(err<5 && err>-5)err=0;
    
    pid_output = PID_Calc(err);
    DEBUG_PRINT("pid_output:%d\r\n", pid_output);
    if(pid_output>500) pid_output=500;
    if(pid_output<-500) pid_output=-500;
    
    DEBUG_PRINT("\r\n");
    
    int16_t err_area = target_area - now_area;
    DEBUG_PRINT("now_area:%d, target_area:%d\r\n", now_area, target_area);
    DEBUG_PRINT("err_area:%d\r\n", err_area);
    
    if(err_area<30 && err_area>-30)err_area=0;
    pid_output1 = PID_Calc(err_area);
    DEBUG_PRINT("pid_output1:%d\r\n", pid_output1);
    if(pid_output1>300) pid_output1=300;
    if(pid_output1<-300) pid_output1=-300;
    
    DEBUG_PRINT("\r\n");
        
    Motion_Car_Control(pid_output1, 0, pid_output);
}

void Autonomous_Avoid(int w,int h)
{
    target_area = 200;

    int now_area = w*h/100;
    
    DEBUG_PRINT("now_area:%d, target_area:%d\r\n", now_area, target_area);    
    DEBUG_PRINT("\r\n");
    
    if(now_area >= target_area)
    {
        Motion_Car_Control(0, 0, 0);
    }
    delay_ms(100);
}

void RoadSign_Rec(const char* msg)
{
    if(strcmp(msg,"go_straight")==0)
    {
        DEBUG_PRINT("go straight!\r\n");
        Motion_Car_Control(200,0,0);
        delay_ms(1000);
        delay_ms(1000);
    }
    else if(strcmp(msg,"turn_right")==0)
    {
        DEBUG_PRINT("turn right!\r\n");
        Motion_Car_Control(200,0,-300);
        delay_ms(1000);
        delay_ms(1000);
    }
    else if (strcmp(msg, "speed_limit")==0) 
    {
        DEBUG_PRINT("speed limit!\r\n");
        Motion_Car_Control(100,0,0);
        delay_ms(1000);
        delay_ms(1000);
    }
    else if (strcmp(msg, "stop")==0) 
    {
        DEBUG_PRINT("stop!\r\n");
        Motion_Car_Control(0,0,0);
        delay_ms(1000);
        delay_ms(1000);
    }
    else {
        DEBUG_PRINT("Unknown Sign: %s\n", msg);
    }
}

void Color_Rec(const char* msg)
{
    if(strcmp(msg,"RED")==0)
    {
        DEBUG_PRINT("RED!\r\n");
        RGB_Set_Color(255,255,0,0);
        RGB_Update();
        delay_ms(1000);
    }
    else if(strcmp(msg,"GREEN")==0)
    {
        DEBUG_PRINT("GREEN!\r\n");
        RGB_Set_Color(255,0,255,0);
        RGB_Update();
        delay_ms(1000);
    }
    else if (strcmp(msg, "BLUE")==0) 
    {
        DEBUG_PRINT("BLUE!\r\n");
        RGB_Set_Color(255,0,0,255);
        RGB_Update();
        delay_ms(1000);
    }
    else {
        DEBUG_PRINT("Unknown Color: %s\n", msg);
    }
}

void GazeDire_Track(int x_start, int x_end)
{
    int err = x_start - x_end;
    if(err<40 && err>-40)
    {
        err=0;
        Motion_Car_Control(0, 0, 0);
    }
    DEBUG_PRINT("x_start:%d, x_end:%d\r\n", x_start, x_end);
    DEBUG_PRINT("err:%d\r\n", err);

    // 边界检查：禁止任何越界方向的转向 Boundary check: any turn in the out-of-bounds direction is prohibited
    bool allow_motion = true;  // 默认允许运动  Movement is allowed by default

    if (x_start < 270 && err < 0) {
        // 左边界且需要向右转 → 禁止    Left boundary and need to turn right → No
        DEBUG_PRINT("STOP: x_start=%d < 100, err=%d (no right turn)\r\n", x_start, err);
        allow_motion = false;
    } 
    else if (x_start > 400 && err > 0) {
        // 右边界且需要向左转 → 禁止    Right boundary and need to turn left → No
        DEBUG_PRINT("STOP: x_start=%d > 550, err=%d (no left turn)\r\n", x_start, err);
        allow_motion = false;
    }

    // 根据条件执行动作 Perform actions based on conditions
    if (allow_motion && (err > 40 || err < -40)) {
        pid_output = PID_Calc(err);

        // 限制输出范围 Limit output range
        if (pid_output > 250) pid_output = 250;
        if (pid_output < -250) pid_output = -250;

        DEBUG_PRINT("pid_output:%d\r\n", pid_output);
        DEBUG_PRINT("\r\n");
        Motion_Car_Control(0, 0, pid_output);
    } 
    else if (!allow_motion) {
        Motion_Car_Control(0, 0, 0);
    }
}

void Hand_Track(int x,int w,int h)
{
    if(!Wait_Flag)
    {
        delay_ms(1000);delay_ms(1000);delay_ms(1000);//delay 3s
        Wait_Flag = 1;
        return;
    }
    
    if(Wait_Flag && !SetTarget_Flag)
    {
        SetTarget_Flag = 1;
        target_area = w*h/100;
        DEBUG_PRINT("target_area:%d\r\n",target_area);
    }

    int now_area = w*h/100;
    
    int16_t err = 240 - x;
    DEBUG_PRINT("x:%d, CENTER:%d\r\n", x, 240);
    DEBUG_PRINT("err:%d\r\n", err);
    
    pid_output = PID_Calc(err);
    if(pid_output>500) pid_output=500;
    if(pid_output<-500) pid_output=-500;
    DEBUG_PRINT("pid_output:%d\r\n", pid_output);
    
    DEBUG_PRINT("\r\n");
    
    int16_t err_area = target_area - now_area;
    DEBUG_PRINT("now_area:%d, target_area:%d\r\n", now_area, target_area);
    DEBUG_PRINT("err_area:%d\r\n", err_area);
    
    if(err_area<100 && err_area>-100)err_area=0;
    pid_output1 = PID_Calc(err_area);
    DEBUG_PRINT("pid_output1:%d\r\n", pid_output1);
    if(pid_output1>300) pid_output1=300;
    if(pid_output1<-300) pid_output1=-300;
    
    DEBUG_PRINT("\r\n");
        
    Motion_Car_Control(pid_output1, 0, pid_output);
}

void Target_Track(int x)
{
    int16_t err = 280 - x;
    DEBUG_PRINT("x:%d, CENTER:%d\r\n", x, 250);
    DEBUG_PRINT("err:%d\r\n", err);
    if(err<5 && err>-5)err=0;

    pid_output = PID_Calc(err);
    DEBUG_PRINT("pid_output:%d\r\n", pid_output);
    if(pid_output>700) pid_output=700;
    if(pid_output<-700) pid_output=-700;
    
    DEBUG_PRINT("\r\n");        
    Motion_Car_Control(0, 0, pid_output);
}

void HumanBody_Track(int x,int w,int h)
{
    if(!Wait_Flag)
    {
        delay_ms(1000);//delay 1s
        Wait_Flag = 1;
        return;
    }
    
    if(Wait_Flag && !SetTarget_Flag)
    {
        SetTarget_Flag = 1;
        target_area = w*h/100;
        DEBUG_PRINT("target_area:%d\r\n",target_area);
    }

    int now_area = w*h/100;
    
    int16_t err = 260 - x;
    DEBUG_PRINT("x:%d, CENTER:%d\r\n", x, 260);
    DEBUG_PRINT("err:%d\r\n", err);
    if(err<5 && err>-5)err=0;

    pid_output = PID_Calc(err);
    DEBUG_PRINT("pid_output:%d\r\n", pid_output);
    if(pid_output>400) pid_output=400;
    if(pid_output<-400) pid_output=-400;
    
    DEBUG_PRINT("\r\n");
    
    int16_t err_area = target_area - now_area;
    DEBUG_PRINT("now_area:%d, target_area:%d\r\n", now_area, target_area);
    DEBUG_PRINT("err_area:%d\r\n", err_area);
    
    if(err_area<80 && err_area>-80)err_area=0;
    pid_output1 = PID_Calc(err_area);
    DEBUG_PRINT("pid_output1:%d\r\n", pid_output1);
    if(pid_output1>750) pid_output1=750;
    if(pid_output1<-750) pid_output1=-750;
    
    DEBUG_PRINT("\r\n");
        
    Motion_Car_Control(pid_output1, 0, pid_output);
}

void OCRrec_Actions(const char* msg)
{
    if(strcmp(msg,"FORWARD")==0 || strcmp(msg,"forward")==0)
    {
        DEBUG_PRINT("FORWARD!\r\n");
        Motion_Car_Control(200,0,0);
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else if(strcmp(msg,"BACKWARD")==0 || strcmp(msg,"backward")==0)
    {
        DEBUG_PRINT("BACKWARD!\r\n");
        Motion_Car_Control(-200,0,0);
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else if (strcmp(msg, "LEFT") == 0 || strcmp(msg, "left") == 0) 
    {
        DEBUG_PRINT("LEFT!\r\n");
        Motion_Car_Control(200,0,300);
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else if (strcmp(msg, "RIGHT") == 0 || strcmp(msg, "right") == 0) 
    {
        DEBUG_PRINT("RIGHT!\r\n");
        Motion_Car_Control(200,0,-300);
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else if (strcmp(msg, "ROTATELEFT") == 0 || strcmp(msg, "rotateleft") == 0) 
    {
        DEBUG_PRINT("ROTATE LEFT!\r\n");
        Motion_Car_Control(0,0,700);
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else if (strcmp(msg, "ROTATERIGHT") == 0 || strcmp(msg, "rotateright") == 0) 
    {
        DEBUG_PRINT("ROTATE RIGHT!\r\n");
        Motion_Car_Control(0,0,-700);
        delay_ms(1000);
        delay_ms(1000);
        Motion_Car_Control(0,0,0);
    }
    else {
        DEBUG_PRINT("Unknown Character: %s\n", msg);
    }
}

