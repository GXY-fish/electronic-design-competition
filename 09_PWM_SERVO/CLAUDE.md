# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ball-balance control system on **TI MSPM0G3507** (Cortex-M0+, LaunchPad). A servo tilts a platform to move a ball through a vision-guided sequence: arrive at +50mm, then settle at -50mm. The vision system (K230 or similar) streams ball position over UART.

## Build & Flash

This is a **TI Code Composer Studio (CCS) Theia** project. Build and debug are done within CCS. The project uses the TI ARM Clang compiler (`ti-cgt-armllvm_4.0.4.LTS`).

- **SDK**: MSPM0 SDK 2.10+ (DriverLib) at `C:/TI/mspm0_sdk_2_10_00_04/source`
- **SysConfig**: `empty.syscfg` defines all peripheral/pin configuration. Generated output lands in `Debug/ti_msp_dl_config.c` and `Debug/ti_msp_dl_config.h`. Do not hand-edit these generated files.
- **Device define**: `__MSPM0G3507__`
- **Build output**: `Debug/01_LED.out` (the output name comes from CCS build config, not the project name)

No standalone Makefile or CMake — open the project in CCS Theia IDE to build.

## Peripheral Map (SysConfig-generated)

| Label | Peripheral | Pins | Purpose |
|-------|-----------|------|---------|
| `SERVO` | TIMG7 (PWM, edge-aligned up) | PA27 | Servo PWM — 100kHz timer clock, 20ms period (count=2000), compare defines pulse width |
| `PRINT` | UART1, 115200 bps, RX interrupt | PB7(RX), PB6(TX) | Vision data input from camera system |
| `OLED` | I2C1, 100 kHz | PB3(SDA), PB2(SCL) | OLED display (not used during competition control) |
| `xuanniu` | ADC1 channel 1 | PA16 | Potentiometer/knob ADC input |
| `LED` | GPIO | PA14, PA15 | Debug LEDs |
| `VREF` | Internal 2.5V | — | ADC reference |
| HFXT | External 40 MHz crystal | PA5, PA6 | SYSPLL → 80 MHz `CPUCLK_FREQ` |

## Architecture

### Data Flow

```
Vision Camera → UART1 RX ISR → VisionProtocol (frame parser)
                                    ↓
   BallBalanceApp_Update20ms() ← SysTick 20ms timer (1000 Hz SysTick, /20 divider)
        ├── VisionProtocol_GetLatest() → VisionMeasurement
        ├── BallTask_Update() → state machine (target switching)
        ├── BallControl_Update() → alpha-beta filter + PID → theta_cmd_deg
        └── ServoMap_AngleToPulse() → Platform_ServoWriteUs() → TIMG7 PWM
```

### Modules

**`ball_app.c` / `ball_app.h`** — Top-level application glue. Owns the static instances of all subsystems (`BallControl`, `BallTask`, `ServoMap`, `VisionProtocol`). Implements the 20ms control loop:
1. Waits in `BALL_TASK_IDLE` until first valid vision measurement
2. Starts the task state machine (targets → +50mm → -50mm)
3. Switches between two PID gain sets (Kp/Kd tuned separately for the + and - directions)
4. Tracks overshoot stats (`g_result_plus_max_mm`, `g_result_minus_min_mm`) for competition judging
5. Exports debug globals (`g_debug_*`) for live monitoring via debugger or serial

**`ball_control.c` / `ball_control.h`** — PID-like controller with alpha-beta position/velocity filter. Key behaviors:
- **Alpha-beta filter**: position estimate `x_est` and velocity estimate `v_est` fused from vision measurements. `alpha=0.65`, `beta=0.15` (auto-tuned for the 20ms cycle).
- **PID**: P on position error + D on estimated velocity + conditional I (anti-windup by position window, speed window, and saturation)
- **Output rate limiting**: `theta_step_per_20ms_deg` caps servo angle change per cycle
- **Slew-to-level**: when vision is lost or faulted, gradually returns servo to level (0°)

**`ball_task.c` / `ball_task.h`** — Finite state machine for the competition sequence:
- `IDLE` → `GO_PLUS_5` → `GO_MINUS_5` → `FINISHED` (or `FAULT`)
- Transitions use debounced condition-holds (position + velocity tolerances with configurable hold times)
- Fault conditions: vision timeout (100ms), ball out of bounds (±115mm), total task timeout (15s)
- `TASK_POSITION_SIGN` inverts all targets (set +1.0 or -1.0 based on mechanical orientation)

**`vision_protocol.c` / `vision_protocol.h`** — UART frame parser. Protocol:
- 15-byte frames: `[0xAA, 0x55, 0x0B, seq, cam_ts_lo, cam_ts_hi, x_lo, x_hi, v_lo, v_hi, v_diff_lo, v_diff_hi, confidence, flags, CRC8]`
- CRC-8 (poly=0x07) over bytes 2-13
- Positions are int16 in mm, scaled by `VISION_POSITION_SIGN`
- Valid frames require: CRC match, `VISION_MEASUREMENT_VALID` flag set, and confidence ≥ 35

**`servo_map.c` / `servo_map.h`** — Piecewise linear interpolation: maps angle (degrees) → PWM pulse width (µs). Configured with a 5-point calibration table. Angles outside the table clamp to the nearest endpoint.

**`uart.c` / `uart.h`** — UART TX helpers + RX ISR (`PRINT_INST_IRQHandler`). Every received byte is forwarded to `BallBalanceApp_OnUartRxByte()`.

**`platform_port.h`** — Hardware abstraction: `Platform_GetMillis()`, `Platform_ServoWriteUs()`, `Platform_DisplayResult()`.

### Key Constants (all in `ball_config.h`)

| Constant | Value | Meaning |
|----------|-------|---------|
| `BALL_CONTROL_PERIOD_S` | 0.020 | Control loop period |
| `BALL_THETA_LIMIT_DEG` | 1.8° | Max servo angle from level |
| `BALL_TARGET_PLUS_MM` | 50.0 | First waypoint |
| `BALL_TARGET_MINUS_MM` | -50.0 | Second waypoint |
| `BALL_DANGER_POSITION_MM` | 115.0 | Fault if ball exceeds this |
| `BALL_TASK_TIMEOUT_MS` | 15000 | Whole sequence timeout |
| `CPUCLK_FREQ` | 80000000 | System clock (80 MHz) |
| `SERVO_INST_CLK_FREQ` | 100000 | Timer clock for servo PWM |

### PWM/Servo Calibration Notes

The TIMG7 PWM runs at 100kHz (10µs per count), period=2000 counts (20ms). The pulse width in µs maps directly to compare value: `compare = pulse_us / 10`. The 5-point calibration in `ball_app.c` **must be re-measured on the actual hardware** with a level — the values in the code are placeholders. Angle convention: positive = left servo side raised. PWM decreases as angle increases (confirmed in hardware: "compare 减小 → 舵机端抬高").

### `main.c` Control Loop

SysTick at 1kHz increments `g_system_ms`. Every 20th tick (20ms), sets `g_ball_20ms_due`. The main loop polls this flag, atomically clears it, and runs `BallBalanceApp_Update20ms()`. The servo timer is started **after** SysTick and app init to avoid a spurious initial pulse.
