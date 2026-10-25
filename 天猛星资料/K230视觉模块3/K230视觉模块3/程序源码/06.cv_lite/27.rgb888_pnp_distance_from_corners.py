# ============================================================
# MicroPython 轮廓检测+PnP 距离估计测试（cv_lite 扩展）
# Contour Detection + PnP Distance Estimation via cv_lite
# ============================================================

import time, os, gc
from machine import Pin
from media.sensor import *
from media.display import *
from media.media import *
import _thread
import cv_lite               # 需要实现对应的 native C 接口
import ulab.numpy as np

# -------------------------------
# 图像尺寸 / Image size
# -------------------------------
image_shape = [480, 640]

# -------------------------------
# 摄像头初始化
# -------------------------------
sensor = Sensor(id=2,width=1280,height=960,fps=90)
sensor.reset()
# 设置采集图片的分辨率
sensor.set_framesize(w=image_shape[1], h=image_shape[0],chn=CAM_CHN_ID_0)
sensor.set_pixformat(Sensor.RGB888)

# -------------------------------
# 虚拟显示器输出
# -------------------------------
Display.init(Display.ST7701, width=image_shape[1], height=image_shape[0], to_ide=True, quality=50)

# -------------------------------
# 启动媒体管理器
# -------------------------------
MediaManager.init()
sensor.run()

# -------------------------------
# 相机参数
# -------------------------------
# -------------------------------
# 相机内参与畸变系数 / Camera intrinsics and distortion
# -------------------------------
camera_matrix = [
    1199.1495245491617, 0.0, 670.4213222250077,
    0.0, 1200.6879329729338, 475.11122810359876,
    0.0, 0.0, 1.0
]
dist_coeffs = [-0.0331624688297151, 0.04145795463721313, 0.0016964134879770974, 0.0008834973490863845, -0.05414957483933673]
dist_len = len(dist_coeffs)

# -------------------------------
# 目标实际尺寸（单位 cm）
# -------------------------------
obj_width_real = 12.8
obj_height_real = 12.8

# -------------------------------
# 帧率监控
# -------------------------------
clock = time.clock()

# -------------------------------
# 主循环
# -------------------------------
while True:
    clock.tick()

    img = sensor.snapshot()
    img_np = img.to_numpy_ref()

    # 距离估计（通过轮廓+PnP）
    res = cv_lite.rgb888_pnp_distance_from_corners(
        image_shape, img_np,
        camera_matrix, dist_coeffs, dist_len,
        obj_width_real, obj_height_real
    )
    distance=res[0]/2
    rect=res[1]
    corners=res[2]

    # 如果距离估计成功
    if distance > 0:
        img.draw_string_advanced(10, 10, 32, "Dist: %.2fcm" % distance, color=(0, 255, 0))
        img.draw_rectangle(rect[0], rect[1], rect[2], rect[3], color=(255, 0, 0), thickness=2)
        img.draw_cross(corners[0][0],corners[0][1],color=(255,255,255),size=5,thickness=2)
        img.draw_cross(corners[1][0],corners[1][1],color=(255,255,255),size=5,thickness=2)
        img.draw_cross(corners[2][0],corners[2][1],color=(255,255,255),size=5,thickness=2)
        img.draw_cross(corners[3][0],corners[3][1],color=(255,255,255),size=5,thickness=2)
    else:
        img.draw_string_advanced(10, 10, 32, "No Rect Found", color=(255, 0, 0))

    # 显示图像
    Display.show_image(img)

    print("contour_pnp:", clock.fps())
#    print("Distance:", distance)
    gc.collect()

# -------------------------------
# 释放资源
# -------------------------------
sensor.stop()
Display.deinit()
os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
time.sleep_ms(100)
MediaManager.deinit()