from machine import FPIOA, UART
import time

# ============================================================
# 1. 强制把IO9、IO10映射到UART1
# ============================================================
fpioa = FPIOA()

fpioa.set_function(9, FPIOA.UART1_TXD)
fpioa.set_function(10, FPIOA.UART1_RXD)

print("IO9 function:")
try:
    fpioa.help(9)
except Exception as e:
    print("help(9) failed:", e)

print("IO10 function:")
try:
    fpioa.help(10)
except Exception as e:
    print("help(10) failed:", e)

# ============================================================
# 2. 初始化UART1，115200 8N1
# ============================================================
uart = UART(
    UART.UART1,
    baudrate=115200,
    bits=UART.EIGHTBITS,
    parity=UART.PARITY_NONE,
    stop=UART.STOPBITS_ONE
)

# 合法的15字节测试帧：
# x=0mm, v=0, confidence=90, VALID+CAL_OK
# CRC8已经计算为0xEA
test_frame = bytes((
    0xAA, 0x55, 0x0B,
    0x01,                   # SEQ
    0x34, 0x12,             # timestamp
    0x00, 0x00,             # x_mm = 0
    0x00, 0x00,             # v_ab = 0
    0x00, 0x00,             # v_df = 0
    0x5A,                   # confidence = 90
    0x05,                   # VALID | CAL_OK
    0xEA                    # CRC8
))

print("UART1 TX test started")

count = 0

while True:
    result = uart.write(test_frame)
    count += 1

    print("TX frame =", count,
          "write result =", result,
          "length =", len(test_frame))

    time.sleep_ms(100)