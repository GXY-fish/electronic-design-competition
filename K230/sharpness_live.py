"""
K230 清晰度实时查看工具
=======================
GC2093 是定焦镜头, 焦距固定不可调。
本工具帮你在移动摄像头时, 实时看到画面清晰度数值。

用法:
  1. 运行本脚本
  2. 上下前后移动摄像头, 观察屏幕上的 sharp 值
  3. sharp 值越大 = 越清晰
  4. 找到 sharp 值最大的位置, 固定摄像头在那里

屏幕显示:
  - sharp: 中心 80x80 区域的 G 通道标准差 (越大越清晰)
  - 同时画一个绿色进度条, 直观显示清晰度
  - 如果检测到球, 显示检测框和置信度
"""

import ulab.numpy as np
from libs.PipeLine import PipeLine, ScopedTiming
from libs.PlatTasks import DetectionApp
from libs.Utils import *
from media.sensor import *
from media.media import *
import os, gc, time

KMODEL_DIR = "/sdcard/kmodel/"
RGB888P_SIZE = [640, 480]
DISPLAY_SIZE = [640, 480]
DISPLAY_MODE = "st7701"

# ============== 初始化 ==============
print("=" * 50)
print(" K230 清晰度实时查看 (定焦镜头辅助定位)")
print("=" * 50)
print("[CAM] GC2093 定焦传感器")
print("[CAM] 移动摄像头找到 sharp 值最大的位置")
print()

cam_sensor = Sensor()
cam_sensor.reset()

try:
    cam_sensor.auto_exposure(False)
    print("[CAM] 自动曝光已关闭")
except:
    pass

pl = PipeLine(rgb888p_size=RGB888P_SIZE, display_size=DISPLAY_SIZE, display_mode=DISPLAY_MODE)
pl.create(sensor=cam_sensor)
display_size = pl.get_display_size()
print("[PIPE] PipeLine 就绪")

# 加载检测模型
try:
    deploy_conf = read_json(KMODEL_DIR + "deploy_config.json")
    kmodel_path = KMODEL_DIR + deploy_conf["kmodel_path"]
    labels = deploy_conf["categories"]
    conf_thresh = deploy_conf["confidence_threshold"]
    nms_thresh = deploy_conf["nms_threshold"]
    model_input_size = deploy_conf["img_size"]
    model_type = deploy_conf["model_type"]
    anchors = deploy_conf["anchors"][0] + deploy_conf["anchors"][1] + deploy_conf["anchors"][2]
    det_app = DetectionApp("video", kmodel_path, labels, model_input_size,
                           anchors, model_type, conf_thresh, nms_thresh,
                           RGB888P_SIZE, display_size, debug_mode=0)
    det_app.config_preprocess()
    print("[DET] 检测模型已加载")
    has_det = True
except Exception as e:
    print("[DET] 检测模型加载失败, 只显示清晰度:", e)
    has_det = False

# ============== 清晰度计算 ==============
def calc_sharpness_center(img):
    """计算画面中心 80x80 区域的 G 通道标准差"""
    try:
        cx = RGB888P_SIZE[0] // 2
        cy = RGB888P_SIZE[1] // 2
        half = 40
        region = img[1, cy-half:cy+half, cx-half:cx+half]
        return int(np.std(region))
    except:
        return 0

def calc_sharpness_region(img, x1, y1, x2, y2):
    """计算指定区域的 G 通道标准差"""
    try:
        x0 = max(0, x1)
        y0 = max(0, y1)
        x1 = min(RGB888P_SIZE[0], x2)
        y1 = min(RGB888P_SIZE[1], y2)
        if x1 - x0 < 8 or y1 - y0 < 8:
            return 0
        region = img[1, y0:y1, x0:x1]
        return int(np.std(region))
    except:
        return 0

# ============== 主循环 ==============
print("\n开始实时显示... 移动摄像头找到最清晰位置")
print("sharp 值越大 = 越清晰")
print()

max_sharp_seen = 0
frame_count = 0

while True:
    os.exitpoint()
    img = pl.get_frame()

    # 中心区域清晰度
    sharp_center = calc_sharpness_center(img)

    # 检测球
    det_info = ""
    sharp_ball = 0
    if has_det:
        res = det_app.run(img)
        if res:
            boxes = res.get('boxes', [])
            scores = res.get('scores', [])
            idx_list = res.get('idx', [])
            for i, box in enumerate(boxes):
                if scores[i] < conf_thresh:
                    continue
                if len(idx_list) > 0 and idx_list[i] != 0:
                    continue
                x1, y1, x2, y2 = box
                w = x2 - x1
                h = y2 - y1
                if w < 5 or w > 200:
                    continue
                # 画框
                x1_d = int(x1 * display_size[0] // RGB888P_SIZE[0])
                y1_d = int(y1 * display_size[1] // RGB888P_SIZE[1])
                w_d = int(w * display_size[0] // RGB888P_SIZE[0])
                h_d = int(h * display_size[1] // RGB888P_SIZE[1])
                # 球区域清晰度
                sharp_ball = calc_sharpness_region(img, x1, y1, x2, y2)
                # 绿色框 = 球区域清晰, 红色框 = 球区域糊
                box_color = (0, 255, 0) if sharp_ball > 30 else (255, 0, 0)
                pl.osd_img.draw_rectangle(x1_d, y1_d, w_d, h_d, color=box_color, thickness=2)
                det_info = "ball conf=%.2f sharp=%d" % (scores[i], sharp_ball)
                break

    # 记录最大清晰度
    cur_sharp = sharp_ball if sharp_ball > 0 else sharp_center
    if cur_sharp > max_sharp_seen:
        max_sharp_seen = cur_sharp

    # 显示信息
    pl.osd_img.clear()

    if has_det and det_info:
        # 重新画框 (clear 之后)
        pass  # 上面已经画了

    pl.osd_img.draw_string_advanced(10, 10, 20,
        "center sharp=%d" % sharp_center,
        color=(255, 255, 0))
    if det_info:
        pl.osd_img.draw_string_advanced(10, 40, 16, det_info, color=(0, 255, 0))

    # 清晰度进度条
    bar_w = min(300, cur_sharp * 5)
    bar_color = (0, 255, 0) if cur_sharp > 40 else (255, 0, 0)
    pl.osd_img.draw_rectangle(10, 70, bar_w, 12, color=bar_color, thickness=1)
    pl.osd_img.draw_string_advanced(10, 90, 14,
        "max=%d  (green=clear  red=blurry)" % max_sharp_seen,
        color=(128, 128, 128))

    pl.show_image()
    gc.collect()
    frame_count += 1
