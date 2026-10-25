#ifndef __BALANCE_H
#define __BALANCE_H

#include <stdint.h>

/**
  * 稳摆控制器 (基本要求(3)/发挥部分: 直立保持) —— 双环串级 PID (A 式融合)
  *
  *   内环 = 摆杆角度环 PD : 镇定摆角(别倒), 目标 = 竖直(|theta|=180°)
  *   外环 = 臂位置环   PD : 约束旋转臂停在哪(别转飞)
  *   融合  Moto = 角度环输出 - 位置环输出   (WHEELTEC / 平衡小车同源)
  *   输出  限幅到 [-100, +100] 后交 Motor_SetSpeed(int8_t)  ★占空比量纲, 非 ±800!
  *
  * 与 Swing.c(起摆) 的接力:
  *   起摆段用能量法泵到接近倒立; main 状态机检测 Balance_InZone()==1 持续若干拍
  *   -> 调 Balance_SetSteady() 切稳态温和增益 -> 每拍 Balance_Update(...).
  *   脱离平衡区过久 -> 回起摆 或 FAIL 停车 (停转保护, 见 main 状态机).
  *
  * 增益调度(先猛后稳): 刚进平衡用 Aggressive(抓得住), 稳定后切 Steady(温和不抖).
  *
  * ★ 符号约定: 下列增益写为正数, 控制方向由 err 符号 + BAL_MOTOR_SIGN 决定。
  *   上板若发现"越纠越倒"(正反馈), 把 BAL_MOTOR_SIGN 取反即可, 不必改增益。
  *
  * ⚠ 本模块为仿真验证(balance_dualpid_sim.py 已 PASS)后落地的骨架,
  *   增益为仿真量纲的起点值, 未上板整定、未在 Keil 编译验证;
  *   接入 main 状态机 + 真机整定 Kp/Kd 后方可用于任务3。
  */

#define BAL_MOTOR_SIGN   1     // 若稳摆越纠越倒(正反馈), 改为 -1

void  Balance_Init(void);              // 复位内部状态
void  Balance_SetAggressive(void);     // 刚进平衡区: 激进增益(抓住)
void  Balance_SetSteady(void);         // 稳定后: 温和增益(不抖)
void  Balance_CaptureArmZero(void);    // 把当前臂角记为位置环目标(切入稳摆时调一次)

uint8_t Balance_InZone(float theta_deg);   // 摆角进入直立区(|theta|接近180°)返回1
void  Balance_Update(float theta_deg, float theta_dot_dps); // 每控制节拍(5ms)调用

float Balance_GetLastMoto(void);       // 最近一次输出占空比(调参/显示用)

#endif
