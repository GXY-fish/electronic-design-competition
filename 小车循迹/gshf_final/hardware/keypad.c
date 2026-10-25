/**
 * @file    keypad.c
 * @brief   4×4 矩阵键盘驱动实现 (多端口支持)
 *
 *          行 (输出): PB25, PA24, PA14, PA16
 *          列 (输入+上拉): PA22, PA2, PA26, PB21
 *
 *          工作原理:
 *          依次将 ROW1~ROW4 拉低, 同时读取 4 列 COL1~COL4 电平。
 *          某列读到低电平 → 交点上的按键被按下。
 *          需要连续 2 次扫描一致才确认 (20ms 消抖)。
 */

#include "keypad.h"
#include "ti_msp_dl_config.h"

/* ================================================================
 * 引脚描述结构体
 * ================================================================ */

typedef struct {
    GPIO_Regs *port;         /* GPIOA / GPIOB */
    uint32_t   pin;          /* DL_GPIO_PIN_x */
    uint32_t   iomux;        /* IOMUX_PINCMxx */
} kp_pin_t;

/* ================================================================
 * 行引脚 (输出, 扫描时依次拉低)
 * ================================================================ */

static const kp_pin_t kp_rows[4] = {
    { GPIOB, DL_GPIO_PIN_25, IOMUX_PINCM56 },  /* ROW1: PB25 */
    { GPIOA, DL_GPIO_PIN_24, IOMUX_PINCM54 },  /* ROW2: PA24 */
    { GPIOA, DL_GPIO_PIN_14, IOMUX_PINCM36 },  /* ROW3: PA14 */
    { GPIOA, DL_GPIO_PIN_16, IOMUX_PINCM38 },  /* ROW4: PA16 */
};

/* ================================================================
 * 列引脚 (输入, 内部上拉)
 * ================================================================ */

static const kp_pin_t kp_cols[4] = {
    { GPIOA, DL_GPIO_PIN_22, IOMUX_PINCM47 },  /* COL1: PA22 */
    { GPIOA, DL_GPIO_PIN_2,  IOMUX_PINCM7  },  /* COL2: PA2  */
    { GPIOA, DL_GPIO_PIN_26, IOMUX_PINCM59 },  /* COL3: PA26 */
    { GPIOB, DL_GPIO_PIN_21, IOMUX_PINCM49 },  /* COL4: PB21 */
};

/* ================================================================
 * 消抖状态
 * ================================================================ */

static uint8_t last_key           = KEYPAD_NO_KEY;
static volatile uint8_t stable_key = KEYPAD_NO_KEY;  /* ISR 写, 主循环读 */
static uint8_t db_cnt             = 0;
volatile uint8_t debug_raw        = 0;     /* 调试: 最近一次 raw 扫描值 */
volatile uint8_t debug_stable     = 0;     /* 调试: 消抖后的 stable_key */

/* ================================================================
 * 初始化 — 行输出高, 列输入上拉
 * ================================================================ */

void Keypad_Init(void)
{
    uint32_t i;

    /* 行: 输出, 初始拉高 (不扫描状态) */
    for (i = 0; i < 4; i++)
    {
        DL_GPIO_initDigitalOutput(kp_rows[i].iomux);
        DL_GPIO_setPins(kp_rows[i].port, kp_rows[i].pin);
        DL_GPIO_enableOutput(kp_rows[i].port, kp_rows[i].pin);
    }

    /* 列: 输入, 内部上拉 */
    for (i = 0; i < 4; i++)
    {
        DL_GPIO_initDigitalInputFeatures(kp_cols[i].iomux,
            DL_GPIO_INVERSION_DISABLE, DL_GPIO_RESISTOR_PULL_UP,
            DL_GPIO_HYSTERESIS_DISABLE, DL_GPIO_WAKEUP_DISABLE);
    }

    last_key   = KEYPAD_NO_KEY;
    stable_key = KEYPAD_NO_KEY;
    db_cnt     = 0;
}

/* ================================================================
 * 原始扫描 (不消抖): 返回键号 1~16, 0=无按键
 * 键号 = row * 4 + col + 1
 * ================================================================ */

static uint8_t Keypad_ScanRaw(void)
{
    uint8_t r, c;

    for (r = 0; r < 4; r++)
    {
        /* 当前行拉低 */
        DL_GPIO_clearPins(kp_rows[r].port, kp_rows[r].pin);

        /* 延时 2μs 让电平稳定 (原来 2 NOP 不够) */
        delay_cycles(64);

        /* 读取 4 列 */
        for (c = 0; c < 4; c++)
        {
            if (!DL_GPIO_readPins(kp_cols[c].port, kp_cols[c].pin))
            {
                /* 该列为低 → 交点按键按下 */
                DL_GPIO_setPins(kp_rows[r].port, kp_rows[r].pin);
                return (uint8_t)(r * 4 + c + 1);   /* key1 ~ key16 */
            }
        }

        /* 当前行恢复高 */
        DL_GPIO_setPins(kp_rows[r].port, kp_rows[r].pin);
    }

    return KEYPAD_NO_KEY;
}

/* ================================================================
 * 消抖扫描: 连续 2 次一致才确认
 * 调用频率: 10ms, 即消抖窗口 20ms
 * ================================================================ */

uint8_t Keypad_Scan(void)
{
    uint8_t raw = Keypad_ScanRaw();

    if (raw == last_key)
    {
        if (db_cnt < 2) db_cnt++;
        if (db_cnt == 2)
            stable_key = raw;
    }
    else
    {
        db_cnt = 0;
        last_key = raw;
    }

    if (raw == KEYPAD_NO_KEY && last_key == KEYPAD_NO_KEY)
    {
        if (db_cnt >= 2)
            stable_key = KEYPAD_NO_KEY;
    }

    debug_raw    = raw;
    debug_stable = stable_key;
    return stable_key;
}

/* ================================================================
 * 获取当前按键号 (1~16), 0=无按键
 * ================================================================ */

uint8_t Keypad_GetKey(void)
{
    return stable_key;
}

/* ================================================================
 * 简单状态查询
 * ================================================================ */

bool Keypad_IsPressed(void)
{
    return (stable_key != KEYPAD_NO_KEY);
}

/* ================================================================
 * 直接读取 (带消抖扫描 + 返回键值)
 * ================================================================ */

uint8_t Keypad_Read(void)
{
    Keypad_Scan();
    return stable_key;
}
