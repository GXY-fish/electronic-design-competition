from media.pyaudio import *                     # 音频模块
from media.media import *                       # 软件抽象模块，主要封装媒体数据链路以及媒体缓冲区
import media.wave as wave                       # wav音频处理模块
import nncase_runtime as nn                     # nncase运行模块，封装了kpu（kmodel推理）和ai2d（图片预处理加速）操作
import ulab.numpy as np                         # 类似python numpy操作，但也会有一些接口不同
import time                                     # 时间统计
import os,sys                                   # 操作系统接口模块
import _thread

from media.sensor import *
from media.display import *
from ybUtils.YbSpeaker import YbSpeaker

# 初始化扬声器 Initialize speaker
spk = YbSpeaker()


# 显示参数 / Display parameters
DISPLAY_WIDTH = 640    # LCD显示宽度 / LCD display width
DISPLAY_HEIGHT = 480   # LCD显示高度 / LCD display height

# 颜色阈值(LAB色彩空间) / Color thresholds (LAB color space)
# (L Min, L Max, A Min, A Max, B Min, B Max)
COLOR_THRESHOLDS = [
    (0, 66, 7, 127, 3, 127),    # 红色阈值 / Red threshold
    (42, 100, -128, -17, 6, 66),     # 绿色阈值 / Green threshold
    (43, 99, -43, -4, -56, -7),       # 蓝色阈值 / Blue threshold
]

# 显示颜色定义 / Display color definitions
DRAW_COLORS = [(255,0,0), (0,255,0), (0,0,255)]  # RGB颜色 / RGB colors
COLOR_LABELS = ['RED', 'GREEN', 'BLUE']           # 颜色标签 / Color labels
play_flag = -1

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

def process_blobs(img, threshold_idx):
    """处理颜色区块检测 / Process color blob detection"""
    area_threshold = 5000
    blobs = img.find_blobs([COLOR_THRESHOLDS[threshold_idx]], area_threshold=area_threshold, merge=True)
    max_area = -1
    if blobs:
        for blob in blobs:
            if blob.area() > max_area:
                max_area = blob.area()
            # 绘制检测框和标记 / Draw detection box and markers
            img.draw_rectangle(blob[0:4], thickness=4, color=DRAW_COLORS[threshold_idx])
            img.draw_cross(blob[5], blob[6], thickness=2)
            img.draw_string_advanced(blob[0], blob[1]-35, 30,
                                   COLOR_LABELS[threshold_idx],
                                   color=DRAW_COLORS[threshold_idx])
    return max_area


def play_audio(wav_file):
    global p
    spk.enable()  # 启用扬声器 Enable speaker
    # 有关音频流的宏变量
    SAMPLE_RATE = 24000         # 采样率24000Hz,即每秒采样24000次
    CHANNELS = 1                # 通道数 1为单声道，2为立体声
    FORMAT = paInt16            # 音频输入输出格式 paInt16
    CHUNK = int(24000*0.3)    # 每次读取音频数据的帧数，设置为0.3s的帧数24000*0.3=7200

    # 用于播放音频
    output_stream = p.open(format=FORMAT,channels=CHANNELS,rate=SAMPLE_RATE,output=True,frames_per_buffer=CHUNK)
    wf = wave.open(wav_file, "rb")
    wav_data = wf.read_frames(CHUNK)
    while wav_data:
        output_stream.write(wav_data)
        wav_data = wf.read_frames(CHUNK)
    time.sleep(2) # 时间缓冲，用于播放声音
    wf.close()
    output_stream.stop_stream()
    output_stream.close()
    spk.disable()  # 禁用扬声器 Disable speaker


def func(name):
    time.sleep(.1)
    global play_flag, wav_files

    while True:
        os.exitpoint()
        if play_flag != -1:
            play_audio(wav_files[play_flag])
            play_flag = -1
        time.sleep(.01)


if __name__ == "__main__":
    os.exitpoint(os.EXITPOINT_ENABLE)
    nn.shrink_memory_pool()

    wav_files = ["/sdcard/audio/detect_red.wav", "/sdcard/audio/detect_green.wav", "/sdcard/audio/detect_blue.wav"]

    _thread.start_new_thread(func,("THREAD_1",))
    CHUNK = int(24000*0.3)
    p = PyAudio()
    p.initialize(CHUNK)

    try:
        sensor = init_sensor()
        init_display()
        sensor.run()

        clock = time.clock()
        last_color = -1
        color_igonre = 10
        color_count = 0
        while True:
            os.exitpoint()
            clock.tick()

            # 捕获图像 / Capture image
            img = sensor.snapshot()
            max_value = [-1, -1]

            # 检测三种颜色 / Detect three colors
            for i in range(3):
                value = process_blobs(img, i)
                if value > max_value[1]:
                    max_value[1] = value
                    max_value[0] = i
            if max_value[0] != -1:
                if last_color == max_value[0] and play_flag == -1:
                    color_count = color_count + 1
                    if color_count > color_igonre:
                        print("color:", max_value[0], max_value[1])
                        play_flag = max_value[0]
                        color_count = 0
                        # play_audio(wav_files[play_flag])
                else:
                    last_color = max_value[0]
                    color_count = 0
            else:
                last_color = -1
                color_count = 0
            # 显示图像并打印FPS / Display image and print FPS
            Display.show_image(img)
            print(clock.fps())

    except Exception as e:
        print(e)                  # 打印异常信息
    finally:
        p.terminate()
        if 'sensor' in locals() and isinstance(sensor, Sensor):
            sensor.stop()
        Display.deinit()
        MediaManager.deinit()


