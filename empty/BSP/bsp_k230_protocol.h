#ifndef _BSP_K230_PROTOCOL_H
#define _BSP_K230_PROTOCOL_H

#include "board.h"

/*
 * K230 二进制位置帧协议解析 (v2 — 双速度)
 * ==================================
 *
 * 帧格式 (15 字节, 小端):
 * ┌──────┬──────┬──────┬──────┬─────────┬─────────┬──────────┬──────────┬──────┬──────┬──────┐
 * │ 0xAA │ 0x55 │ 0x0B │ SEQ  │ T_MS LE │ X_MM LE │ V_AB  LE │ V_DF  LE │ CONF │FLAGS │ CRC8 │
 * └──────┴──────┴──────┴──────┴─────────┴─────────┴──────────┴──────────┴──────┴──────┴──────┘
 *
 * 字段:
 *   SOF1=0xAA, SOF2=0x55: 帧头
 *   LEN=0x0B: SEQ~FLAGS 共 11 字节
 *   SEQ: 帧序号 0-255
 *   T_MS: uint16 LE, K230 时间戳 (ms), 65.5s 回绕
 *   X_MM: int16 LE, 钢球位置 (mm), 中心O=0, 执行端为正
 *   V_AB: int16 LE, alpha-beta 滤波速度 (mm/s) — 平滑但有滞后
 *   V_DF: int16 LE, 帧间差分速度 (mm/s) — 零滞后但有噪声
 *   CONF: uint8, 置信度 0-100
 *   FLAGS: uint8, bit0=VALID, bit1=LOST, bit2=CAL_OK
 *   CRC8: 从 LEN 到 FLAGS 共 12 字节计算
 *
 * 解析策略:
 *   UART 中断逐字节喂入 Pto_Data_Receive()
 *   状态机: SOF1 → SOF2 → LEN → 接收body(11字节) → CRC
 *   CRC 错误丢帧; 主循环从 Pto_Loop() 提取最新帧
 */

/* 协议常量 */
#define PTO_SOF1            0xAA
#define PTO_SOF2            0x55
#define PTO_LEN_VAL         0x0B
#define PTO_FRAME_TOTAL     15   /* 帧总长 */
#define PTO_BODY_LEN        11   /* SEQ~FLAGS 共 11 字节 */
#define PTO_CRC_LEN         12   /* LEN~FLAGS 共 12 字节 */

/* FLAGS 位定义 */
#define FLAG_VALID    0x01
#define FLAG_LOST     0x02
#define FLAG_CAL_OK   0x04

/* 超时判断 (ms) */
#define PTO_VISION_TIMEOUT_MS  100

/* 钢球位置数据结构 */
typedef struct {
    int16_t  x_mm;         /* 钢球位置 (mm), 中心0, 执行端为正 */
    int16_t  v_ab_mm_s;    /* alpha-beta 滤波速度 (mm/s) — 平滑但有滞后 */
    int16_t  v_df_mm_s;    /* 帧间差分速度 (mm/s) — 零滞后但有噪声 */
    uint16_t timestamp_ms; /* K230 时间戳 */
    uint8_t  confidence;   /* 置信度 0-100 */
    uint8_t  flags;        /* 状态标志 */
    uint8_t  seq;          /* 帧序号 */
    uint32_t rx_local_ms;  /* MSPM0 接收时间戳 (ms) */
    uint8_t  fresh;        /* 1=有新帧, 0=已读 */
} BallVision_t;

/* 解析状态 */
typedef enum {
    PARSE_WAIT_SOF1 = 0,
    PARSE_WAIT_SOF2,
    PARSE_WAIT_LEN,
    PARSE_RECV_BODY,
    PARSE_WAIT_CRC
} ParseState_t;

/* 全局钢球位置数据 (供上层读取) */
extern BallVision_t g_ball_vision;

/* 逐字节喂入 (UART 中断调用) */
void Pto_Data_Receive(uint8_t byte);

/* 主循环调用: 检查是否有完整帧, 更新 g_ball_vision */
void Pto_Loop(void);

/* 读取最新位置数据 (返回 1=有新数据) */
uint8_t BallVision_Read(BallVision_t *out);

/* 判断视觉是否超时 (返回 1=超时, 0=正常) */
uint8_t BallVision_IsTimeout(uint32_t current_ms);

/* 获取当前帧年龄 (ms) */
uint32_t BallVision_GetAge(uint32_t current_ms);

#endif /* _BSP_K230_PROTOCOL_H */
