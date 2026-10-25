import time, os, sys
from media.sensor import *
from media.display import *
from media.media import *

from libs.YbProtocol import YbProtocol
from ybUtils.YbUart import YbUart
# uart = None
uart = YbUart(baudrate=115200)
pto = YbProtocol()

last_cx = 300 #初始点x坐标
last_cy = 220 #初始点y坐标
# 显示参数 / Display parameters
DISPLAY_WIDTH = 640   # LCD显示宽度 / LCD display width
DISPLAY_HEIGHT = 480  # LCD显示高度 / LCD display height

# LAB颜色空间阈值 / LAB color space thresholds
# (L Min, L Max, A Min, A Max, B Min, B Max)
THRESHOLDS = [
    (0, 66, 7, 127, 3, 127),    # 红色阈值 / Red threshold
    (42, 100, -128, -17, 6, 66),     # 绿色阈值 / Green threshold
    (43, 99, -43, -4, -56, -7),       # 蓝色阈值 / Blue threshold
    (37, 100, -128, 127, -128, -27)    # 亚博智能Logo的颜色 color of YAHBOOM
]

def get_closest_rgb(lab_threshold):
    """根据LAB阈值计算最接近的RGB颜色 / Calculate closest RGB color based on LAB threshold"""
    # 获取LAB空间的中心点值
    l_center = (lab_threshold[0] + lab_threshold[1]) // 2
    a_center = (lab_threshold[2] + lab_threshold[3]) // 2
    b_center = (lab_threshold[4] + lab_threshold[5]) // 2
    return image.lab_to_rgb((l_center,a_center,b_center))

def init_sensor():
    """初始化摄像头 / Initialize camera sensor"""
    sensor = Sensor()
    sensor.reset()
    sensor.set_framesize(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)
    sensor.set_pixformat(Sensor.RGB565)
    return sensor

def init_display():
    """初始化显示 / Initialize display"""
    Display.init(Display.ST7701, to_ide=True)
    MediaManager.init()

def process_blobs(img, blobs, color):
    global last_cx
    global last_cy
    """处理检测到的色块 / Process detected color blobs"""
    for blob in blobs:
        img.draw_rectangle(blob[0:4], color=color, thickness=4)
        img.draw_cross(blob[5], blob[6], color=color, thickness=2)
        cx = blob[0]
        cy = blob[1]
        last_cx = cx#更新坐标
        last_cy = cy#更新坐标
        return cx, cy, 1
    return last_cx, last_cy, 0


def draw_fps(img, fps):
    """绘制FPS信息 / Draw FPS information"""
    img.draw_string_advanced(0, 0, 30, f'FPS: {fps:.3f}', color=(255, 255, 255))


def conversion_postion(x,y):
    if x > 510:
       x_h = 255
       x_l = 255
       x_z = x-255-255
    elif 510>=x>=255:
       x_h = 255
       x_l = x-255
       x_z = 0
    else:
       x_h = x
       x_l = 0
       x_z = 0
    if y > 510:
       y_h = 255
       y_l = 255
       y_z = y-255-255
    elif 510>=y>=255:
       y_h = 255
       y_l = y-255
       y_z = 0
    else:
       y_h = y
       y_l = 0
       y_z = 0
    return x_h,x_l,x_z,y_h,y_l,y_z

def main():
    try:
        # 初始化设备 / Initialize devices
        sensor = init_sensor()
        init_display()
        sensor.run()

        clock = time.clock()

        # 选择要检测的颜色索引 (0:红, 1:绿, 2:蓝) / Select color index to detect
        color_index = 1  # 可以修改这个值来选择检测不同的颜色
        threshold = THRESHOLDS[color_index]
        detect_color = get_closest_rgb(threshold)

        while True:
            clock.tick()
            img = sensor.snapshot()

            # 检测指定颜色 / Detect specified color
            blobs = img.find_blobs([threshold], area_threshold=5000, merge=True)
            if blobs:
                x,y,ok= process_blobs(img, blobs, detect_color)
                cx_h,cx_l,cx_z,cy_h,cy_l,cy_z = conversion_postion(x,y)
                uart.write(bytearray([0x55,0xaa,0x00,int(cx_h),int(cx_l),int(cx_z),0xfa]))
                uart.write(bytearray([0x55,0xaa,0xff,int(cy_h),int(cy_l),int(cy_z),0xfa]))
            fps = clock.fps()
            draw_fps(img, fps)

            print(fps)

            Display.show_image(img)

    except KeyboardInterrupt as e:
        print("用户中断 / User interrupted: ", e)
    except Exception as e:
        print(f"发生错误 / Error occurred: {e}")
    finally:
        if 'sensor' in locals() and isinstance(sensor, Sensor):
            sensor.stop()
        Display.deinit()
        MediaManager.deinit()

if __name__ == "__main__":
    main()
