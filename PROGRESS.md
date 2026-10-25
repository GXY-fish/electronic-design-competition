# K230 钢球测速串口传回 — 当前进度与交接文档

> 更新时间: 2026-07-30 (v2)  
> 用途: 上下文过长，换窗口继续时直接读本文件恢复上下文

---

## 一、项目背景

**赛题**: 2026 电赛 H 题 — 车载平衡滚球运动控制系统  
**分工**: 视觉组（K230）只负责钢球检测 + 位置/速度计算 + UART 传回  
**队友**: PID 控制组用天猛星 MSPM0G3507 做水管 PID，他们需要我们传的速度数据

**架构边界**: K230 只管"看球和传数据"，MSPM0 负责"全部控制"。UART 有线传输，Wi-Fi 只传视频不进控制闭环。

---

## 二、已完成的工作

### 2.1 K230 端 (`要求2/K230/main.py`)

**当前版本**: PipeLine 架构（和 `steel_ball_detect.py` 一致），已验证可跑

**功能清单**:
- ✅ YOLO 钢球检测 (DetectionApp, 320×320 输入, conf_thresh=0.4)
- ✅ 像素→毫米标定框架 (`calibrate.py` + `calibration.json`，当前未标定用默认值)
- ✅ alpha-beta 速度滤波 (alpha=0.75, beta=0.10)
- ✅ 13 字节二进制 UART 帧发送 (帧头 0xAA 0x55, CRC8 校验)
- ✅ WiFi AP 启动 (SSID=K230_H, 密码=12345678)
- ✅ IDE 预览 + OSD 叠加检测框/位置/速度/置信度
- ✅ `os.exitpoint()` 可以正常停止脚本
- ✅ 尺寸过滤 (检测框 10-100px，排除噪点和反光)
- ✅ 位置限幅 ±120mm，速度限幅 ±1500mm/s

**关键参数**:
```
UART_BAUD = 115200  (已从 460800 改回，匹配 MSPM0 SysConfig)
RGB888P_SIZE = [640, 480]
DISPLAY_MODE = "st7701"
ALPHA = 0.75, BETA = 0.10
CONF_MIN = 50 (低于此值滤波器只预测不修正)
LOST_TIMEOUT_MS = 200
```

**UART 帧格式 (13 字节)**:
```
[0xAA][0x55][0x09][SEQ][T_MS_L][T_MS_H][X_MM_L][X_MM_H][V_MM_S_L][V_MM_S_H][CONF][FLAGS][CRC8]
FLAGS: bit0=VALID, bit1=LOST, bit2=CAL_OK
```

**已解决的固件兼容问题**:
1. WiFi AP: `essid`/`password` → `ssid`/`key`（K230 固件特有）
2. `active(True)` 报错 → try/except 忽略
3. `import _thread` 缺失 → 已加
4. RTSP Encoder API: 此固件不传 `venc_chn`（`SetOutBufs(8,w,h)`, `Create(attr)`, `Start()`, `GetStream(sd,timeout)`, `ReleaseStream(sd)`）
5. RTSP 从手动喂帧改为 auto-link（基于 `main0.py` 已验证写法）
6. 但 RTSP auto-link 导致 IDE 预览黑屏（无 Display.show_image），所以**暂时回退到 PipeLine 架构，RTSP 去掉了**

### 2.2 MSPM0 端 (`要求2/MSPM0/`)

**文件**:
- `bsp_k230_protocol.h` — 二进制帧解析器头文件（BallVision_t 结构体）
- `bsp_k230_protocol.c` — 逐字节状态机解析 + CRC8 校验
- `test_main.c` — 串口测试程序 v2（**无 printf 版**，UART3 接收 → 解析 → UART0/CH340 打印）

**已验证**:
- ✅ 编译成功（天猛星 `build.py`）
- ✅ 烧录成功（J-Link `flash.py`）
- ✅ **程序稳定运行（无 HardFault，串口数据正常输出）**
- ✅ K230 → MSPM0 UART 数据正确传输
- ✅ 实测 33fps，SEQ 连续无丢帧
- ✅ 数据格式: `[帧号] seq=序号 x=位置mm v=速度mm/s conf=置信度 flags=标志 fps=帧率`

### 2.3 PC 端测试脚本 (`要求2/serial_test.py`)

- Python 脚本读取 CH340 串口输出
- 解析 MSPM0 打印的文本行（v2 格式：mm 单位，十进制 flags）
- 统计帧率/丢帧/位置抖动/速度
- 已更新匹配无 printf 固件输出格式，**可测试**

### 2.4 模型文件

已在 K230 SD 卡 `/sdcard/kmodel/`:
- `best_AnchorBaseDet_can2_5_s_20260726145328.kmodel` ✅
- `deploy_config.json` ✅  
- `calibration.json` ✅ (未标定模板)

---

## 三、已解决的问题

### 3.1 MSPM0 printf 栈溢出 HardFault ✅ 已解决

**现象**: MSPM0 烧录后用 `%d` 格式 printf，串口无任何输出（连启动 banner 都没有）。

**根因**: **栈溢出导致 HardFault**。`device_linker.cmd` 默认 `--stack_size=512`，ti-clang 的 printf 内部需要 200-400 字节栈，加上 main() 局部变量，总栈使用超过 512 字节 → 栈溢出 → CFSR 报 `MUNSTKERR | BUNSTKERR | IBUSERR` → HardFault。

**诊断过程**:
1. `jlink_debug.py fault` → CFSR = `MUNSTKERR | BFARVALID | BUNSTKERR | BIMPRECISEERR | IBUSERR`
2. `jlink_debug.py regs` → SP=0x20207FB8 (距栈顶仅 72 字节)
3. 确认是栈溢出

**修复方案**: **完全绕过 printf**，改用 `uart0_send_string()` + 自定义 `print_int()` 函数:
- `print_int()` 栈使用仅 ~32 字节（buf[12] + 4 局部变量）
- 对比 printf 的 200-400 字节，彻底消除栈溢出风险
- LED (PB22) 每秒闪烁作为程序存活指示
- 输出格式: `[帧号] seq=序号 x=位置mm v=速度mm/s conf=置信度 flags=标志 fps=帧率`

**注意**: `device_linker.cmd` 的 `--stack_size` 改为 2048 后会被 build.py 重新生成为 512。但由于绕过了 printf，512 字节足够（实际使用 ~82 字节）。

### 3.2 RTSP 视频推流（暂缓）

**问题**: PipeLine 架构有 IDE 预览但无法同时做 RTSP。dual-channel + auto-link 架构能做 RTSP 但 IDE 预览黑屏。

**方案（待实现）**: 
- 用 PipeLine 做检测 + 显示
- 在 PipeLine 的 sensor 上额外配置一个通道做 RTSP
- 或者分开跑两个脚本（检测脚本 + 独立 RTSP 脚本）

### 3.3 帧率 33fps（低于老师 50Hz 要求）

PipeLine 单通道 640×480 实测 33fps。老师要求 ≥40Hz。
- 当前 33fps 对静态测试够用
- 最终比赛可能需要提高（降低分辨率或用 dual-channel）

---

## 四、05 工程的临时修改状态

为了编译测试，对 `05.K230_SteelBall_Tracker/MSPM0_ServoTracker` 做了临时修改:
1. `APP/task_tracker.c` → 重命名为 `.bak`
2. `APP/tracker_core.c` → 重命名为 `.bak`
3. `BSP/bsp_servo.c` → 重命名为 `.bak`
4. `BSP/bsp_key.c` → 重命名为 `.bak`
5. `BSP/bsp_k230_protocol.c/.h` → 替换为二进制协议版本
6. `main.c` → 替换为 `test_main.c` (v2 无 printf 版)
7. `ticlang/makefile` → build.py 每次重新生成，改名后的 .bak 文件不会被编译

**注意**: 用户说会 re-clone 05 文件夹，所以这些临时修改不影响原始工程。最终交付应在 `要求2/` 里建独立工程。

**路径映射**: 工作区 `c:\Users\沈炎龙\Desktop\K230_Visual Measure\` 实际映射到 `E:\Obsidian_Hub\Quick Mark\K230学习资料_C题专用版\`。build.py 和 flash.py 使用映射后的路径。

---

## 五、后续任务

### 5.1 必须完成

1. ~~**修好 MSPM0 printf**~~ ✅ 已解决（绕过 printf，用自定义 print_int）
2. **串口测试** — 用 `serial_test.py` 验证:
   - ✅ 帧率稳定性（实测 33fps ≥ 25Hz）
   - ✅ SEQ 连续无丢帧
   - ✅ 速度数据合理（球不动 v=0mm/s）
   - ⬜ 位置数据合理（球放中间 x≈0mm，当前 x=120mm 因为球在边缘 + 未标定）
   - ⬜ CRC 无错（需 serial_test.py 长时间运行验证）
3. **标定** — 跑 `auto_setup.py` 一键标定（焦距+ROI+位置）
4. **最终交付包** — 在 `要求2/` 里建独立的 MSPM0 工程（不依赖 05 文件夹）

### 5.2 应该完成

5. **RTSP 视频推流** — 恢复无线图传功能（要求 1 的内容）
6. **帧率提升** — 从 33fps 提到 40Hz+（可能需要 dual-channel 或降分辨率）
7. ~~**固定曝光/白平衡**~~ ✅ 已实现 (main.py 中 auto_exposure(False) + exposure())

### 5.3 新增 — 摄像头标定体系 ✅ 已实现

**一键标定脚本**: `auto_setup.py` — 焦距+ROI+位置三合一

**三个阶段**:
1. Phase 1: ROI 检测 — 球放管子上, 自动确定白管区域 Y 范围
2. Phase 2: 智能对焦 — 粗扫+精扫, 评分=置信度×检测率, 自动找最佳焦距
3. Phase 3: 位置标定 — ±5cm 五点标定 (与 calibrate.py 一致)

**生成的配置文件**:
- `camera_config.json` — 焦距位置 + ROI 范围 (main.py 自动加载)
- `calibration.json` — 像素→毫米标定 (main.py 自动加载)

**main.py 中的集成**:
- `load_camera_config()` — 启动时加载 camera_config.json
- `apply_roi_mask()` — 每帧 get_frame() 后, 上下区域填零
- ROI 软过滤 — 检测中心 Y 超出 ROI 的检测直接丢弃
- OSD 画品红横线标示 ROI 范围

**标定时机**:
- 摄像头/水管位置不变 → 焦距+ROI 一劳永逸, 不用重标
- 换球/调水管 → 重跑 auto_setup.py
- 仅位置不准 → 可单独跑 calibrate.py (但建议一起跑, 因为焦距影响检测精度)

### 5.3 锦上添花

8. **MSPM0→K230 状态回传** — 10Hz 状态帧（mode/x_ref/elapsed_ms），用于视频 OSD
9. **软关联逻辑** — 如果误检横跳严重，加"降低远处检测置信度"而非硬拒
10. **LED 补光** — 摄像头两侧柔和白光，提升检测稳定性

### 5.4 约束参数记录

当前生效的约束:
```
ALPHA = 0.75, BETA = 0.10     (alpha-beta 滤波)
CONF_MIN = 50                  (低于此值只预测)
X_MAX = 120mm                  (位置限幅)
V_MAX = 1500mm/s               (速度限幅)
LOST_TIMEOUT_MS = 200          (丢球超时)
MIN_BOX_W/H = 10, MAX_BOX_W/H = 100  (尺寸过滤)
```

已移除的约束（留备注）:
```
# MAX_JUMP_PX = 250  (最近邻关联，已移除——会误拒快速移动)
# REACQUIRE_FRAMES = 10 (重搜索，随关联一起移除)
```

---

## 六、关键文件路径

| 文件 | 路径 | 说明 |
|------|------|------|
| K230 主程序 | `要求2：K230钢球测速串口传回/K230/main.py` | 当前运行版本 (含对焦+ROI+曝光) |
| K230 一键标定 | `要求2：K230钢球测速串口传回/K230/auto_setup.py` | 焦距+ROI+位置三合一标定 |
| K230 焦距标定 | `要求2：K230钢球测速串口传回/K230/focus_calibrate.py` | 焦距+ROI (被 auto_setup.py 取代, 保留备用) |
| K230 位置标定 | `要求2：K230钢球测速串口传回/K230/calibrate.py` | 仅位置标定 (±5cm 五点) |
| K230 摄像头配置 | `要求2：K230钢球测速串口传回/K230/camera_config.json` | 焦距+ROI (标定后生成) |
| K230 标定参数 | `要求2：K230钢球测速串口传回/K230/calibration.json` | 像素→毫米 (标定后生成) |
| MSPM0 协议头文件 | `要求2：K230钢球测速串口传回/MSPM0/bsp_k230_protocol.h` | 二进制帧定义 |
| MSPM0 协议源文件 | `要求2：K230钢球测速串口传回/MSPM0/bsp_k230_protocol.c` | 状态机解析 |
| MSPM0 测试主程序 | `要求2：K230钢球测速串口传回/MSPM0/test_main.c` | 串口测试 v2 (无 printf) |
| PC 测试脚本 | `要求2：K230钢球测速串口传回/serial_test.py` | 帧率/CRC 统计 v2 |
| 参考工程(05) | `05.K230_SteelBall_Tracker/MSPM0_ServoTracker/` | 临时改了做编译测试 |
| 参考图传代码 | `要求1：无线图传实时与回放/main0.py` | 已验证的 RTSP 写法 |
| 老师分工手册 | `00.题目与分工/H题_车载平衡滚球系统_任务拆解与实施手册_K230版.md` | 完整要求 |

---

## 七、天猛星工具链

```
编译: python C:\Users\沈炎龙\.copilot\skills\mspm0kit-tianmengxing\scripts\build.py <项目路径> --yes
烧录: python C:\Users\沈炎龙\.copilot\skills\mspm0kit-tianmengxing\scripts\flash.py <项目路径>
串口: python C:\Users\沈炎龙\.copilot\skills\mspm0kit-tianmengxing\scripts\serial_console.py COM5 -b 115200 -d <秒数>
调试: python C:\Users\沈炎龙\.copilot\skills\mspm0kit-tianmengxing\scripts\jlink_debug.py reset/fault/regs/pc
```

CH340 串口: **COM5** @ 115200  
J-Link: 已连接，禁止用 ST-Link（会锁 MSPM0 芯片）

SDK 路径: `E:\TI\CCStudio\mspm0_sdk_2_11_00_07`  
编译器: `E:\TI\CCStudio\ccs\tools\compiler\ti-cgt-armllvm_4.0.4.LTS`

---

## 八、实测数据 (2026-07-30)

串口监控 8 秒采样:
```
[830] seq=239 x=120mm v=0mm/s conf=86 flags=1 fps=33
[831] seq=240 x=120mm v=0mm/s conf=86 flags=1 fps=33
...
[847] seq=0   x=120mm v=0mm/s conf=86 flags=1 fps=33  (SEQ 255→0 回绕正常)
...
--- STATS: total=851 fps=33 ---
--- STATS: total=916 fps=33 ---
--- STATS: total=981 fps=33 ---
```

**结论**:
- K230 → MSPM0 UART 通信完全正常
- 33fps 稳定，无丢帧
- x=120mm 表示球在边缘（未标定，默认 5mm/像素，球偏中心 24px → 120mm）
- v=0mm/s 球不动，速度正确
- conf=86 置信度良好
- flags=1 (FLAG_VALID) 检测有效
