# 导入 machine 模块中的 I2C 和 FPIOA 类
# (Import the I2C and FPIOA classes from the machine module)
from machine import I2C
from machine import FPIOA

# 导入 ssd1306 模块中的 SSD1306_I2C 类
# (Import the SSD1306_I2C class from the ssd1306 module)
from ybUtils.ssd1306 import SSD1306_I2C

# 导入时间模块
# (Import the time module)
import time

# 实例化 FPIOA 对象
# (Create an instance of the FPIOA object)
fpioa = FPIOA()

# 创建 I2C 实例，使用 I2C 通道 1
# (Create an I2C instance, using I2C channel 1)
i2c = I2C(1)

# 配置引脚功能:
# - 将 GPIO 引脚 34 映射到 I2C1_SCL 功能
# - 将 GPIO 引脚 35 映射到 I2C1_SDA 功能
# (Configure pin functions:
# - Map GPIO pin 34 to I2C1_SCL function
# - Map GPIO pin 35 to I2C1_SDA function)
fpioa.set_function(34, FPIOA.IIC1_SCL, oe=1, ie=1, pu=1, st=1, ds=15)
fpioa.set_function(35, FPIOA.IIC1_SDA, oe=1, ie=1, pu=1, st=1, ds=15)

# 创建 SSD1306 OLED 显示器实例
# (Create an SSD1306 OLED display instance)
# 设置 OLED 显示器的分辨率为 128x32
# (Set the OLED display resolution to 128x32)
oled = SSD1306_I2C(128, 32, i2c)

# 清除 OLED 显示器的内容
# (Clear the content of the OLED display)
oled.fill(0)

# 在 OLED 显示器上显示文字 "Hello Yahboom"，在坐标 (0, 10) 处
# (Display the text "Hello Yahboom" on the OLED display at coordinates (0, 10))
oled.text('Hello Yahboom', 0, 10)

# 遍历 OLED 显示器的所有像素
# (Iterate through all the pixels of the OLED display)
for x in range(128):
    for y in range(32):
        # 获取指定像素的值
        # (Get the value of the specified pixel)
        a = oled.pixel(x, y)

        # 如果像素值为 1（亮起），则打印坐标
        # (If the pixel value is 1 (lit up), print the coordinates)
        if a == 1:
            print(x, y)

# 更新 OLED 显示器的内容
# (Update the content of the OLED display)
oled.show()
