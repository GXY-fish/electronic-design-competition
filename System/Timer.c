/**
 * @file        Timer.c
 * @brief       TIM1 定时中断初始化（1ms 控制节拍）
 * @platform    STM32F103C8  @ APB2 = 72MHz
 * @note        公共函数名保持 Timer_Init() 不变（被 main 调用）。
 *              内部按“开时钟 → 配时基 → 配中断 → 启动”拆成四个私有函数，
 *              主函数只做顺序调用，逻辑一目了然。
 *
 * 定时参数推导：
 *   定时器时钟 = APB2 = 72MHz
 *   预分频 PSC = 72-1  → 计数频率 = 72M / 72 = 1MHz（每 tick = 1us）
 *   自动重装 ARR = 1000-1 → 计满 1000 个 tick = 1000us = 1ms 进一次中断
 *   故 TIM1 每 1ms 触发一次 Update 中断，作为倒立摆控制主节拍。
 */

#include "stm32f10x.h"   /* Device header */

/* ------------------------------------------------------------------ */
/* 私有函数 1：开启 TIM1 外设时钟                                     */
/* ------------------------------------------------------------------ */
static void Timer_ClockEnable(void)
{
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM1, ENABLE);
}

/* ------------------------------------------------------------------ */
/* 私有函数 2：配置时基（内部时钟源 + 1ms 溢出）                      */
/* ------------------------------------------------------------------ */
static void Timer_BaseSetup(void)
{
    /* TIM1 使用内部时钟（CK_INT，来自 APB2） */
    TIM_InternalClockConfig(TIM1);

    TIM_TimeBaseInitTypeDef tb;
    tb.TIM_ClockDivision     = TIM_CKD_DIV1;   /* 时钟分频：不分频            */
    tb.TIM_CounterMode       = TIM_CounterMode_Up;  /* 向上计数模式         */
    tb.TIM_Period            = 1000 - 1;      /* 自动重装值 ARR（1ms 溢出） */
    tb.TIM_Prescaler         = 72 - 1;        /* 预分频 PSC（→1MHz 计数）    */
    tb.TIM_RepetitionCounter = 0;             /* 重复计数（高级定时器特有）  */
    TIM_TimeBaseInit(TIM1, &tb);

    /* 写 ARR 后会挂起 Update 标志，先清掉，避免一使能就误进中断 */
    TIM_ClearFlag(TIM1, TIM_FLAG_Update);
}

/* ------------------------------------------------------------------ */
/* 私有函数 3：配置 NVIC 中断优先级                                    */
/* ------------------------------------------------------------------ */
static void Timer_NVICSetup(void)
{
    /* 整个工程统一用“2 位抢占 + 2 位响应”分组 */
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);

    NVIC_InitTypeDef nvic;
    nvic.NVIC_IRQChannel          = TIM1_UP_IRQn;   /* TIM1 溢出中断向量     */
    nvic.NVIC_IRQChannelCmd      = ENABLE;          /* 使能该中断通道        */
    nvic.NVIC_IRQChannelPreemptionPriority = 2;     /* 抢占优先级 2          */
    nvic.NVIC_IRQChannelSubPriority        = 1;     /* 响应优先级 1          */
    NVIC_Init(&nvic);
}

/* ------------------------------------------------------------------ */
/* 私有函数 4：使能更新中断并启动计数器                               */
/* ------------------------------------------------------------------ */
static void Timer_Start(void)
{
    TIM_ITConfig(TIM1, TIM_IT_Update, ENABLE);  /* 打开 Update 中断   */
    TIM_Cmd(TIM1, ENABLE);                      /* 计数器开始跑       */
}

/* ------------------------------------------------------------------ */
/* 公共函数：TIM1 初始化入口（顺序调用上面四步）                      */
/* ------------------------------------------------------------------ */
void Timer_Init(void)
{
    Timer_ClockEnable();   /* 1. 开时钟   */
    Timer_BaseSetup();     /* 2. 配时基   */
    Timer_NVICSetup();     /* 3. 配中断   */
    Timer_Start();         /* 4. 启动     */
}

/* TIM1 中断服务函数已统一移至 User/stm32f10x_it.c，
   此处不再重复定义，避免与向量表中的同名符号冲突。 */
