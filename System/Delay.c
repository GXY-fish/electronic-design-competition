/**
 * @file        Delay.c
 * @brief       基于 SysTick 的阻塞式延时（us / ms / s）
 * @platform    STM32F103C8  @ HCLK = 72MHz
 * @note        本文件为系统级驱动，公共函数名保持 Delay_us/Delay_ms/Delay_s
 *              不变（被 OLED、main 等模块调用），仅重写内部实现与注释风格。
 *
 * 原理简述：
 *   SysTick 是 Cortex-M3 内核自带的 24 位递减定时器。
 *   把它的时钟源选成 HCLK(72MHz) 后，每个计数周期 = 1/72 us。
 *   因此“延时 x us”只需把重载值 LOAD 设为 72*x，启动后等它数到 0 即可。
 *   注意：LOAD 是 24 位寄存器，最大值 0xFFFFFF ≈ 1677 万，
 *   72 * xus 不得超过该上限（约 xus ≤ 233015），超了会回绕。
 */

#include "stm32f10x.h"

/* ------------------------------------------------------------------ */
/* 私有常量：把 SysTick 控制寄存器的“魔法数”翻译成可读位定义          */
/* ------------------------------------------------------------------ */
#define SYSTICK_CTRL_ENABLE    (1u << 0)   /* bit0 : 计数器使能                  */
#define SYSTICK_CTRL_CLKSRC    (1u << 2)   /* bit2 : 1=HCLK(72M)，0=HCLK/8      */
#define SYSTICK_CTRL_COUNTFLAG (1u << 16)  /* bit16: 计数到 0 后置 1（读后清）   */

/* 每个微秒对应的 SysTick 计数个数（72MHz / 1MHz = 72） */
#define SYSTICK_TICKS_PER_US   (SystemCoreClock / 1000000u)

/* ------------------------------------------------------------------ */
/* 私有函数：纯微秒阻塞延时（Delay_ms / Delay_s 的底层引擎）          */
/* ------------------------------------------------------------------ */

/**
 * @brief  微秒级阻塞延时
 * @param  us  延时时长（建议 ≤ 233015，受 24 位 LOAD 限制）
 */
static void Delay_BlockUs(uint32_t us)
{
    SysTick->LOAD  = (uint32_t)SYSTICK_TICKS_PER_US * us;  /* 设定倒计时总量   */
    SysTick->VAL   = 0u;                                   /* 清空当前计数值   */
    SysTick->CTRL  = SYSTICK_CTRL_ENABLE | SYSTICK_CTRL_CLKSRC;  /* 启动，源=HCLK */
    while ((SysTick->CTRL & SYSTICK_CTRL_COUNTFLAG) == 0u)      /* 等数到 0        */
    {
        /* 空转等待，无操作 */
    }
    SysTick->CTRL  = SYSTICK_CTRL_CLKSRC;                   /* 关闭使能（保留源配置） */
}

/* ------------------------------------------------------------------ */
/* 公共函数                                                            */
/* ------------------------------------------------------------------ */

/**
 * @brief  微秒级延时（对外接口）
 */
void Delay_us(uint32_t us)
{
    Delay_BlockUs(us);
}

/**
 * @brief  毫秒级延时
 * @param  ms  延时时长，范围：0 ~ 0xFFFFFFFF
 */
void Delay_ms(uint32_t ms)
{
    while (ms-- != 0u)
    {
        Delay_BlockUs(1000u);   /* 1 ms = 1000 us，循环累加 */
    }
}

/**
 * @brief  秒级延时
 * @param  s  延时时长，范围：0 ~ 0xFFFFFFFF
 */
void Delay_s(uint32_t s)
{
    while (s-- != 0u)
    {
        Delay_ms(1000u);        /* 1 s = 1000 ms，循环累加 */
    }
}
