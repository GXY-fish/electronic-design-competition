/**
 * @file    line_sensor.c
 * @brief   八路红外巡线传感器 — GPIO 直读 + 权重法
 *          X1..X8 对应 PB6,7,8,9,10,11,14,19
 *          传感器值: 0 = 检测到黑线(命中), 1 = 白色/无线
 *          权重: -7,-5,-3,-1,+1,+3,+5,+7
 *          e_line = Σ(命中权重) / 命中数
 *          e_line<0 黑线偏左, e_line>0 黑线偏右
 */

#include "line_sensor.h"
#include "ti_msp_dl_config.h"

/* ================================================================
 * 硬件引脚定义
 * ================================================================ */

#define XJ_RD(port, pin)  ((DL_GPIO_readPins(port, pin) == (pin)) ? 1 : 0)

typedef struct { GPIO_Regs *port; uint32_t pin; } xj_pin_t;

static const xj_pin_t xj_pins[8] = {
    { GPIOB, DL_GPIO_PIN_6  }, /* X1 */
    { GPIOB, DL_GPIO_PIN_7  }, /* X2 */
    { GPIOB, DL_GPIO_PIN_8  }, /* X3 */
    { GPIOB, DL_GPIO_PIN_9  }, /* X4 */
    { GPIOB, DL_GPIO_PIN_10 }, /* X5 */
    { GPIOB, DL_GPIO_PIN_11 }, /* X6 */
    { GPIOB, DL_GPIO_PIN_14 }, /* X7 */
    { GPIOB, DL_GPIO_PIN_19 }, /* X8 */
};

/* IOMUX 索引 (配置上拉必需) */
static const uint32_t xj_iomux[8] = {
    IOMUX_PINCM23, IOMUX_PINCM24, IOMUX_PINCM25, IOMUX_PINCM26,
    IOMUX_PINCM27, IOMUX_PINCM28, IOMUX_PINCM31, IOMUX_PINCM45,
};

/* 传感器权重: 从左到右 */
static const float xj_weight[8] = {
    -7.0f, -5.0f, -3.0f, -1.0f,   /* X1  X2  X3  X4 */
    +1.0f, +3.0f, +5.0f, +7.0f    /* X5  X6  X7  X8 */
};

/* ================================================================
 * 全局数据
 * ================================================================ */

LineSensor_t g_line;
static uint8_t track_bits = 0xFF;
static float   last_error = 0.0f;

/* ================================================================
 * 初始化
 * ================================================================ */

void LineSensor_Init(void)
{
    /* 只开内部上拉, 传感器开漏输出必需 (与 wheel_4 XJ_Init 一致) */
    for (int i = 0; i < 8; i++)
    {
        DL_GPIO_initDigitalInputFeatures(xj_iomux[i],
            DL_GPIO_INVERSION_DISABLE, DL_GPIO_RESISTOR_PULL_UP,
            DL_GPIO_HYSTERESIS_DISABLE, DL_GPIO_WAKEUP_DISABLE);
    }
    track_bits = 0xFF;
    g_line.error      = 0.0f;
    g_line.derivative = 0.0f;
    g_line.valid      = 0;
    last_error        = 0.0f;
}

/* ================================================================
 * 读取 8 路传感器
 * ================================================================ */

void LineSensor_Update(void)
{
    uint8_t d = 0;
    for (int i = 0; i < 8; i++)
    {
        if (XJ_RD(xj_pins[i].port, xj_pins[i].pin))
            d |= (1 << (7 - i));
    }
    track_bits = d;

    /* 权重法: e_line = Σ(命中权重) / 命中数 */
    float sum = 0.0f, weighted = 0.0f;
    for (uint8_t i = 0; i < 8; i++)
    {
        /* bit 0 = 检测到黑线 (命中) */
        if (((d >> (7 - i)) & 1) == 0)
        {
            weighted += xj_weight[i];
            sum += 1.0f;
        }
    }

    if (sum == 0.0f)
    {
        /* 全白 = 丢线 */
        g_line.valid      = 0;
        g_line.derivative = 0.0f;
        /* 保持 last_error 不变, 用于判断丢线方向 */
    }
    else if (sum == 8.0f)
    {
        /* 全黑 = 十字路口或异常, 视为居中 */
        g_line.valid      = 1;
        g_line.error      = 0.0f;
        g_line.derivative = 0.0f;
        last_error        = 0.0f;
    }
    else
    {
        float err = weighted / sum;  /* e_line<0 偏左, e_line>0 偏右, 范围 ±7 */
        g_line.valid      = 1;
        g_line.derivative = err - last_error;
        g_line.error      = err;
        last_error        = err;
    }
}

/* ================================================================
 * 调试接口
 * ================================================================ */

uint8_t LineSensor_GetChannel(uint8_t index)
{
    return (index > 7) ? 1 : ((track_bits >> (7 - index)) & 1);
}

uint8_t LineSensor_GetAllChannels(void)
{
    return track_bits;
}
