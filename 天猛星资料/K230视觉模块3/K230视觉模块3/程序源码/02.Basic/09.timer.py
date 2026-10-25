from machine import Timer
import time

def timer_callback_once(t):
    """
    单次定时器回调函数
    One-shot timer callback function
    """
    print("单次定时器触发了！ Single shot timer triggered!")

def timer_callback_periodic(t):
    """
    周期性定时器回调函数
    Periodic timer callback function
    """
    print("周期定时器触发了！ Periodic timer triggered!")

try:
    # 实例化一个软定时器
    # Initialize a virtual timer
    timer = Timer(-1)

    # 配置单次模式定时器，周期为100ms
    # Configure one-shot timer with 100ms period
    print("启动单次定时器 Starting one-shot timer...")
    timer.init(period=100,
              mode=Timer.ONE_SHOT,
              callback=timer_callback_once)

    # 等待单次定时器触发完成
    # Wait for one-shot timer to complete
    time.sleep(0.2)

    # 配置周期模式定时器，频率为1Hz（周期1秒）
    # Configure periodic timer with 1Hz frequency (1 second period)
    print("启动周期定时器 Starting periodic timer...")
    timer.init(freq=1,
              mode=Timer.PERIODIC,
              callback=timer_callback_periodic)

    # 让周期定时器运行4秒
    # Let periodic timer run for 2 seconds
    time.sleep(4)

except Exception as e:
    print(f"Error occurred: {e}")

finally:
    # 释放定时器资源
    # Release timer resources
    timer.deinit()
    print("Timer deinitialized")
