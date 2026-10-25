import lvgl as lv
from media.display import *
import time  # 显式导入time模块 / Explicitly import time module

from machine import TOUCH
class touch_screen():
    def __init__(self):
        self.state = lv.INDEV_STATE.RELEASED

        self.indev_drv = lv.indev_create()
        self.indev_drv.set_type(lv.INDEV_TYPE.POINTER)
        self.indev_drv.set_read_cb(self.callback)
        self.touch = TOUCH(0)

    def callback(self, driver, data):
        x, y, state = 0, 0, lv.INDEV_STATE.RELEASED
        tp = self.touch.read(1)
        if len(tp):
            x, y, event = tp[0].x, tp[0].y, tp[0].event
            if event == 2 or event == 3:
                state = lv.INDEV_STATE.PRESSED
        data.point = lv.point_t({'x': x, 'y': y})
        data.state = state


# 显示屏分辨率配置 / Display resolution configuration
DISPLAY_WIDTH = 640   # 显示屏宽度 / Display width
DISPLAY_HEIGHT = 480  # 显示屏高度 / Display height

def disp_drv_flush_cb(disp_drv, area, color):
    """
    显示驱动刷新回调函数
    Display driver flush callback function

    Args:
        disp_drv: 显示驱动对象 / Display driver object
        area: 刷新区域 / Refresh area
        color: 颜色数据 / Color data
    """
    global disp_img1
    Display.show_image(disp_img1)  # 显示图像缓冲区 / Show image buffer
    time.sleep(0.01)  # 适当延时确保显示稳定 / Small delay to ensure stable display
    disp_drv.flush_ready()  # 通知LVGL刷新完成 / Notify LVGL that flush is complete

def display_init():
    """
    显示设备初始化函数
    Display device initialization function
    """
    # 初始化ST7701显示屏 / Initialize ST7701 display
    Display.init(
        Display.ST7701,
        width=DISPLAY_WIDTH,
        height=DISPLAY_HEIGHT,
        to_ide=True  # 启用IDE显示功能 / Enable IDE display function
    )

    # 初始化媒体管理器 / Initialize media manager
    MediaManager.init()

def lvgl_init():
    """
    LVGL初始化函数
    LVGL initialization function
    """
    global disp_img1

    # 初始化LVGL库 / Initialize LVGL library
    lv.init()

    # 创建显示缓冲区 / Create display buffer
    disp_img1 = image.Image(
        DISPLAY_WIDTH,
        DISPLAY_HEIGHT,
        image.BGRA8888  # 使用BGRA8888颜色格式 / Use BGRA8888 color format
    )

    # 创建显示驱动 / Create display driver
    disp_drv = lv.disp_create(DISPLAY_WIDTH, DISPLAY_HEIGHT)

    # 设置显示缓冲区 / Set display buffers
    disp_drv.set_draw_buffers(
        disp_img1.bytearray(),
        None,  # 单缓冲模式 / Single buffer mode
        disp_img1.size(),
        lv.DISP_RENDER_MODE.DIRECT  # 直接渲染模式 / Direct rendering mode
    )

    # 设置刷新回调函数 / Set flush callback
    disp_drv.set_flush_cb(disp_drv_flush_cb)

    tp = touch_screen()

def on_click(event):
    print("I was clicked!")

def display_deinit():
    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(50)
    # deinit display
    Display.deinit()
    # release media buffer
    MediaManager.deinit()

def lvgl_deinit():
    global disp_img1
    lv.deinit()
    del disp_img1


def create_button():
    """
    创建按钮函数
    Create button function
    """
    # 创建按钮组件 / Create button widget
    btn = lv.btn(lv.scr_act())
    # 居中对齐按钮 / Center align button
    btn.align(lv.ALIGN.CENTER, 0, 0)
    # 创建标签 / Create label
    label = lv.label(btn)
    # 设置按钮文本 / Set button text
    label.set_text("Button")
    # 添加点击事件处理 / Add click event handler
    btn.add_event(on_click, lv.EVENT.CLICKED, None)



def main():
    """
    主函数
    Main function
    """
    try:
        # 初始化显示设备和LVGL / Initialize display device and LVGL
        display_init()
        lvgl_init()
        create_button()
        print("LVGL initialization completed")

        # LVGL主循环 / LVGL main loop
        while True:
            # 运行LVGL定时器处理程序 / Run LVGL timer handler
            period = lv.timer_handler_run_in_period(1)
            time.sleep_ms(period)

    except Exception as e:
        display_deinit()
        lvgl_deinit()
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
