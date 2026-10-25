"""
K230 钢球标定脚本 (5点线性标定)
==============================
将球分别放在 -5, -2.5, 0, +2.5, +5 cm 位置,
自动记录像素坐标, 拟合线性关系 x_mm = scale * pixel + offset

使用方法:
  1. 确保摆杆水平, 关闭舵机控制
  2. 运行本脚本
  3. 按提示放置球到指定位置, 按回车记录
  4. 自动生成 calibration.json

部署: 拷贝到 K230 SD 卡, 用 CanMV IDE 运行
"""

from libs.PlatTasks import DetectionApp
from libs.PipeLine import PipeLine
from libs.Utils import *
from ybUtils.YbUart import YbUart
import os, gc, ujson, time
from media.media import *
import nncase_runtime as nn

# --- 配置 ---
KMODEL_DIR = "/sdcard/kmodel/"
CALIB_FILE = KMODEL_DIR + "calibration.json"

# 标定点 (mm) — 监视区 ±5cm
CALIB_POINTS_MM = [-50, -25, 0, 25, 50]
CALIB_POINTS_LABEL = ["-5cm", "-2.5cm", "O(中心)", "+2.5cm", "+5cm"]

# 每点采样次数
SAMPLES_PER_POINT = 50

# --- 加载模型配置 ---
deploy_conf = read_json(KMODEL_DIR + "deploy_config.json")
kmodel_path = KMODEL_DIR + deploy_conf["kmodel_path"]
labels = deploy_conf["categories"]
conf_thresh = deploy_conf["confidence_threshold"]
nms_thresh = deploy_conf["nms_threshold"]
model_input_size = deploy_conf["img_size"]
nms_option = deploy_conf["nms_option"]
model_type = deploy_conf["model_type"]
anchors = deploy_conf["anchors"][0] + deploy_conf["anchors"][1] + deploy_conf["anchors"][2]

# --- 初始化 PipeLine (用 PipeLine 因为标定时不需要 RTSP) ---
display_mode = "st7701"
rgb888p_size = [640, 480]
display_size = [640, 480]

pl = PipeLine(rgb888p_size=rgb888p_size, display_size=display_size, display_mode=display_mode)
pl.create()
display_size = pl.get_display_size()

det_app = DetectionApp("video", kmodel_path, labels, model_input_size,
                       anchors, model_type, conf_thresh, nms_thresh,
                       rgb888p_size, display_size, debug_mode=0)
det_app.config_preprocess()

print("=" * 40)
print(" 钢球 5 点标定工具")
print("=" * 40)
print()
print("请准备5个标定位置:")
for i, label in enumerate(CALIB_POINTS_LABEL):
    print("  %d. %s (%d mm)" % (i+1, label, CALIB_POINTS_MM[i]))
print()

# --- 标定过程 ---
calib_pixels = []

for pt_idx in range(len(CALIB_POINTS_MM)):
    label = CALIB_POINTS_LABEL[pt_idx]
    mm_val = CALIB_POINTS_MM[pt_idx]

    print("=" * 40)
    print("标定点 %d/%d: %s (%d mm)" % (pt_idx+1, len(CALIB_POINTS_MM), label, mm_val))
    print("请将钢球放在 %s 位置" % label)
    print("放好后, 按回车开始采集 (CanMV IDE 控制台输入)")
    print("=" * 40)

    # 等待用户输入 (CanMV IDE 支持 input())
    try:
        input()
    except:
        # 如果不支持 input(), 延时 5 秒自动开始
        print("等待 5 秒...")
        time.sleep(5)

    # 采集 SAMPLES_PER_POINT 帧, 取中心 x 的中位数
    cx_list = []
    print("采集中 (%d 帧)..." % SAMPLES_PER_POINT)

    for i in range(SAMPLES_PER_POINT):
        img = pl.get_frame()
        res = det_app.run(img)

        pl.osd_img.clear()

        if res:
            boxes = res.get('boxes', [])
            scores = res.get('scores', [])
            idx = res.get('idx', [])

            best_cx = None
            best_score = 0.0
            for j, box in enumerate(boxes):
                if scores[j] < conf_thresh:
                    continue
                if len(idx) > 0 and idx[j] != 0:
                    continue
                if scores[j] > best_score:
                    best_score = scores[j]
                    x1, y1, x2, y2 = box
                    w = x2 - x1
                    h = y2 - y1
                    if w > 0 and h > 0:
                        best_cx = (x1 + x2) // 2

            if best_cx is not None:
                cx_list.append(best_cx)
                # 画框
                box = boxes[j]
                x1, y1, x2, y2 = box
                w = x2 - x1
                h = y2 - y1
                x1_d = int(x1 * display_size[0] // rgb888p_size[0])
                y1_d = int(y1 * display_size[1] // rgb888p_size[1])
                w_d = int(w * display_size[0] // rgb888p_size[0])
                h_d = int(h * display_size[1] // rgb888p_size[1])
                pl.osd_img.draw_rectangle(x1_d, y1_d, w_d, h_d, color=(0, 255, 0), thickness=3)
                info = "cx=%d score=%.2f (%d/%d)" % (best_cx, best_score, len(cx_list), SAMPLES_PER_POINT)
                pl.osd_img.draw_string_advanced(10, 10, 16, info, color=(255, 255, 0))

        pl.show_image()
        gc.collect()
        time.sleep_ms(20)

    if len(cx_list) < 10:
        print("警告: 只采集到 %d 帧有效数据!" % len(cx_list))

    # 取中位数
    cx_list.sort()
    median_cx = cx_list[len(cx_list) // 2]
    calib_pixels.append(median_cx)

    print("结果: %s → pixel_cx = %d (中位数, %d 帧有效)" % (label, median_cx, len(cx_list)))
    print()

# --- 线性拟合: x_mm = scale * pixel + offset ---
print("=" * 40)
print("线性拟合:")
print("  像素:", calib_pixels)
print("  毫米:", CALIB_POINTS_MM)
print()

# 最小二乘法: y = a*x + b
# y = mm, x = pixel
n = len(calib_pixels)
sum_x = sum(calib_pixels)
sum_y = sum(CALIB_POINTS_MM)
sum_xy = sum(calib_pixels[i] * CALIB_POINTS_MM[i] for i in range(n))
sum_x2 = sum(calib_pixels[i] ** 2 for i in range(n))

scale = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
offset = (sum_y - scale * sum_x) / n

print("  x_mm = %.6f * pixel + %.4f" % (scale, offset))

# 残差
max_residual = 0
for i in range(n):
    predicted = scale * calib_pixels[i] + offset
    residual = abs(predicted - CALIB_POINTS_MM[i])
    if residual > max_residual:
        max_residual = residual
    print("  %s: pixel=%d → predicted=%.2fmm, actual=%dmm, residual=%.2fmm" % (
        CALIB_POINTS_LABEL[i], calib_pixels[i], predicted, CALIB_POINTS_MM[i], residual
    ))

print()
print("  最大残差: %.2f mm" % max_residual)
if max_residual > 2.0:
    print("  ⚠ 残差 > 2mm, 建议检查标定或改用分段线性!")
else:
    print("  ✓ 残差 ≤ 2mm, 标定精度合格")

# --- 保存标定文件 ---
cal_data = {
    "calibrated": True,
    "description": "钢球像素→毫米标定参数 (5点线性拟合)",
    "calibration_date": str(time.time()),
    "pixel_points": {
        "minus5cm": calib_pixels[0],
        "minus2_5cm": calib_pixels[1],
        "center": calib_pixels[2],
        "plus2_5cm": calib_pixels[3],
        "plus5cm": calib_pixels[4]
    },
    "scale": scale,
    "offset": offset,
    "validation": {
        "max_residual_mm": max_residual,
        "samples": SAMPLES_PER_POINT
    },
    "coordinate_def": {
        "x_mm": "中心O为0, 向执行机构端为正, 单位mm",
        "pixel_cx": "钢球检测框中心x坐标 (RGB888 坐标系)",
        "formula": "x_mm = scale * pixel_cx + offset"
    }
}

with open(CALIB_FILE, 'w') as f:
    ujson.dump(cal_data, f)

print()
print("=" * 40)
print("标定完成! 已保存到:", CALIB_FILE)
print("将此文件保留在 SD 卡中, main.py 会自动加载")
print("=" * 40)

# 清理
det_app.deinit()
pl.destroy()
