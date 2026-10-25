#ifndef __PID_H
#define __PID_H

//#ifndef PID_CONTROLLER_H
//#define PID_CONTROLLER_H
// PID结构体（核心）
typedef struct {
    float Kp, Ki, Kd;      // PID系数
    float err_sun;        // 积分累积
    float last_error;      // 上次误差（用于微分）
    float max_err_sun;    // 积分限幅（防饱和）
    float max_output;      // 输出限幅
} PID_Controller;
//#endif // PID_CONTROLLER_H

float I_xianfu(float max,float now);
float place_PID_value(float measure,float calcu);//循迹用的位置环



#endif