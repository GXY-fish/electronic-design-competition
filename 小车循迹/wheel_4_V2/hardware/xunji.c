/**
 * @file    xunji.c
 * @brief   八路红外巡线传感器 — GPIO 直读 + 加权质心 + PD 差速 (四驱)
 */

#include "xunji.h"
#include "motor_ctrl.h"

/* ================================================================
 * GPIO: X1=PB6 X2=PB7 X3=PB8 X4=PB9 X5=PB10 X6=PB11 X7=PB14 X8=PB19
 * ================================================================ */

#define XJ_RD(port, pin)  ((DL_GPIO_readPins(port, pin) == (pin)) ? 1 : 0)

typedef struct { GPIO_Regs *port; uint32_t pin; } xj_pin_t;
static const xj_pin_t xj_pins[8] = {
    { GPIOB, DL_GPIO_PIN_6  }, { GPIOB, DL_GPIO_PIN_7  },
    { GPIOB, DL_GPIO_PIN_8  }, { GPIOB, DL_GPIO_PIN_9  },
    { GPIOB, DL_GPIO_PIN_10 }, { GPIOB, DL_GPIO_PIN_11 },
    { GPIOB, DL_GPIO_PIN_14 }, { GPIOB, DL_GPIO_PIN_19 },
};
static const uint32_t xj_iomux[8] = {
    IOMUX_PINCM23, IOMUX_PINCM24, IOMUX_PINCM25, IOMUX_PINCM26,
    IOMUX_PINCM27, IOMUX_PINCM28, IOMUX_PINCM31, IOMUX_PINCM45,
};

/* ================================================================
 * 数据 & 参数
 * ================================================================ */

static uint8_t  track_bits    = 0xFF;
static volatile uint8_t data_updated = 0;
uint8_t xj_enable      = 1;
float   xj_base_speed  = 350.0f;
int16_t xj_error       = 0;
static float xj_last_error = 0.0f;
volatile uint32_t g_xj_read_ok   = 0;
volatile uint32_t g_xj_ctrl_call = 0;

/* ================================================================
 * 初始化
 * ================================================================ */

void XJ_Init(void)
{
    for (int i = 0; i < 8; i++)
        DL_GPIO_initDigitalInputFeatures(xj_iomux[i],
            DL_GPIO_INVERSION_DISABLE, DL_GPIO_RESISTOR_PULL_UP,
            DL_GPIO_HYSTERESIS_DISABLE, DL_GPIO_WAKEUP_DISABLE);
    track_bits = 0xFF; data_updated = 0;
}

/* ================================================================
 * 读取 8 路
 * ================================================================ */

void XJ_Update(void)
{
    uint8_t d = 0;
    for (int i = 0; i < 8; i++)
        if (XJ_RD(xj_pins[i].port, xj_pins[i].pin)) d |= (1 << (7 - i));
    track_bits = d; data_updated = 1; g_xj_read_ok++;
}

uint8_t XJ_GetValue(uint8_t i)  { return (i > 7) ? 1 : ((track_bits >> (7 - i)) & 1); }
uint8_t XJ_GetAllChannels(void) { return track_bits; }
uint8_t XJ_DataUpdated(void)    { uint8_t r = data_updated; data_updated = 0; return r; }

/* ================================================================
 * 加权质心法 → 偏差 (-3.5 ~ +3.5), 999=丢线
 * ================================================================ */

static float calc_line_error(void)
{
    float sum = 0.0f, weighted = 0.0f;
    for (uint8_t i = 0; i < 8; i++) {
        if (XJ_GetValue(i) == 0) { weighted += (float)i; sum += 1.0f; }
    }
    if (sum == 0.0f) return 999.0f;
    if (sum == 8.0f) return 0.0f;
    return weighted / sum - 3.5f;  /* 线偏右→err>0, 线偏左→err<0 */
}

/* ================================================================
 * 巡线控制
 * ================================================================ */

void XJ_LineFollowing_Init(void)
{
    xj_last_error = 0.0f;
    /* 用已有的 pid_Turn, 配置巡线参数 */
    Set_PID_Param(&pid_Turn, 400.0f, 0.0f, 10.0f);
    pid_Turn.PID_Limit_MAX = 500;
    pid_Turn.Ki_Limit_MAX  = 200;
}

void XJ_PID_SetTunings(float Kp, float Ki, float Kd) {
    Set_PID_Param(&pid_Turn, Kp, Ki, Kd);
}
void XJ_PID_GetTunings(float *Kp, float *Ki, float *Kd) {
    *Kp = pid_Turn.Kp; *Ki = pid_Turn.Ki; *Kd = pid_Turn.Kd;
}

void XJ_LineFollowing_Update(void)
{
    g_xj_ctrl_call++;
    if (!xj_enable) return;

    float err = calc_line_error();
    xj_error = (int16_t)(err * 10.0f);

    /* 丢线: 慢转找线 */
    if (err > 100.0f) {
        int d = (xj_last_error >= 0.0f) ? 1 : -1;
        int spd = (int)xj_base_speed;
        if (d > 0) SET_MOTORS_SPEED(0, spd, 0, spd);
        else       SET_MOTORS_SPEED(spd, 0, spd, 0);
        return;
    }

    /* PID 输出 → 差速修正量 */
    float corr = PID_Calculate(&pid_Turn, 0.0f, err);
    xj_last_error = err;

    int base = (int)xj_base_speed;
    int diff = (int)corr;

    /* 限幅: 允许大差速响应 */
    int maxDiff = 500;
    if (diff > maxDiff)  diff = maxDiff;
    if (diff < -maxDiff) diff = -maxDiff;

    /* diff>0: 线右→左慢右快→右转; diff<0: 线左→左快右慢→左转 */
    SET_MOTORS_SPEED_DIFF(base, diff);
}
