#include "pid.h"
#include "board.h"
extern float Kp,Ki,Kd;   //直立环参数
float err = 0;               //此次误差
float last_err = 0;          //上次误差
float err_sum=0;         //误差累加
float err_difference = 0;    //误差的差值

/****************循迹，位置环********************/
//float place_Kp=20*0.6,place_Ki=1.8,place_Kd=6;  
float place_Kp=6,place_Ki=0.4,place_Kd=6;  
float place_err;               //此次误差
float place_last_err;          //上次误差
float place_err_sum=0;         //误差累加
float place_err_difference;    //误差的差值
float place_PID_value(float measure,float calcu)//循迹用的位置环
{
	place_err = measure - calcu;             //误差
	place_err_sum+=place_err;                      //误差的累加
   place_err_sum = I_xianfu(50,place_err_sum);
//   V_xianfu(5500);//0.3M/S可以这么限制幅度
//    V3_xianfu(800);
	place_err_difference = place_err - place_last_err;   //误差的差值
	place_last_err = place_err;                    //此次误差记录为“上次误差”
	return place_Kp*place_err + place_Ki*place_err_sum + place_Kd*place_err_difference;

}

//I限幅：
float I_xianfu(float max,float now)
{
      if(now > max)  now =  max;
      if(now < -max) now = -max;
   
  return now;
}