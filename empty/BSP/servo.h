#ifndef SERVO_H
#define SERVO_H

#include "ti_msp_dl_config.h"

/* ====== 舵机硬件定义 (TIMG7 CCP1 → PA24, 50Hz) ====== */
/* 如果 SysConfig 没生成这些宏则手动定义 */
#ifndef SERVO_INST
#define SERVO_INST                     TIMG7
#endif
#ifndef SERVO_INST_CLK_FREQ
#define SERVO_INST_CLK_FREQ            100000
#endif
#ifndef GPIO_SERVO_C1_PORT
#define GPIO_SERVO_C1_PORT             GPIOA
#endif
#ifndef GPIO_SERVO_C1_PIN
#define GPIO_SERVO_C1_PIN              DL_GPIO_PIN_24
#endif
#ifndef GPIO_SERVO_C1_IOMUX
#define GPIO_SERVO_C1_IOMUX            (IOMUX_PINCM54)
#endif
#ifndef GPIO_SERVO_C1_IOMUX_FUNC
#define GPIO_SERVO_C1_IOMUX_FUNC       IOMUX_PINCM54_PF_TIMG7_CCP1
#endif
#ifndef GPIO_SERVO_C1_IDX
#define GPIO_SERVO_C1_IDX              DL_TIMER_CC_1_INDEX
#endif

/**
 * @brief 初始化舵机 PWM (TIMG7, PA24, 50Hz)
 *
 * 手动配置 TIMG7 CCP1 输出 50Hz PWM 到 PA24.
 * 必须在 SYSCFG_DL_init() 之后调用.
 */
void Servo_Init(void);

void Servo_SetPWM(int pwm_value);
void Servo_SetAngle(uint16_t angle);
uint16_t Servo_GetAngle(void);
int Servo_GetPWM(void);

#endif /* SERVO_H */
