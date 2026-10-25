# 导入线程模块 Import thread module
import _thread
# 导入时间模块用于实现延时 Import time module for delay functionality
import time

# 定义线程执行的函数 Define the function to be executed in threads
# name: 线程名称参数 Thread name parameter
def func(name):
    while True:
        # 每隔一秒输出一次信息 Print message every second
        print("This is thread {}".format(name))
        # 休眠1秒 Sleep for 1 second
        time.sleep(1)

# 创建并启动第一个线程 Create and start the first thread
# func: 线程函数 Thread function
# ("THREAD_1",): 传递给线程函数的参数(必须是元组格式)
# Arguments passed to thread function (must be tuple format)
_thread.start_new_thread(func,("THREAD_1",))

# 延时500毫秒
# Delay 500ms to give the first thread a chance to start
time.sleep_ms(500)

# 创建并启动第二个线程 Create and start the second thread
# 参数与第一个线程类似 Similar parameters as the first thread
_thread.start_new_thread(func,("THREAD_2",))

# 主线程死循环,防止程序退出
# Main thread infinite loop to prevent program exit
# 延时1毫秒,避免占用过多CPU资源
# Delay 1ms to avoid consuming too much CPU
while True:
    time.sleep_ms(1)
