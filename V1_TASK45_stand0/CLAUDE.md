# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ball-balance PD control test on **TI MSPM0G3507** (Cortex-M0+, LaunchPad). A servo tilts a platform to hold a ball at a fixed target position. The vision system (K230) streams ball position over UART.

This is a **TI Code Composer Studio (CCS) Theia** project. Build and debug are done within CCS. No standalone Makefile or CMake.

## Build & Flash

- **IDE**: CCS Theia (open the `.project` file as a CCS project)
- **Compiler**: TI ARM Clang `ti-cgt-armllvm_4.0.4.LTS` (paths in `.vscode/c_cpp_properties.json`)
- **SDK**: MSPM0 SDK 2.10+ (DriverLib) at `C:/TI/mspm0_sdk_2_10_00_04/source`
- **Device define**: `__MSPM0G3507__`
- **SysConfig**: `empty.syscfg` generates `Debug/ti_msp_dl_config.c` and `Debug/ti_msp_dl_config.h`. Do not hand-edit generated files.
- **VS Code IntelliSense**: `.vscode/c_cpp_properties.json` has include paths and defines for clangd.

## Peripheral Map

| Label | Peripheral | Pins | Purpose |
|-------|-----------|------|---------|
| `SERVO` | TIMG7 (PWM, 100kHz timer, 20ms period) | PA27 | Servo PWM output |
| `PRINT` | UART1, 115200 bps, RX interrupt | PB7(RX), PB6(TX) | Vision data from K230 camera |
| `OLED` | I2C1, 100 kHz | PB3(SDA), PB2(SCL) | OLED display (unused in this test) |
| `xuanniu` | ADC1 channel 1 | PA16 | Potentiometer ADC input |
| `LED` | GPIO | PA14, PA15 | Debug LEDs |
| `BANG_LED` | GPIO (PB22) | PB22 | Onboard LED — active high |
| `VREF` | Internal 2.5V | — | ADC reference |
| HFXT | External 40 MHz crystal | PA5, PA6 | SYSPLL → 80 MHz CPUCLK |

Debug serial output goes to UART1 TX (PB6) via `DEBUG_UART` (`PRINT_INST`).

## Architecture — What Actually Runs

The current `ball_app.c` is a **self-contained PD test** targeting a fixed -50mm position. It does NOT use the modular `ball_control.c` / `ball_task.c` / `servo_map.c` libraries — those exist alongside as reusable modules but are not wired in.

### Data Flow

```
K230 Camera → UART1 RX ISR → VisionProtocol frame parser
                                    ↓
   BallBalanceApp_Update20ms() ← SysTick 1kHz / 20 divider
        ├── VisionProtocol_GetLatest() → raw x_mm measurement
        ├── Inline alpha-beta filter (α=0.65, β=0.15) → x_est, v_est
        ├── Inline PD: theta = Kp*error + Kd*v_est
        ├── Linear PWM map: pulse = 2375 - theta * 30
        └── Platform_ServoWriteUs() → TIMG7 PWM
```

### Key Files

**`main .c`** — Entry point. Sets up SysTick at 1kHz, polls `g_ball_20ms_due` flag, calls `BallBalanceApp_Update20ms()` every 20ms. Initializes servo PWM to level (2375µs) before enabling the timer to avoid a spurious pulse.

**`ball_app.c`** — The whole control application. Self-contained; does not include `ball_control.h`, `ball_task.h`, or `servo_map.h`. Contains:
- Inline alpha-beta position/velocity filter
- Inline PD controller with hardcoded gains (`TEST_KP=0.030`, `TEST_KD=0.025`)
- Linear PWM mapping (`pulse = 2375 - theta * 30`)
- LED state machine: slow flash (waiting for K230), solid (PD active), fast flash (vision lost)
- Serial telemetry every 500ms: `x=... T=-50.0 err=... v=... th=... PWM=...us`
- Debug globals (`g_debug_*`) for live monitoring via CCS debugger

**`ball_app.h`** — Minimal public API: `BallBalanceApp_Init()`, `BallBalanceApp_OnUartRxByte()`, `BallBalanceApp_Update20ms()`.

**`vision_protocol.c/h`** — K230 UART frame parser (15-byte frames with CRC-8). Protocol: `[0xAA, 0x55, 0x0B, seq, cam_ts(2), x(2), v(2), v_diff(2), confidence, flags, CRC8]`. CRC-8 poly=0x07 over bytes 2–13. `VisionMeasurement_IsUsable()` enforces: valid flag, confidence ≥ 35, age ≤ 100ms.

**`uart.c/h`** — UART TX helpers (`UART_send_string`, `UART_print_int`, `UART_print_float1`) and the RX ISR (`PRINT_INST_IRQHandler`). Every received byte is forwarded to `BallBalanceApp_OnUartRxByte()`.

**`ball_config.h`** — All tunable constants: filter alpha/beta, PD gains (separate Kp/Kd for + and - directions), angle/speed limits, servo calibration pulse widths, task timing, vision protocol parameters, and coordinate sign flippers (`VISION_POSITION_SIGN`, `TASK_POSITION_SIGN`).

**`platform_port.h`** — Hardware abstraction declared here, implemented in `main .c`: `Platform_GetMillis()`, `Platform_ServoWriteUs()`, `Platform_DisplayResult()`.

### Standalone Library Modules (exist but not used by ball_app.c)

These are modular implementations that can replace the inline code in `ball_app.c`:

- **`ball_control.c/h`** — Configurable PID controller struct with alpha-beta filter, rate limiting (`move_toward`), anti-windup integral (conditional on position window, speed window, and saturation), and slew-to-level on vision loss.
- **`ball_task.c/h`** — Finite state machine (`IDLE → GO_PLUS_5 → GO_MINUS_5 → FINISHED/FAULT`) with debounced condition-holds, fault detection (vision timeout, position bounds, total timeout).
- **`servo_map.c/h`** — Piecewise linear interpolation: angle (degrees) → PWM pulse width (µs). Supports up to 8 calibration points. Angles outside the table clamp to endpoints.

### PWM / Servo Calibration

- TIMG7: 100kHz clock (10µs per count), period = 2000 counts = 20ms
- Compare value = `pulse_us / 10`
- 5-point calibration in `ball_config.h` (placeholders — must be re-measured on hardware)
- Angle convention: positive = left servo side raised
- **PWM decreases as angle increases** (hardware-verified: lower compare → servo end rises)

### Key Constants (ball_config.h)

| Constant | Value | Meaning |
|----------|-------|---------|
| `BALL_CONTROL_PERIOD_S` | 0.020 | Control loop period |
| `BALL_FILTER_ALPHA` | 0.65 | Position smoothing |
| `BALL_FILTER_BETA` | 0.15 | Velocity estimate gain |
| `BALL_THETA_LIMIT_DEG` | 3.0 | Max servo angle from level |
| `BALL_TARGET_PLUS_MM` | 50.0 | First waypoint (task module) |
| `BALL_TARGET_MINUS_MM` | -50.0 | Second waypoint (task module) |
| `BALL_DANGER_POSITION_MM` | 115.0 | Fault if ball exceeds this |
| `BALL_VISION_TIMEOUT_MS` | 100 | Max age of usable vision data |
| `VISION_CONFIDENCE_MIN` | 35 | Minimum confidence threshold |
| `VISION_POSITION_SIGN` | 1.0 | Flip to -1.0 to invert vision x-axis |
| `TASK_POSITION_SIGN` | 1.0 | Flip to -1.0 to invert task target signs |
| `CPUCLK_FREQ` | 80000000 | System clock (80 MHz) |

### Local Hardcoded Constants in ball_app.c

These override/shadow the `ball_config.h` values for the inline PD implementation:

| Constant | Value | Meaning |
|----------|-------|---------|
| `TEST_TARGET_MM` | -50.0 | Fixed target position |
| `TEST_KP` | 0.030 | PD proportional gain (deg/mm) |
| `TEST_KD` | 0.025 | PD derivative gain (deg·s/mm) |
| `TEST_ALPHA` | 0.65 | Alpha-beta position filter |
| `TEST_BETA` | 0.15 | Alpha-beta velocity filter |
| `TEST_PWM_LEVEL` | 2375 | PWM pulse for level (µs) |
| `TEST_PWM_SLOPE` | 30.0 | PWM change per degree (µs/deg) |

## Debug Globals

The following `volatile` globals in `ball_app.c` are exported for live monitoring in the CCS debugger:

| Variable | Purpose |
|----------|---------|
| `g_debug_task_state` | LED mode (0=wait, 1=lost, 2=active) |
| `g_debug_target_mm` | Current target position |
| `g_debug_error_mm` | Position error (x_est - target) |
| `g_debug_theta_cmd_deg` | Commanded servo angle |
| `g_debug_x_est_mm` | Alpha-beta position estimate |
| `g_debug_v_est_mm_s` | Alpha-beta velocity estimate |
| `g_debug_servo_pulse_us` | Output PWM pulse width |
| `g_debug_fault_flags` | Fault bits (from task module) |
| `g_vision_valid_frame_count` | Count of valid K230 frames |
| `g_vision_x_mm` | Raw vision position |
| `g_vision_confidence` | Last frame confidence |
| `g_uart_rx_byte_count` | Total UART bytes received |

## Notes

- The `ball_control`, `ball_task`, and `servo_map` modules are tested library code ready to be wired in when the competition sequence (arrive at +50mm, settle at -50mm) is needed. Currently `ball_app.c` bypasses them for a simpler fixed-target PD test.
- Servo calibration pulse widths in `ball_config.h` are placeholders and must be re-measured with a bubble level on the actual hardware before competition use.
