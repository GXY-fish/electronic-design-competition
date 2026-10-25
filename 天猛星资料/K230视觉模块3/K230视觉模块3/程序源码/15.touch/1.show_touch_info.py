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

def touch_point_display():
    """
    Function to display touch points with coordinates
    显示触摸点和坐标的函数
    """
    print("Touch point display test")

    # Create main background image with white color
    # 创建白色背景的主图像
    img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB888)
    
    def clear_and_reset_background():
        """Clear the image and reset to white background"""
        img.clear()
        img.draw_rectangle(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, color=(255,255,255), fill=True)

    # Initialize with white background
    # 初始化白色背景
    clear_and_reset_background()

    # Initialize display with ST7701 driver
    # 使用ST7701驱动初始化显示器
    Display.init(Display.ST7701, width = DISPLAY_WIDTH, height = DISPLAY_HEIGHT, to_ide = True)
    # Initialize media manager
    # 初始化媒体管理器
    MediaManager.init()

    try:
        # Variables to store current touch state
        # 存储当前触摸状态的变量
        current_touch_active = False
        last_touch_down_time = 0
        
        while True:
            os.exitpoint()
            # Read touch point data
            # 读取触摸点数据
            point = tp.read(1)

            if len(point):
                pt = point[0]
                
                # Handle touch down event
                # 处理触摸按下事件
                if pt.event == TOUCH.EVENT_DOWN:
                    # Clear previous touch point and reset background
                    # 清除上一个触摸点并重置背景
                    clear_and_reset_background()
                    
                    # Draw circle at touch point
                    # 在触摸点绘制圆形
                    circle_radius = 20
                    img.draw_circle(pt.x, pt.y, circle_radius, color=(255, 0, 0), thickness=3)
                    
                    # Draw coordinate text
                    # 绘制坐标文字
                    coord_text = f"({pt.x}, {pt.y})"
                    
                    # Calculate text position (offset from touch point to avoid overlap)
                    # 计算文字位置（从触摸点偏移以避免重叠）
                    text_x = pt.x + 30
                    text_y = pt.y - 30
                    
                    # Ensure text stays within screen bounds
                    # 确保文字保持在屏幕边界内
                    if text_x + 100 > DISPLAY_WIDTH:
                        text_x = pt.x - 100
                    if text_y < 20:
                        text_y = pt.y + 40
                    
                    # Draw coordinate text with black color
                    # 用黑色绘制坐标文字
                    img.draw_string_advanced(text_x, text_y, 24, coord_text, color=(0, 0, 0))
                    
                    current_touch_active = True
                    last_touch_down_time = time.time()
                    
                    print(f"Touch detected at: {coord_text}")
                
                # Handle touch up event
                # 处理触摸抬起事件
                elif pt.event == TOUCH.EVENT_UP:
                    current_touch_active = False
            
            # Update display with current image
            # 更新显示当前图像
            Display.show_image(img)
            
            time.sleep(0.05)
            
    except KeyboardInterrupt as e:
        print("User stop: ", e)
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
    # Enable exit points and run touch point display test
    # 启用退出点并运行触摸点显示测试
    os.exitpoint(os.EXITPOINT_ENABLE)
    touch_point_display()