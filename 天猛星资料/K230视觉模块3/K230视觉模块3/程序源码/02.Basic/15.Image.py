from media.display import * 
from media.media import *
import image,time


Display.init(Display.ST7701, width = 640, height = 480, osd_num = 1, to_ide = True)

# 如果没有选配屏幕，则使用这一条初始化代码：
# Display.init(Display.VIRT, width = 1920, height = 1080)

img=image.Image("/sdcard/resources/wp.png", copy_to_fb=True)

MediaManager.init()

# 这里必须将png图片转换为rgb888或rgb565，否则无法显示
img = img.to_rgb888()

Display.show_image(img)
while True:
    pass

