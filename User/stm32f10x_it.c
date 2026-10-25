/**
 * @file    stm32f10x_it.c
 * @brief   Cortex-M3 内核异常处理入口
 *
 * 说明:
 *   这里这些处理函数的名字是"约定死的"—— 它们和启动文件
 *   startup_stm32f10x_*.s 里的中断向量表一一对应, 复位后内核出异常时
 *   会按向量表跳到同名函数, 所以名字不能改, 只能填实现。
 *
 *   三个 Fault(Hard/MemManage/Bus/Usage) 停在死循环里, 调试时可以在这
 *   打断点, 直接抓到"程序跑飞"的第一现场; 其余用不到的异常留空即可。
 *
 *   外设中断(如 1ms 节拍的 TIM1_UP_IRQHandler)故意不放这里, 而是和控制
 *   逻辑一起写在 main.c, 避免同一个中断被两处定义。
 */
#include "stm32f10x_it.h"

/* ---- 故障类异常: 死循环陷阱, 便于调试定位 ---- */
void HardFault_Handler(void)  { while (1) {} }
void MemManage_Handler(void)  { while (1) {} }
void BusFault_Handler(void)   { while (1) {} }
void UsageFault_Handler(void) { while (1) {} }

/* ---- 其余内核异常: 本工程未使用, 留空 ---- */
void NMI_Handler(void)      {}
void SVC_Handler(void)      {}
void DebugMon_Handler(void) {}
void PendSV_Handler(void)   {}
void SysTick_Handler(void)  {}
