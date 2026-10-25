# Import required modules
# 导入所需的模块
import time, os, urandom, sys, math
 
# Import display and media related modules
# 导入显示和媒体相关模块
from media.display import *
from media.media import *
from random import randint
 
# Define display resolution constants
# 定义显示分辨率常量
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480
 
def display_test():
    """
    Function to test display functionality
    测试显示功能的函数
    """
 
    # Create main background image with white color
    # 创建白色背景的主图像
    img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.ARGB8888)
    img.clear()
    img.draw_rectangle(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT,color=(255,255,255),fill=True)
 
    # Initialize display with ST7701 driver
    # 使用ST7701驱动初始化显示器
    Display.init(Display.ST7701, width = DISPLAY_WIDTH, height = DISPLAY_HEIGHT, to_ide = True)
    # Initialize media manager
    # 初始化媒体管理器
    MediaManager.init()
    for i in range(10):
        x = randint(0, 2 * img.width()) - img.width() // 2
        y = randint(0, 2 * img.height()) - img.height() // 2
        rx = randint(0, max(img.height(), img.width()) // 2)
        ry = randint(0, max(img.height(), img.width()) // 2)
        rot = randint(0, 360)
 
        r = randint(0, 127) + 128
        g = randint(0, 127) + 128
        b = randint(0, 127) + 128
 
        # 如果第一个参数是缩放器，则此方法需要传递x，y，半径x 和 半径y。
        # 否则，它需要一个（x，y，radius_x，radius_y）元组。
        img.draw_ellipse(
            x, y, rx, ry, rot, color=(r, g, b), thickness=2, fill=False
        )
    # Update display with background image
    # 更新显示背景图像
    Display.show_image(img)
    while True:
        time.sleep(2)
 
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
 