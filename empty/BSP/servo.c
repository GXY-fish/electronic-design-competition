#include "servo.h"

/* 当前舵机PWM值, 默认从中间位置90°开始 */
static int g_servo_pwm = 150;  // PWM=150 → 90°

/* PWM边界常量 */
#define SERVO_PWM_MIN  50   // 0°
#define SERVO_PWM_MAX  250  // 180°

static int clamp(int val, int min, int max)
{
    if (val < min) return min;
    if (val > max) return max;
    return val;
}

/**
 * @brief 舵机 PWM 初始化 (TIMG7 CCP1 → PA24, 50Hz)
 *
 * 手动配置, 因为 SysConfig 的 PWM 模块会导致 UART3 无法接收.
 * 必须在 SYSCFG_DL_init() 之后调用.
 */
void Servo_Init(void)
{
    /* 0. 确保 TIMG7 上电并复位 */
    DL_TimerG_reset(SERVO_INST);
    DL_TimerG_enablePower(SERVO_INST);
    delay_cycles(16);

    /* 1. PA24 引脚复用为 TIMG7 CCP1 (PINCM54) */
    DL_GPIO_initPeripheralOutputFunction(GPIO_SERVO_C1_IOMUX,
                                          GPIO_SERVO_C1_IOMUX_FUNC);
    DL_GPIO_enableOutput(GPIO_SERVO_C1_PORT, GPIO_SERVO_C1_PIN);

    /* 2. TIMG7 时钟: BUSCLK(80MHz) / 8 / (99+1) = 100kHz */
    static const DL_TimerG_ClockConfig clockCfg = {
        .clockSel    = DL_TIMER_CLOCK_BUSCLK,
        .divideRatio = DL_TIMER_CLOCK_DIVIDE_8,
        .prescale    = 99U
    };
    DL_TimerG_setClockConfig(SERVO_INST, (DL_TimerG_ClockConfig *)&clockCfg);

    /* 3. PWM 模式: 边沿对齐递增, 周期 2000 → 50Hz */
    static const DL_TimerG_PWMConfig pwmCfg = {
        .pwmMode           = DL_TIMER_PWM_MODE_EDGE_ALIGN_UP,
        .period            = 2000,
        .isTimerWithFourCC = false,
        .startTimer        = DL_TIMER_START,
    };
    DL_TimerG_initPWMMode(SERVO_INST, (DL_TimerG_PWMConfig *)&pwmCfg);

    /* 4. CCP1 输出控制 */
    DL_TimerG_setCounterControl(SERVO_INST,
        DL_TIMER_CZC_CCCTL1_ZCOND,
        DL_TIMER_CAC_CCCTL1_ACOND,
        DL_TIMER_CLC_CCCTL1_LCOND);

    DL_TimerG_setCaptureCompareOutCtl(SERVO_INST,
        DL_TIMER_CC_OCTL_INIT_VAL_LOW,
        DL_TIMER_CC_OCTL_INV_OUT_DISABLED,
        DL_TIMER_CC_OCTL_SRC_FUNCVAL,
        DL_TIMERG_CAPTURE_COMPARE_1_INDEX);

    DL_TimerG_setCaptCompUpdateMethod(SERVO_INST,
        DL_TIMER_CC_UPDATE_METHOD_IMMEDIATE,
        DL_TIMERG_CAPTURE_COMPARE_1_INDEX);

    DL_TimerG_setCaptureCompareValue(SERVO_INST, 150, DL_TIMER_CC_1_INDEX);

    DL_TimerG_enableClock(SERVO_INST);
    DL_TimerG_setCCPDirection(SERVO_INST, DL_TIMER_CC1_OUTPUT);

    /* 5. 启动计数器 */
    DL_Timer_startCounter(SERVO_INST);
}

void Servo_SetPWM(int pwm_value)
{
    g_servo_pwm = clamp(pwm_value, SERVO_PWM_MIN, SERVO_PWM_MAX);
    DL_Timer_setCaptureCompareValue(SERVO_INST, g_servo_pwm, GPIO_SERVO_C1_IDX);
}

void Servo_SetAngle(uint16_t angle)
{
    int pwm = 50 + (int)((uint32_t)angle * 200 / 180);
    Servo_SetPWM(pwm);
}

uint16_t Servo_GetAngle(void)
{
    return (uint16_t)((g_servo_pwm - 50) * 180 / 200);
}

int Servo_GetPWM(void)
{
    return g_servo_pwm;
}
