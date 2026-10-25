# 要求2：K230 钢球测速串口传回

> **2026 电赛 H 题 — 视觉组（学生B）**  
> K230 检测钢球位置 → alpha-beta 滤波测速 → UART 二进制帧传给 MSPM0  
> MSPM0 队友拿 `x_mm` 和 `v_mm_s` 做水管 PID 控制

---

## 一、职责边界

```
┌─────────────────────────────────────────────────────┐
│                  K230 (视觉组负责)                    │
│                                                     │
│  摄像头 → YOLO检测 → 像素→毫米标定 → alpha-beta滤波  │
│                                          ↓           │
│              13字节二进制UART帧 (50Hz) ──────────────→ │
│              (x_mm, v_mm_s, confidence, flags)       │
└─────────────────────────────────────────────────────┘
                          ↓ UART 460800
┌─────────────────────────────────────────────────────┐
│              MSPM0 (队友负责, 本文件夹只提供协议层)     │
│                                                     │
│  UART3中断 → Pto_Data_Receive() → 状态机解析          │
│  主循环 → Pto_Loop() → BallVision_Read()              │
│       ↓                                             │
│  g_ball_vision.x_mm  → PID 误差输入                   │
│  g_ball_vision.v_mm_s → PID 微分输入                  │
└─────────────────────────────────────────────────────┘
```

**视觉组只管到 UART 发出去为止。** 舵机控制、PID、底盘循迹都是队友的事。

---

## 二、文件夹结构

```
要求2：K230钢球测速串口传回/
├── K230/                          # ← 视觉组部署到 K230
│   ├── main.py                    # 主脚本: 检测+标定+滤波+UART+RTSP
│   ├── calibrate.py               # 5点标定工具
│   └── calibration.json          # 标定参数 (标定前是模板)
│
├── MSPM0/                         # ← 队友集成到 MSPM0 工程
│   ├── bsp_k230_protocol.h        # 协议头文件 (BallVision_t 结构体)
│   ├── bsp_k230_protocol.c        # 协议解析实现 (CRC8+状态机)
│   └── main_example.c            # 集成示例 (给队友看怎么用)
│
└── README.md                       # 本文件
```

---

## 三、K230 端 (视觉组)

### 3.1 `main.py` — 主脚本

基于 GitHub V2 版 `steel_ball_detect.py` 改造，保留 PipeLine + DetectionApp 检测核心，新增：

| 新增功能 | 说明 |
|---------|------|
| 像素→毫米标定 | 5点线性拟合，从 `calibration.json` 读取 |
| alpha-beta 滤波 | 输出平滑位置 `x_mm` + 速度 `v_mm_s` |
| 二进制 UART 帧 | 13字节，CRC8校验，替代原来的 ASCII `$XX,14,...#` |
| WiFi AP + RTSP | 双通道传感器，同时做检测和视频推流（服务要求1） |

**与 V2 `steel_ball_detect.py` 的对应关系：**

| V2 原版 | main.py 改造后 |
|---------|---------------|
| `PipeLine` + `DetectionApp` | 保留，改为双通道传感器 |
| `YbProtocol.get_object_detect_data()` → ASCII | `pack_ball_frame()` → 13字节二进制 |
| `uart.send(pto_data)` | `uart_send(pack_ball_frame(...))` |
| 画框 `pl.osd_img.draw_rectangle()` | 保留，改为画在 YUV 帧上 |
| 无标定 | 新增 `pixel_to_mm()` |
| 无滤波 | 新增 `AlphaBetaFilter` |
| 无 RTSP | 新增 `RtspManager` (子线程推流) |

### 3.2 `calibrate.py` — 标定工具

用 PipeLine + DetectionApp（和 V2 一样的单通道方式），5点标定：
- 把球放在 -10/-5/0/+5/+10 cm
- 每点采 50 帧，取中位数
- 最小二乘拟合 `x_mm = scale × pixel + offset`
- 自动保存 `calibration.json`

### 3.3 部署步骤

```
1. 拷贝到 K230 SD 卡 /sdcard/kmodel/:
   - best_AnchorBaseDet_can2_5_s_20260726145328.kmodel  (来自 03.K230_YOLOModel/models/Pro-Hmf/)
   - deploy_config.json                                   (同上)
   - calibration.json                                    (先放模板, 标定后覆盖)

2. 先运行 calibrate.py 做 5 点标定

3. 再运行 main.py:
   → WiFi AP 启动 (SSID=K230_H)
   → RTSP 服务器启动 (端口 2004)
   → 主循环: 检测→标定→滤波→UART (50Hz)
   → 子线程: RTSP 推流
```

---

## 四、MSPM0 端 (给队友集成)

### 4.1 队友需要做什么

```
1. 把 bsp_k230_protocol.c 和 bsp_k230_protocol.h 拷到工程的 BSP/ 目录

2. 确保 UART3 RX 中断里调用 Pto_Data_Receive():
   (如果队友的 bsp_uart.c 里 UART3 中断已经有了就不用改)

   void UART_3_INST_IRQHandler(void) {
       uint8_t received = DL_UART_Main_receiveData(UART_3_INST);
       Pto_Data_Receive(received);   // ← 加这一行
   }

3. 主循环调用 Pto_Loop() 和 BallVision_Read():

   while (1) {
       Pto_Loop();

       BallVision_t ball;
       if (BallVision_Read(&ball)) {
           // ball.x_mm   → 位置 (mm), 中心O=0, 执行端为正
           // ball.v_mm_s → 速度 (mm/s)
           // ball.confidence → 置信度 0-100
           // ball.flags → bit0=VALID, bit1=LOST

           // 喂给 PID: pid_update(ball.x_mm, ball.v_mm_s);
       }

       if (BallVision_IsTimeout(sys_tick_ms)) {
           // K230 断连或丢球超时, 安全停车
       }
   }
```

### 4.2 `main_example.c` — 集成示例

完整的最小示例，队友可以直接参考。包含：
- UART 初始化 + RX 中断开启
- 主循环调用 `Pto_Loop()` + `BallVision_Read()`
- 串口打印位置和速度
- 超时检查

### 4.3 不需要的模块（已剔除）

| 模块 | 原因 |
|------|------|
| `bsp_servo.c/.h` | 舵机队友有自己的代码 |
| `bsp_key.c/.h` | 按键队友按需加 |
| `tracker_core.c/.h` | 云台 PID 追踪，H题不需要 |
| `task_tracker.c/.h` | 任务编排，队友自己写 |
| `bsp_ldc1614.c/.h` | 电感传感器，已改用摄像头 |
| `bsp_electromagnet.c/.h` | 电磁铁，H题不需要 |

---

## 五、UART 二进制帧协议 (v1)

```
帧总长 13 字节, 50Hz, 小端

┌──────┬──────┬──────┬──────┬─────────┬─────────┬──────────┬──────┬──────┬──────┐
│ 0xAA │ 0x55 │ 0x09 │ SEQ  │ T_MS LE │ X_MM LE │ V_MM_S LE│ CONF │FLAGS │ CRC8 │
└──────┴──────┴──────┴──────┴─────────┴─────────┴──────────┴──────┴──────┴──────┘
```

| 字节 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 0-1 | SOF | 0xAA 0x55 | 帧头 |
| 2 | LEN | 0x09 | SEQ~FLAGS 共9字节 |
| 3 | SEQ | uint8 | 帧序号 0-255 |
| 4-5 | T_MS | uint16 LE | K230 时间戳 (ms) |
| 6-7 | **X_MM** | **int16 LE** | **位置 (mm), 中心O=0, 执行端为正** |
| 8-9 | **V_MM_S** | **int16 LE** | **速度 (mm/s)** |
| 10 | CONF | uint8 | 置信度 0-100 |
| 11 | FLAGS | uint8 | bit0=VALID, bit1=LOST, bit2=CAL_OK |
| 12 | CRC8 | uint8 | LEN~FLAGS 共10字节 |

**波特率**：460800（不稳定时退到 115200，改 main.py 里 `UART_BAUD`）

---

## 六、硬件接线

### K230 ↔ MSPM0 (UART)

| K230 | MSPM0 | 说明 |
|------|-------|------|
| TXD (IO9) | PA25 | K230 TX → MSPM0 UART3 RX |
| RXD (IO10) | PA26 | MSPM0 UART3 TX → K230 RX |
| GND | GND | 共地 |

### K230 WiFi (RTSP, 服务于要求1)

- K230 启动为热点：SSID=`K230_H`，密码=`12345678`
- RTSP：`rtsp://<K230_IP>:2004/VisionCarStream`
- 接收端用 `要求1` 文件夹的 `receiver.py`

---

## 七、关键参数速查

| 参数 | 值 | 在哪改 |
|------|-----|--------|
| WiFi SSID | `K230_H` | main.py |
| WiFi 密码 | `12345678` | main.py |
| RTSP 端口 | `2004` | main.py + receiver.py |
| RTSP session | `VisionCarStream` | main.py + receiver.py |
| UART 波特率 | `460800` | main.py + MSPM0 SysConfig |
| 滤波 alpha | `0.75` | main.py |
| 滤波 beta | `0.10` | main.py |
| 置信度阈值 | `0.4` | deploy_config.json |
| 视觉超时 | `100ms` | bsp_k230_protocol.h |
| 速度限幅 | `±1500 mm/s` | main.py |
| 位置限幅 | `±120 mm` | main.py |

---

## 八、模型文件（需单独拷贝）

来自 `03.K230_YOLOModel/models/Pro-Hmf/`：

| 文件 | 拷贝到 |
|------|--------|
| `best_AnchorBaseDet_can2_5_s_20260726145328.kmodel` | `/sdcard/kmodel/` |
| `deploy_config.json` | `/sdcard/kmodel/` |

---

## 九、与 GitHub V2 原版的对应关系

本文件夹的 `main.py` 基于 GitHub 仓库 `SYIlony/K230-----_C----` 的 V2 提交
（commit `2b41962`, "PD优化+阈值保护-v2"）改造：

| GitHub V2 文件 | 本文件夹对应 | 状态 |
|---------------|------------|------|
| `K230/steel_ball_detect.py` | `K230/main.py` | 改造：加标定+滤波+二进制UART+RTSP |
| `MSPM0_ServoTracker/BSP/bsp_k230_protocol.c/.h` | `MSPM0/bsp_k230_protocol.c/.h` | 替换：ASCII→二进制 |
| `MSPM0_ServoTracker/BSP/bsp_servo.c/.h` | — | 删除：队友自己有 |
| `MSP0_ServoTracker/BSP/bsp_key.c/.h` | — | 删除：不需要 |
| `MSPM0_ServoTracker/APP/tracker_core.c/.h` | — | 删除：H题不追踪 |
| `MSPM0_ServoTracker/APP/task_tracker.c/.h` | — | 删除：队友自己写 |
| `MSPM0_ServoTracker/Board/board.c/.h` | — | 删除：队友工程自带 |
| `MSPM0_ServoTracker/main.c` | `MSPM0/main_example.c` | 替换：简化为集成示例 |
