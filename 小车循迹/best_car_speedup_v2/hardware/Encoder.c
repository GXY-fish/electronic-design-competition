/**
 * @file    Encoder.c
 * @brief   4 通道编码器 — GPIOB GROUP1 中断，8 引脚全在一个 handler
 *          E1: PB0/PB1 → M1, E2: PB2/PB3 → M2
 *          E3: PB4/PB5 → M3, E4: PB12/PB13 → M4
 */

#include "Encoder.h"

int32_t Motor1_Encoder_Value = 0;
int32_t Motor2_Encoder_Value = 0;
int32_t Motor3_Encoder_Value = 0;
int32_t Motor4_Encoder_Value = 0;

/* ISR 触发计数器 (诊断用: 看哪个编码器的中断在工作) */
volatile uint32_t g_enc_isr_cnt[4] = {0, 0, 0, 0};

float Motor1_Speed = 0;
float Motor2_Speed = 0;
float Motor3_Speed = 0;
float Motor4_Speed = 0;

void GROUP1_IRQHandler(void)
{
    uint32_t pendingInt;

    if (DL_Interrupt_getStatusGroup(DL_INTERRUPT_GROUP_1, Encoder_INT_IIDX))
    {
        pendingInt = DL_GPIO_getEnabledInterruptStatus(
            Encoder_PORT,
            Encoder_E1A_PIN | Encoder_E1B_PIN |
            Encoder_E2A_PIN | Encoder_E2B_PIN |
            Encoder_E3A_PIN | Encoder_E3B_PIN |
            Encoder_E4A_PIN | Encoder_E4B_PIN);

        /* ---- Motor1 Phase A (E1A) ---- */
        if (pendingInt & Encoder_E1A_PIN) {
            DL_GPIO_clearInterruptStatus(Encoder_PORT, Encoder_E1A_PIN);
            g_enc_isr_cnt[0]++;
            if (Read_Encoder_E1A == 1) {
                if (Read_Encoder_E1B == 0)      Motor1_Encoder_Value++;
                else if (Read_Encoder_E1B == 1) Motor1_Encoder_Value--;
            } else {
                if (Read_Encoder_E1B == 0)      Motor1_Encoder_Value--;
                else if (Read_Encoder_E1B == 1) Motor1_Encoder_Value++;
            }
        }
        /* ---- Motor1 Phase B (E1B) ---- */
        if (pendingInt & Encoder_E1B_PIN) {
            DL_GPIO_clearInterruptStatus(Encoder_PORT, Encoder_E1B_PIN);
            g_enc_isr_cnt[0]++;
            if (Read_Encoder_E1B == 1) {
                if (Read_Encoder_E1A == 0)      Motor1_Encoder_Value--;
                else if (Read_Encoder_E1A == 1) Motor1_Encoder_Value++;
            } else {
                if (Read_Encoder_E1A == 0)      Motor1_Encoder_Value++;
                else if (Read_Encoder_E1A == 1) Motor1_Encoder_Value--;
            }
        }
        /* ---- Motor2 Phase A (E2A) ---- */
        if (pendingInt & Encoder_E2A_PIN) {
            g_enc_isr_cnt[1]++;
            DL_GPIO_clearInterruptStatus(Encoder_PORT, Encoder_E2A_PIN);
            if (Read_Encoder_E2A == 1) {
                if (Read_Encoder_E2B == 0)      Motor2_Encoder_Value++;
                else if (Read_Encoder_E2B == 1) Motor2_Encoder_Value--;
            } else {
                if (Read_Encoder_E2B == 0)      Motor2_Encoder_Value--;
                else if (Read_Encoder_E2B == 1) Motor2_Encoder_Value++;
            }
        }
        /* ---- Motor2 Phase B (E2B) ---- */
        if (pendingInt & Encoder_E2B_PIN) {
            DL_GPIO_clearInterruptStatus(Encoder_PORT, Encoder_E2B_PIN);
            g_enc_isr_cnt[1]++;
            if (Read_Encoder_E2B == 1) {
                if (Read_Encoder_E2A == 0)      Motor2_Encoder_Value--;
                else if (Read_Encoder_E2A == 1) Motor2_Encoder_Value++;
            } else {
                if (Read_Encoder_E2A == 0)      Motor2_Encoder_Value++;
                else if (Read_Encoder_E2A == 1) Motor2_Encoder_Value--;
            }
        }
        /* ---- Motor3 Phase A (E3A) ---- */
        if (pendingInt & Encoder_E3A_PIN) {
            DL_GPIO_clearInterruptStatus(Encoder_PORT, Encoder_E3A_PIN);
            g_enc_isr_cnt[2]++;
            if (Read_Encoder_E3A == 1) {
                if (Read_Encoder_E3B == 0)      Motor3_Encoder_Value++;
                else if (Read_Encoder_E3B == 1) Motor3_Encoder_Value--;
            } else {
                if (Read_Encoder_E3B == 0)      Motor3_Encoder_Value--;
                else if (Read_Encoder_E3B == 1) Motor3_Encoder_Value++;
            }
        }
        /* ---- Motor3 Phase B (E3B) ---- */
        if (pendingInt & Encoder_E3B_PIN) {
            DL_GPIO_clearInterruptStatus(Encoder_PORT, Encoder_E3B_PIN);
            g_enc_isr_cnt[2]++;
            if (Read_Encoder_E3B == 1) {
                if (Read_Encoder_E3A == 0)      Motor3_Encoder_Value--;
                else if (Read_Encoder_E3A == 1) Motor3_Encoder_Value++;
            } else {
                if (Read_Encoder_E3A == 0)      Motor3_Encoder_Value++;
                else if (Read_Encoder_E3A == 1) Motor3_Encoder_Value--;
            }
        }
        /* ---- Motor4 Phase A (E4A) ---- */
        if (pendingInt & Encoder_E4A_PIN) {
            DL_GPIO_clearInterruptStatus(Encoder_PORT, Encoder_E4A_PIN);
            g_enc_isr_cnt[3]++;
            if (Read_Encoder_E4A == 1) {
                if (Read_Encoder_E4B == 0)      Motor4_Encoder_Value++;
                else if (Read_Encoder_E4B == 1) Motor4_Encoder_Value--;
            } else {
                if (Read_Encoder_E4B == 0)      Motor4_Encoder_Value--;
                else if (Read_Encoder_E4B == 1) Motor4_Encoder_Value++;
            }
        }
        /* ---- Motor4 Phase B (E4B) ---- */
        if (pendingInt & Encoder_E4B_PIN) {
            DL_GPIO_clearInterruptStatus(Encoder_PORT, Encoder_E4B_PIN);
            g_enc_isr_cnt[3]++;
            if (Read_Encoder_E4B == 1) {
                if (Read_Encoder_E4A == 0)      Motor4_Encoder_Value--;
                else if (Read_Encoder_E4A == 1) Motor4_Encoder_Value++;
            } else {
                if (Read_Encoder_E4A == 0)      Motor4_Encoder_Value++;
                else if (Read_Encoder_E4A == 1) Motor4_Encoder_Value--;
            }
        }
    }
}

/* 差分测速: 保留原始累计值，用 delta 算速度 */
static float Encoder_Calc_Speed(int32_t  cur_val, int32_t *last_val)
{
    int32_t delta = cur_val - *last_val;
    *last_val = cur_val;
    /* 速度 (mm/s) = (delta/CPR) * 周长 / 采样周期 */
    return (float)delta * WHEEL_CIRCUM / (CPR * SAMPLE_TIME);
}

static int32_t last_m1 = 0, last_m2 = 0, last_m3 = 0, last_m4 = 0;

void Motor1_Get_Speed(void) { Motor1_Speed =  Encoder_Calc_Speed(Motor1_Encoder_Value, &last_m1); }
void Motor2_Get_Speed(void) { Motor2_Speed = -Encoder_Calc_Speed(Motor2_Encoder_Value, &last_m2); }
void Motor3_Get_Speed(void) { Motor3_Speed =  Encoder_Calc_Speed(Motor3_Encoder_Value, &last_m3); }
void Motor4_Get_Speed(void) { Motor4_Speed = -Encoder_Calc_Speed(Motor4_Encoder_Value, &last_m4); }

static float Motor1_Lucheng = 0, Motor2_Lucheng = 0;
static float Motor3_Lucheng = 0, Motor4_Lucheng = 0;
float Measure_Distance = 0;

void MEASURE_MOTORS_SPEED(void)
{
    Motor1_Get_Speed();
    Motor2_Get_Speed();
    Motor3_Get_Speed();
    Motor4_Get_Speed();

    Motor1_Lucheng += Motor1_Speed * SAMPLE_TIME;
    Motor2_Lucheng += Motor2_Speed * SAMPLE_TIME;
    Motor3_Lucheng += Motor3_Speed * SAMPLE_TIME;
    Motor4_Lucheng += Motor4_Speed * SAMPLE_TIME;
    Measure_Distance = (Motor1_Lucheng + Motor2_Lucheng +
                        Motor3_Lucheng + Motor4_Lucheng) / 4.0f;

    if (Measure_Distance > 10000) {
        Measure_Distance = 0;
        Motor1_Lucheng = 0;
        Motor2_Lucheng = 0;
        Motor3_Lucheng = 0;
        Motor4_Lucheng = 0;
    }
}
