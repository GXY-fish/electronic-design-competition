#ifndef __PENDULUM_H
#define __PENDULUM_H

/**
  * 摆杆角度测量 (依据 PID电机驱动及控制板-V1.0 原理图)
  *   - 臂角编码器: TIM3 (PA6/PA7)  -> 电机编码器
  *   - 摆杆相对臂角: ADC1_IN8 (PB0) -> 角度传感器电位器 (SENSOR1)
  *   绝对摆角 theta = THETA_SIGN * 摆杆相对角(电位器), 0° = 自然下垂(与臂方位角无关)
  *   (旋转倒立摆: 电机只转臂方位, 摆杆重力角仅由关节电位器决定; 上电下垂,
  *    按 K1 启动会调用 Pendulum_Zero 采当前 ADC 作为零位)
  */
void Pendulum_Init(void);
void Pendulum_Zero(void);     // 清零角度/速度 (假设已处于下垂零位)
void Pendulum_ZeroArm(void);  // 仅把臂角参考归零(不动摆杆零位), 起摆标定后用
void Pendulum_Update(void);   // 每个控制节拍调用: 更新绝对摆角与角速度

float Pendulum_GetAngle(void);   // 绝对摆角(度, EMA 滤波后), 0=下垂, +为逆时针
float Pendulum_GetSpeed(void);   // 角速度(度/秒)
float Pendulum_GetArmAngle(void); // 臂方位角(度, TIM3 编码器累加), 稳摆外环(位置环)用
uint16_t Pendulum_GetRawAdc(void); // 最近一次电位器原始 ADC 值(诊断漂移用)
void Pendulum_TrackZero(void);    // 空闲时由 main 周期调用, 缓慢跟踪零位抵消漂移

#define CONTROL_TS   0.005f    // 控制节拍周期 = 1/200Hz = 5ms
#define THETA_SIGN  1          // 若摆角方向反了, 改为 -1

#endif
