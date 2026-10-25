# 导入YbRGB库 (Import YbRGB library)
from ybUtils.YbRGB import YbRGB
# 导入时间库 (Import time library)
import time
# 导入数学库 (Import math library)
import math

# 初始化RGB LED (Initialize RGB LED)
rgb = YbRGB()

def breath_effect(r, g, b, duration=2):
    """
    实现呼吸灯效果 (Implement breathing light effect)
    r, g, b: 目标颜色的RGB值（0-255） (Target color RGB values (0-255))
    duration: 一次呼吸效果的持续时间（秒） (Duration of one breathing cycle in seconds)
    """
    steps = 1000  # 渐变步数 (Number of gradient steps)
    for i in range(steps):
        # 使用正弦函数使亮度变化更加平滑 (Use sine function to make brightness change smoother)
        brightness = math.sin(i / steps * math.pi)
        current_r = int(r * brightness)
        current_g = int(g * brightness)
        current_b = int(b * brightness)
        rgb.show_rgb([current_r, current_g, current_b])
        time.sleep(duration / (2 * steps))

    # 渐暗过程 (Fade-out process)
    for i in range(steps-1, -1, -1):
        brightness = math.sin(i / steps * math.pi)
        current_r = int(r * brightness)
        current_g = int(g * brightness)
        current_b = int(b * brightness)
        rgb.show_rgb([current_r, current_g, current_b])
        time.sleep(duration / (2 * steps))

# 定义几种好看的颜色 (Define several beautiful colors)
colors = [
    (255, 0, 0),    # 红色 (Red)
    (0, 255, 0),    # 绿色 (Green)
    (0, 0, 255),    # 蓝色 (Blue)
    (255, 0, 255),  # 紫色 (Purple)
    (255, 165, 0),  # 橙色 (Orange)
    (0, 255, 255),  # 青色 (Cyan)
]

# 主循环 (Main loop)
try:
    while True:
        for color in colors:
            breath_effect(color[0], color[1], color[2])

except Exception:
    # 确保程序结束时关闭LED (Ensure LED is turned off when the program ends)
    rgb.show_rgb([0, 0, 0])
