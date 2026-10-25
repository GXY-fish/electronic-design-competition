#ifndef __APP_MOTOR_H_
#define __APP_MOTOR_H_

#include "ti_msp_dl_config.h"
#include "app_motor_usart.h"
#include "delay.h"
#include "bsp_rgb.h"

//小车底盘电机间距之和的一半 Half of the sum of the distances between the chassis and motors of the trolley
#define Car_APB          				(188.0f)//  (228+148)/2

float PID_Calc(float actual_value);
void Set_Motor(int MOTOR_TYPE);
void Motion_Car_Control(int16_t V_x, int16_t V_y, int16_t V_z);
void Visual_Line_Track(int x,int w);
void Color_Trace(int x,int w,int h);
void QRCode_Action(const char* msg);
void Human_Face_Track(int x,int w, int h);
void AprilTag_Track(int x,int w,int h);
void Licence_Track(int x1,int y1,int x2,int y2,int x3);
void Autonomous_Avoid(int w,int h);
void RoadSign_Rec(const char* msg);
void Color_Rec(const char* msg);
void GazeDire_Track(int x_start, int x_end);
void Hand_Track(int x,int w,int h);
void Target_Track(int x);
void HumanBody_Track(int x,int w,int h);
void OCRrec_Actions(const char* msg);


#endif
