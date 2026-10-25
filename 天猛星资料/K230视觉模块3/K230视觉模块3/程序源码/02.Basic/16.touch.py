# Import required modules
# 导入所需的模块
import time, os, urandom, sys

# Import display and media related modules
# 导入显示和媒体相关模块
from media.display import *
from media.media import *

# Import touch sensor module
# 导入触摸传感器模块
from machine import TOUCH

# Initialize touch sensor on pin 0
# 在引脚0上初始化触摸传感器
tp = TOUCH(0)

# Define display resolution constants
# 定义显示分辨率常量
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

def display_test():
    """
    Function to test display and touch functionality
    测试显示和触摸功能的函数
    """
    print("display and touch test")

    # Create main background image with white color
    # 创建白色背景的主图像
    img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.ARGB8888)
    img.clear()
    img.draw_rectangle(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT,color=(255,255,255),fill=True)

    # Create secondary image for drawing
    # 创建用于绘画的次要图像
    img2 = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.ARGB8888)
    img2.clear()

    # Initialize display with ST7701 driver
    # 使用ST7701驱动初始化显示器
    Display.init(Display.ST7701, width = DISPLAY_WIDTH, height = DISPLAY_HEIGHT, to_ide = True)
    # Initialize media manager
    # 初始化媒体管理器
    MediaManager.init()

    try:
        # Variables to store previous touch coordinates
        # 存储上一次触摸坐标的变量
        last_x = None
        last_y = None
        while True:
            os.exitpoint()
            # Read touch point data
            # 读取触摸点数据
            point = tp.read(1)

            if len(point):
                print(point)
                pt = point[0]
                # Handle touch events (down or move)
                # 处理触摸事件（按下或移动）
                if pt.event == 0 or pt.event == TOUCH.EVENT_DOWN or pt.event == TOUCH.EVENT_MOVE:
                    if((last_x is not None) and (last_y is not None) and pt.event is not 2):
                        # Draw line between previous and current touch points
                        # 在上一个触摸点和当前触摸点之间画线
                        img2.draw_line(last_x,last_y,pt.x, pt.y, color=(0,0,0), thickness = 5)
                        Display.show_image(img2, layer = Display.LAYER_OSD2, alpha = 128)
                    last_x = pt.x
                    last_y = pt.y
            # Update display with background image
            # 更新显示背景图像
            Display.show_image(img)

            time.sleep(0.05)
    except KeyboardInterrupt as e:
        print("user stop: ", e)
    except BaseException as e:
        print(f"Exception {e}")

    # Cleanup and deinitialize display
    # 清理并反初始化显示器
    Display.deinit()
    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(100)
    # Release media resources
    # 释放媒体资源
    MediaManager.deinit()

if __name__ == "__main__":
    # Enable exit points and run display test
    # 启用退出点并运行显示测试
    os.exitpoint(os.EXITPOINT_ENABLE)
    display_test()
