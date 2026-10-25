/**
 * @file    key.c
 * @brief   2×2 矩阵键盘 — 逐行扫描 + 消抖
 *
 *          PB20(C1) PB25(C2)
 *   PA14(R1)  KEY1    KEY2
 *   PA16(R2)  KEY3    KEY4
 */
#include "key.h"
#include "ti_msp_dl_config.h"

/* 行 (输出) */
#define R1_PORT  GPIOA
#define R1_PIN   DL_GPIO_PIN_14
#define R2_PORT  GPIOA
#define R2_PIN   DL_GPIO_PIN_16

/* 列 (输入,上拉) */
#define COL_PORT GPIOB
#define C1_PIN   DL_GPIO_PIN_20
#define C2_PIN   DL_GPIO_PIN_25

static uint8_t key_state[4], key_cnt[4], key_edge[4], key_edge_ack[4];
#define DEBOUNCE_MS 3

void Key_Init(void)
{
    DL_GPIO_initDigitalInputFeatures(IOMUX_PINCM46,  /* PB20 */
        DL_GPIO_INVERSION_DISABLE, DL_GPIO_RESISTOR_PULL_UP,
        DL_GPIO_HYSTERESIS_DISABLE, DL_GPIO_WAKEUP_DISABLE);
    DL_GPIO_initDigitalInputFeatures(IOMUX_PINCM53,  /* PB25 */
        DL_GPIO_INVERSION_DISABLE, DL_GPIO_RESISTOR_PULL_UP,
        DL_GPIO_HYSTERESIS_DISABLE, DL_GPIO_WAKEUP_DISABLE);

    DL_GPIO_initDigitalOutput(IOMUX_PINCM36);  /* PA14 */
    DL_GPIO_initDigitalOutput(IOMUX_PINCM38);  /* PA16 */
    DL_GPIO_setPins(R1_PORT, R1_PIN);
    DL_GPIO_setPins(R2_PORT, R2_PIN);

    for (int i = 0; i < 4; i++)
        key_state[i] = 1, key_cnt[i] = 0, key_edge[i] = 0, key_edge_ack[i] = 0;
}

void Key_Scan(void)
{
    uint32_t col_pins[2] = { C1_PIN, C2_PIN };
    uint8_t raw[4];

    for (int r = 0; r < 2; r++) {
        DL_GPIO_clearPins((r == 0) ? R1_PORT : R2_PORT,
                          (r == 0) ? R1_PIN  : R2_PIN);
        DL_GPIO_setPins((r == 1) ? R1_PORT : R2_PORT,
                        (r == 1) ? R1_PIN  : R2_PIN);
        for (volatile int d = 0; d < 20; d++);
        for (int c = 0; c < 2; c++) {
            raw[r * 2 + c] = (DL_GPIO_readPins(COL_PORT, col_pins[c])
                              == col_pins[c]) ? 1 : 0;
        }
    }
    DL_GPIO_setPins(R1_PORT, R1_PIN);
    DL_GPIO_setPins(R2_PORT, R2_PIN);

    for (int i = 0; i < 4; i++) {
        if (raw[i] != key_state[i]) {
            if (++key_cnt[i] >= DEBOUNCE_MS)
                key_state[i] = raw[i], key_cnt[i] = 0,
                (raw[i] == 0) ? (key_edge[i] = 1) : 0;
        } else key_cnt[i] = 0;
    }
}

uint8_t Key_Pressed(uint8_t id)
{
    if (id > 3) return 0;
    if (key_edge[id] && !key_edge_ack[id])
        return key_edge_ack[id] = 1, 1;
    if (key_state[id] == 1) key_edge_ack[id] = 0;
    return 0;
}
