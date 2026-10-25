#!/usr/bin/env python3
"""
K230 小球实时位置监控脚本 (v3 — 匹配 v4 固件)
=============================================
在电脑上运行, 读取天猛星 CH340 串口的输出, 实时显示小球位置。

v4 固件输出格式 (每 100ms 刷新):
  [BALL]  pos=+xxmm  |  vel=+xxmm/s  |  dif=+xxmm/s  |  conf=xx%  [OK]  CAL  fps=xx
  [---|---|---|---|---|●---|---|---|---|---]

使用方法:
  1. K230 运行 main.py (UART 115200)
  2. 天猛星烧录 main.c v4 (UART3 接 K230, UART0 接 CH340)
  3. python serial_test.py COM5

依赖: pip install pyserial
"""

import sys
import time
import re
from collections import deque

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("请先安装 pyserial: pip install pyserial")
    sys.exit(1)


def find_serial_port():
    """自动查找 CH340 串口"""
    ports = serial.tools.list_ports.comports()
    ch340_ports = []
    for p in ports:
        desc = p.description.upper()
        if 'CH340' in desc or 'CH341' in desc or 'USB-SERIAL' in desc or 'USB' in desc:
            ch340_ports.append((p.device, p.description))
    return ch340_ports


def parse_line(line):
    """解析 v4 固件输出的 [BALL] 行"""
    # 格式: [BALL]  pos=+120mm  |  vel=-30mm/s  |  dif=-35mm/s  |  conf=86%  [OK]  CAL  fps=33
    m = re.match(
        r'\[BALL\]\s+pos=([+-]?\d+)mm\s+\|\s+vel=([+-]?\d+)mm/s\s+\|\s+dif=([+-]?\d+)mm/s\s+\|\s+conf=(\d+)%',
        line
    )
    if m:
        result = {
            'x_mm': int(m.group(1)),
            'v_ab': int(m.group(2)),
            'v_df': int(m.group(3)),
            'conf': int(m.group(4)),
        }
        # 提取状态标志
        if '[OK]' in line:
            result['status'] = 'OK'
        elif '[LOST]' in line:
            result['status'] = 'LOST'
        else:
            result['status'] = '---'
        result['cal'] = 'CAL' in line
        # 提取 fps
        fps_m = re.search(r'fps=(\d+)', line)
        if fps_m:
            result['fps'] = int(fps_m.group(1))
        else:
            result['fps'] = 0
        return result
    return None


def parse_stats_line(line):
    """解析 STATS 行"""
    m = re.match(r'.*STATS:\s+total=(\d+)\s+frames\s+fps=(\d+)', line)
    if m:
        return {'total': int(m.group(1)), 'fps': int(m.group(2))}
    return None


def clear_line():
    """清除当前行"""
    sys.stdout.write('\r' + ' ' * 120 + '\r')
    sys.stdout.flush()


def main():
    # --- 找串口 ---
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        ports = find_serial_port()
        if not ports:
            print("未找到 CH340 串口! 请指定 COM 口:")
            print("  python serial_test.py COM5")
            sys.exit(1)
        if len(ports) == 1:
            port = ports[0][0]
        else:
            print("找到多个串口, 请选择:")
            for i, (p, d) in enumerate(ports):
                print(f"  {i}: {p} ({d})")
            idx = int(input("输入序号: "))
            port = ports[idx][0]

    baud = 115200
    print(f"连接 {port} @ {baud}...")
    print("按 Ctrl+C 停止\n")

    ser = serial.Serial(port, baud, timeout=0.1)

    # --- 统计变量 ---
    frame_count = 0
    x_values = deque(maxlen=200)
    v_ab_values = deque(maxlen=200)
    v_df_values = deque(maxlen=200)
    start_time = time.time()
    output_lines = 0  # 完整行计数(非BALL行过滤用)

    # --- 清屏 ---
    print("\033[2J\033[H", end="")
    print("=" * 72)
    print("  小球实时位置监控")
    print(f"  串口: {port} @ {baud}")
    print("=" * 72)
    print()

    try:
        buf = b""
        last_state_line = ""  # 最后一个完整 [BALL] 行(含进度条)
        in_stats_block = False

        while True:
            data = ser.read(256)
            if data:
                buf += data
                while b"\n" in buf:
                    line_bytes, buf = buf.split(b"\n", 1)
                    line = line_bytes.decode('ascii', errors='ignore').strip()

                    if not line:
                        in_stats_block = False
                        continue

                    # 忽略 STATS 块 (每秒输出一次, 不影响实时显示)
                    if 'STATS:' in line or '───' in line:
                        in_stats_block = True
                        # 打印 STATS 到单独一行
                        stats = parse_stats_line(line)
                        if stats:
                            pass  # 静默收集
                        continue

                    if in_stats_block and not line:
                        in_stats_block = False
                        continue

                    # 解析 [BALL] 行
                    parsed = parse_line(line)
                    if parsed is not None:
                        frame_count += 1
                        x_values.append(parsed['x_mm'])
                        v_ab_values.append(parsed['v_ab'])
                        v_df_values.append(parsed['v_df'])

                        # 用当前数据更新状态行 (不清屏, 实时覆盖)
                        elapsed = time.time() - start_time

                        # 构建进度条 (±120mm范围)
                        bar_width = 50
                        bar_center = bar_width // 2
                        x_clamped = max(-120, min(120, parsed['x_mm']))
                        bar_pos = bar_center + int(x_clamped * bar_center / 120)
                        bar_pos = max(0, min(bar_width - 1, bar_pos))

                        bar = ['─'] * bar_width
                        bar[bar_center] = '│'
                        bar[bar_pos] = '●'
                        bar_str = ''.join(bar)

                        # 实时刷新行
                        clear_line()
                        sys.stdout.write(
                            f"\r  ⚫ pos={parsed['x_mm']:+d}mm  "
                            f"vel={parsed['v_ab']:+d}mm/s  "
                            f"dif={parsed['v_df']:+d}mm/s  "
                            f"conf={parsed['conf']}%  "
                            f"[{parsed['status']}]"
                        )
                        if parsed['cal']:
                            sys.stdout.write("  CAL")
                        sys.stdout.write(f"  fps={parsed['fps']}\n")

                        # 进度条
                        sys.stdout.write(f"  [{bar_str}]  -120mm           O           +120mm\n")
                        sys.stdout.flush()

                    # 忽略 header/info 行 (以 ┌└│ 等字符开头)

    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        print("\n\n" + "=" * 72)
        print("  监控结束 - 统计")
        print("=" * 72)

        elapsed = time.time() - start_time
        if frame_count > 0 and elapsed > 0:
            x_arr = list(x_values)
            v_ab_arr = list(v_ab_values)
            v_df_arr = list(v_df_values)

            if x_arr:
                x_mean = sum(x_arr) / len(x_arr)
                x_std = (sum((x - x_mean)**2 for x in x_arr) / len(x_arr))**0.5
            else:
                x_mean = x_std = 0
            if v_ab_arr:
                v_mean_ab = sum(v_ab_arr) / len(v_ab_arr)
            else:
                v_mean_ab = 0

            print(f"  总帧数:      {frame_count}")
            print(f"  运行时间:    {elapsed:.1f}s")
            print(f"  平均帧率:    {frame_count/elapsed:.1f} fps")
            print(f"  位置 x:      均值={x_mean:.1f}mm  标准差={x_std:.2f}mm")
            if x_arr:
                print(f"               范围=[{min(x_arr)}, {max(x_arr)}]mm")
            print(f"  滤波速度 vab: 均值={v_mean_ab:.1f}mm/s")

            if x_std < 2:
                print("  ✓ 位置抖动 < 2mm, 符合 PID 需求")
            else:
                print("  ⚠ 位置抖动 >= 2mm, 需要检查")
            if frame_count/elapsed >= 25:
                print(f"  ✓ 帧率 {frame_count/elapsed:.0f}fps >= 25Hz, 可用于控制")
            else:
                print(f"  ⚠ 帧率 {frame_count/elapsed:.0f}fps < 25Hz, 偏低")
        print("=" * 72)


if __name__ == "__main__":
    main()
