# Import required modules
# 导入所需的模块
import time, os, urandom, sys

# Import display and media related modules
# 导入显示和媒体相关模块
from media.display import *
from media.media import *

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

    try:
        # Draw "Yahboom" string
        # 绘制"Yahboom"字符串
        # Y字母
        # 设置屏幕宽度变量
        screen_width = 640

        # 设置文字粗细和颜色
        thickness = 5
        text_color = (0, 191, 255)

        # 计算文本的总宽度
        text_width = 200
        # 计算文本起始位置，使其居中
        start_x = (screen_width - text_width) // 2

        # Y字母
        img.draw_line(start_x, 220, start_x + 20, 240, color=text_color, thickness=thickness)
        img.draw_line(start_x + 20, 240, start_x + 40, 220, color=text_color, thickness=thickness)
        img.draw_line(start_x + 20, 240, start_x + 20, 260, color=text_color, thickness=thickness)

        # a字母
        img.draw_line(start_x + 45, 240, start_x + 65, 240, color=text_color, thickness=thickness)
        img.draw_line(start_x + 65, 240, start_x + 65, 260, color=text_color, thickness=thickness)
        img.draw_line(start_x + 70, 260, start_x + 45, 260, color=text_color, thickness=thickness)
        img.draw_line(start_x + 45, 260, start_x + 45, 240, color=text_color, thickness=thickness)
#        img.draw_line(start_x + 50, 260, start_x + 50, 240, color=text_color, thickness=thickness)

        # h字母
        img.draw_line(start_x + 80, 220, start_x + 80, 260, color=text_color, thickness=thickness)
        img.draw_line(start_x + 80, 240, start_x + 100, 240, color=text_color, thickness=thickness)
        img.draw_line(start_x + 100, 240, start_x + 100, 260, color=text_color, thickness=thickness)

        # b字母
        img.draw_line(start_x + 110, 220, start_x + 110, 260, color=text_color, thickness=thickness)
        img.draw_line(start_x + 110, 240, start_x + 130, 240, color=text_color, thickness=thickness)
        img.draw_line(start_x + 130, 240, start_x + 130, 260, color=text_color, thickness=thickness)
        img.draw_line(start_x + 130, 260, start_x + 110, 260, color=text_color, thickness=thickness)

        # o字母
        img.draw_line(start_x + 140, 240, start_x + 160, 240, color=text_color, thickness=thickness)
        img.draw_line(start_x + 160, 240, start_x + 160, 260, color=text_color, thickness=thickness)
        img.draw_line(start_x + 160, 260, start_x + 140, 260, color=text_color, thickness=thickness)
        img.draw_line(start_x + 140, 260, start_x + 140, 240, color=text_color, thickness=thickness)

        # o字母
        img.draw_line(start_x + 170, 240, start_x + 190, 240, color=text_color, thickness=thickness)
        img.draw_line(start_x + 190, 240, start_x + 190, 260, color=text_color, thickness=thickness)
        img.draw_line(start_x + 190, 260, start_x + 170, 260, color=text_color, thickness=thickness)
        img.draw_line(start_x + 170, 260, start_x + 170, 240, color=text_color, thickness=thickness)

        # m字母
        img.draw_line(start_x + 200, 240, start_x + 200, 260, color=text_color, thickness=thickness)
        img.draw_line(start_x + 200, 240, start_x + 210, 250, color=text_color, thickness=thickness)
        img.draw_line(start_x + 210, 250, start_x + 220, 240, color=text_color, thickness=thickness)
        img.draw_line(start_x + 220, 240, start_x + 220, 260, color=text_color, thickness=thickness)

        # Update display with background image
        # 更新显示背景图像
        Display.show_image(img)
        while True:
            time.sleep(2)

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
