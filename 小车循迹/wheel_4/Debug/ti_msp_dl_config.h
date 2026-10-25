/*
 * Copyright (c) 2023, Texas Instruments Incorporated - http://www.ti.com
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * *  Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *
 * *  Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * *  Neither the name of Texas Instruments Incorporated nor the names of
 *    its contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
 * OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/*
 *  ============ ti_msp_dl_config.h =============
 *  Configured MSPM0 DriverLib module declarations
 *
 *  DO NOT EDIT - This file is generated for the MSPM0G350X
 *  by the SysConfig tool.
 */
#ifndef ti_msp_dl_config_h
#define ti_msp_dl_config_h

#define CONFIG_MSPM0G350X
#define CONFIG_MSPM0G3507

#if defined(__ti_version__) || defined(__TI_COMPILER_VERSION__)
#define SYSCONFIG_WEAK __attribute__((weak))
#elif defined(__IAR_SYSTEMS_ICC__)
#define SYSCONFIG_WEAK __weak
#elif defined(__GNUC__)
#define SYSCONFIG_WEAK __attribute__((weak))
#endif

#include <ti/devices/msp/msp.h>
#include <ti/driverlib/driverlib.h>
#include <ti/driverlib/m0p/dl_core.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 *  ======== SYSCFG_DL_init ========
 *  Perform all required MSP DL initialization
 *
 *  This function should be called once at a point before any use of
 *  MSP DL.
 */


/* clang-format off */

#define POWER_STARTUP_DELAY                                                (16)


#define CPUCLK_FREQ                                                     32000000



/* Defines for PWM_0 */
#define PWM_0_INST                                                         TIMA0
#define PWM_0_INST_IRQHandler                                   TIMA0_IRQHandler
#define PWM_0_INST_INT_IRQN                                     (TIMA0_INT_IRQn)
#define PWM_0_INST_CLK_FREQ                                              4000000
/* GPIO defines for channel 0 */
#define GPIO_PWM_0_C0_PORT                                                 GPIOA
#define GPIO_PWM_0_C0_PIN                                          DL_GPIO_PIN_0
#define GPIO_PWM_0_C0_IOMUX                                       (IOMUX_PINCM1)
#define GPIO_PWM_0_C0_IOMUX_FUNC                      IOMUX_PINCM1_PF_TIMA0_CCP0
#define GPIO_PWM_0_C0_IDX                                    DL_TIMER_CC_0_INDEX
/* GPIO defines for channel 1 */
#define GPIO_PWM_0_C1_PORT                                                 GPIOA
#define GPIO_PWM_0_C1_PIN                                          DL_GPIO_PIN_1
#define GPIO_PWM_0_C1_IOMUX                                       (IOMUX_PINCM2)
#define GPIO_PWM_0_C1_IOMUX_FUNC                      IOMUX_PINCM2_PF_TIMA0_CCP1
#define GPIO_PWM_0_C1_IDX                                    DL_TIMER_CC_1_INDEX
/* GPIO defines for channel 2 */
#define GPIO_PWM_0_C2_PORT                                                 GPIOA
#define GPIO_PWM_0_C2_PIN                                         DL_GPIO_PIN_15
#define GPIO_PWM_0_C2_IOMUX                                      (IOMUX_PINCM37)
#define GPIO_PWM_0_C2_IOMUX_FUNC                     IOMUX_PINCM37_PF_TIMA0_CCP2
#define GPIO_PWM_0_C2_IDX                                    DL_TIMER_CC_2_INDEX
/* GPIO defines for channel 3 */
#define GPIO_PWM_0_C3_PORT                                                 GPIOB
#define GPIO_PWM_0_C3_PIN                                         DL_GPIO_PIN_24
#define GPIO_PWM_0_C3_IOMUX                                      (IOMUX_PINCM52)
#define GPIO_PWM_0_C3_IOMUX_FUNC                     IOMUX_PINCM52_PF_TIMA0_CCP3
#define GPIO_PWM_0_C3_IDX                                    DL_TIMER_CC_3_INDEX



/* Defines for TIMER_0 */
#define TIMER_0_INST                                                     (TIMA1)
#define TIMER_0_INST_IRQHandler                                 TIMA1_IRQHandler
#define TIMER_0_INST_INT_IRQN                                   (TIMA1_INT_IRQn)
#define TIMER_0_INST_LOAD_VALUE                                            (39U)



/* Defines for UART_0 */
#define UART_0_INST                                                        UART0
#define UART_0_INST_FREQUENCY                                           32000000
#define UART_0_INST_IRQHandler                                  UART0_IRQHandler
#define UART_0_INST_INT_IRQN                                      UART0_INT_IRQn
#define GPIO_UART_0_RX_PORT                                                GPIOA
#define GPIO_UART_0_TX_PORT                                                GPIOA
#define GPIO_UART_0_RX_PIN                                        DL_GPIO_PIN_11
#define GPIO_UART_0_TX_PIN                                        DL_GPIO_PIN_10
#define GPIO_UART_0_IOMUX_RX                                     (IOMUX_PINCM22)
#define GPIO_UART_0_IOMUX_TX                                     (IOMUX_PINCM21)
#define GPIO_UART_0_IOMUX_RX_FUNC                      IOMUX_PINCM22_PF_UART0_RX
#define GPIO_UART_0_IOMUX_TX_FUNC                      IOMUX_PINCM21_PF_UART0_TX
#define UART_0_BAUD_RATE                                                (115200)
#define UART_0_IBRD_32_MHZ_115200_BAUD                                      (17)
#define UART_0_FBRD_32_MHZ_115200_BAUD                                      (23)





/* Port definition for Pin Group LED */
#define LED_PORT                                                         (GPIOB)

/* Defines for PIN_0: GPIOB.22 with pinCMx 50 on package pin 21 */
#define LED_PIN_0_PIN                                           (DL_GPIO_PIN_22)
#define LED_PIN_0_IOMUX                                          (IOMUX_PINCM50)
/* Port definition for Pin Group Encoder */
#define Encoder_PORT                                                     (GPIOB)

/* Defines for E1A: GPIOB.0 with pinCMx 12 on package pin 47 */
// pins affected by this interrupt request:["E1A","E1B","E2A","E2B","E3A","E3B","E4A","E4B"]
#define Encoder_INT_IRQN                                        (GPIOB_INT_IRQn)
#define Encoder_INT_IIDX                        (DL_INTERRUPT_GROUP1_IIDX_GPIOB)
#define Encoder_E1A_IIDX                                     (DL_GPIO_IIDX_DIO0)
#define Encoder_E1A_PIN                                          (DL_GPIO_PIN_0)
#define Encoder_E1A_IOMUX                                        (IOMUX_PINCM12)
/* Defines for E1B: GPIOB.1 with pinCMx 13 on package pin 48 */
#define Encoder_E1B_IIDX                                     (DL_GPIO_IIDX_DIO1)
#define Encoder_E1B_PIN                                          (DL_GPIO_PIN_1)
#define Encoder_E1B_IOMUX                                        (IOMUX_PINCM13)
/* Defines for E2A: GPIOB.2 with pinCMx 15 on package pin 50 */
#define Encoder_E2A_IIDX                                     (DL_GPIO_IIDX_DIO2)
#define Encoder_E2A_PIN                                          (DL_GPIO_PIN_2)
#define Encoder_E2A_IOMUX                                        (IOMUX_PINCM15)
/* Defines for E2B: GPIOB.3 with pinCMx 16 on package pin 51 */
#define Encoder_E2B_IIDX                                     (DL_GPIO_IIDX_DIO3)
#define Encoder_E2B_PIN                                          (DL_GPIO_PIN_3)
#define Encoder_E2B_IOMUX                                        (IOMUX_PINCM16)
/* Defines for E3A: GPIOB.4 with pinCMx 17 on package pin 52 */
#define Encoder_E3A_IIDX                                     (DL_GPIO_IIDX_DIO4)
#define Encoder_E3A_PIN                                          (DL_GPIO_PIN_4)
#define Encoder_E3A_IOMUX                                        (IOMUX_PINCM17)
/* Defines for E3B: GPIOB.5 with pinCMx 18 on package pin 53 */
#define Encoder_E3B_IIDX                                     (DL_GPIO_IIDX_DIO5)
#define Encoder_E3B_PIN                                          (DL_GPIO_PIN_5)
#define Encoder_E3B_IOMUX                                        (IOMUX_PINCM18)
/* Defines for E4A: GPIOB.12 with pinCMx 29 on package pin 64 */
#define Encoder_E4A_IIDX                                    (DL_GPIO_IIDX_DIO12)
#define Encoder_E4A_PIN                                         (DL_GPIO_PIN_12)
#define Encoder_E4A_IOMUX                                        (IOMUX_PINCM29)
/* Defines for E4B: GPIOB.13 with pinCMx 30 on package pin 1 */
#define Encoder_E4B_IIDX                                    (DL_GPIO_IIDX_DIO13)
#define Encoder_E4B_PIN                                         (DL_GPIO_PIN_13)
#define Encoder_E4B_IOMUX                                        (IOMUX_PINCM30)
/* Port definition for Pin Group Motor_Ctrl_A */
#define Motor_Ctrl_A_PORT                                                (GPIOA)

/* Defines for AIN1: GPIOA.7 with pinCMx 14 on package pin 49 */
#define Motor_Ctrl_A_AIN1_PIN                                    (DL_GPIO_PIN_7)
#define Motor_Ctrl_A_AIN1_IOMUX                                  (IOMUX_PINCM14)
/* Defines for AIN2: GPIOA.8 with pinCMx 19 on package pin 54 */
#define Motor_Ctrl_A_AIN2_PIN                                    (DL_GPIO_PIN_8)
#define Motor_Ctrl_A_AIN2_IOMUX                                  (IOMUX_PINCM19)
/* Defines for BIN1: GPIOA.12 with pinCMx 34 on package pin 5 */
#define Motor_Ctrl_A_BIN1_PIN                                   (DL_GPIO_PIN_12)
#define Motor_Ctrl_A_BIN1_IOMUX                                  (IOMUX_PINCM34)
/* Defines for BIN2: GPIOA.13 with pinCMx 35 on package pin 6 */
#define Motor_Ctrl_A_BIN2_PIN                                   (DL_GPIO_PIN_13)
#define Motor_Ctrl_A_BIN2_IOMUX                                  (IOMUX_PINCM35)
/* Port definition for Pin Group Motor_Ctrl_B */
#define Motor_Ctrl_B_PORT                                                (GPIOB)

/* Defines for CIN1: GPIOB.15 with pinCMx 32 on package pin 3 */
#define Motor_Ctrl_B_CIN1_PIN                                   (DL_GPIO_PIN_15)
#define Motor_Ctrl_B_CIN1_IOMUX                                  (IOMUX_PINCM32)
/* Defines for CIN2: GPIOB.16 with pinCMx 33 on package pin 4 */
#define Motor_Ctrl_B_CIN2_PIN                                   (DL_GPIO_PIN_16)
#define Motor_Ctrl_B_CIN2_IOMUX                                  (IOMUX_PINCM33)
/* Defines for DIN1: GPIOB.17 with pinCMx 43 on package pin 14 */
#define Motor_Ctrl_B_DIN1_PIN                                   (DL_GPIO_PIN_17)
#define Motor_Ctrl_B_DIN1_IOMUX                                  (IOMUX_PINCM43)
/* Defines for DIN2: GPIOB.18 with pinCMx 44 on package pin 15 */
#define Motor_Ctrl_B_DIN2_PIN                                   (DL_GPIO_PIN_18)
#define Motor_Ctrl_B_DIN2_IOMUX                                  (IOMUX_PINCM44)


/* clang-format on */

void SYSCFG_DL_init(void);
void SYSCFG_DL_initPower(void);
void SYSCFG_DL_GPIO_init(void);
void SYSCFG_DL_SYSCTL_init(void);
void SYSCFG_DL_PWM_0_init(void);
void SYSCFG_DL_TIMER_0_init(void);
void SYSCFG_DL_UART_0_init(void);


bool SYSCFG_DL_saveConfiguration(void);
bool SYSCFG_DL_restoreConfiguration(void);

#ifdef __cplusplus
}
#endif

#endif /* ti_msp_dl_config_h */
