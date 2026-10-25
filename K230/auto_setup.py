"""
K230 标定工具 (ROI + 位置)
==========================
GC2093 定焦传感器, 无需对焦标定。

交互方式: 纯时间等待, 不需要任何输入
  - 每个步骤开始前等 10 秒 (放球时间)
  - 采集中如果检测到扰动 (帧间跳变), 重新采集
  - 全程持续取帧, 画面不会卡死

生成两个配置文件:
  camera_config.json — ROI (main.py 自动加载)
  calibration.json   — 像素→毫米标定 (main.py 自动加载)
"""

from libs.PipeLine import PipeLine
from libs.PlatTasks import DetectionApp
from libs.Utils import *
from ybUtils.YbUart import YbUart
from media.sensor import *
from media.media import *
import os, gc, ujson, time, sys
import nncase_runtime as nn

# ============== 配置 ==============
KMODEL_DIR = "/sdcard/kmodel/"
CAMERA_CONFIG_FILE = KMODEL_DIR + "camera_config.json"
CALIB_FILE = KMODEL_DIR + "calibration.json"

RGB888P_SIZE = [640, 480]
DISPLAY_SIZE = [640, 480]
DISPLAY_MODE = "st7701"

ROI_MARGIN_TOP = 50
ROI_MARGIN_BOTTOM = 50

CALIB_POINTS_MM = [-50, -25, 0, 25, 50]
CALIB_POINTS_LABEL = ["-5cm", "-2.5cm", "O(中心)", "+2.5cm", "+5cm"]
SAMPLES_PER_POINT = 50

WAIT_SEC = 10           # 每步开始前等待秒数 (放球时间)
JUMP_PX_THRESH = 15     # 采集中帧间跳变超过这么多像素 = 扰动, 重新采集
MAX_RETRY = 5           # 最多重试次数

# ============== 加载模型配置 ==============
deploy_conf = read_json(KMODEL_DIR + "deploy_config.json")
kmodel_path = KMODEL_DIR + deploy_conf["kmodel_path"]
labels = deploy_conf["categories"]
conf_thresh = deploy_conf["confidence_threshold"]
nms_thresh = deploy_conf["nms_threshold"]
model_input_size = deploy_conf["img_size"]
model_type = deploy_conf["model_type"]
anchors = deploy_conf["anchors"][0] + deploy_conf["anchors"][1] + deploy_conf["anchors"][2]

# ============== 初始化 PipeLine + Sensor ==============
print("=" * 50)
print(" K230 标定 (ROI + 位置)")
print("=" * 50)
print("[CAM] GC2093 定焦传感器")

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

det_app = DetectionApp("video", kmodel_path, labels, model_input_size,
                       anchors, model_type, conf_thresh, nms_thresh,
                       RGB888P_SIZE, display_size, debug_mode=0)
det_app.config_preprocess()
print("[DET] DetectionApp 就绪")


# ============== 公共函数 ==============

_gc_counter = 0

def maybe_gc():
    global _gc_counter
    _gc_counter += 1
    if _gc_counter >= 30:
        gc.collect()
        _gc_counter = 0


def detect_ball(img, roi_y_top=None, roi_y_bottom=None):
    res = det_app.run(img)
    if not res:
        return None
    boxes = res.get('boxes', [])
    scores = res.get('scores', [])
    idx = res.get('idx', [])
    best = None
    best_score = 0.0
    for i, box in enumerate(boxes):
        if scores[i] < conf_thresh:
            continue
        if len(idx) > 0 and idx[i] != 0:
            continue
        x1, y1, x2, y2 = box
        w = x2 - x1
        h = y2 - y1
        if w < 10 or w > 100 or h < 10 or h > 100:
            continue
        cy = (y1 + y2) // 2
        if roi_y_top is not None and roi_y_bottom is not None:
            if cy < roi_y_top or cy > roi_y_bottom:
                continue
        if scores[i] > best_score:
            best_score = scores[i]
            best = (int((x1+x2)//2), int(cy), int(w), int(h), scores[i])
    return best


def draw_roi_lines(y_top, y_bottom):
    y_top_d = int(y_top * display_size[1] // RGB888P_SIZE[1])
    y_bot_d = int(y_bottom * display_size[1] // RGB888P_SIZE[1])
    pl.osd_img.draw_line(0, y_top_d, display_size[0], y_top_d, color=(255, 0, 255), thickness=2)
    pl.osd_img.draw_line(0, y_bot_d, display_size[0], y_bot_d, color=(255, 0, 255), thickness=2)


def draw_det_box(det):
    if not det:
        return
    cx, cy, w, h, score = det
    x1_d = int((cx - w//2) * display_size[0] // RGB888P_SIZE[0])
    y1_d = int((cy - h//2) * display_size[1] // RGB888P_SIZE[1])
    w_d = int(w * display_size[0] // RGB888P_SIZE[0])
    h_d = int(h * display_size[1] // RGB888P_SIZE[1])
    pl.osd_img.draw_rectangle(x1_d, y1_d, w_d, h_d, color=(0, 255, 0), thickness=3)


def wait_seconds(sec, prompt_text, det_fn=None, extra_draw=None):
    """
    倒计时等待指定秒数, 全程取帧不卡死。
    屏幕显示倒计时 + 实时检测。
    """
    print(prompt_text)
    print("等待 %d 秒..." % sec)
    t_start = time.ticks_ms()
    wait_ms = sec * 1000

    while True:
        os.exitpoint()
        elapsed = time.ticks_diff(time.ticks_ms(), t_start)
        remaining = (wait_ms - elapsed) // 1000
        if remaining <= 0:
            break

        img = pl.get_frame()
        pl.osd_img.clear()

        det = None
        if det_fn:
            det = det_fn(img)

        if det:
            draw_det_box(det)

        if extra_draw:
            extra_draw(pl.osd_img)

        pl.osd_img.draw_string_advanced(10, 10, 22, prompt_text, color=(255, 255, 255))

        if det:
            status = "BALL OK  cx=%d" % det[0]
            color = (0, 255, 0)
        else:
            status = "no ball..."
            color = (255, 255, 0)

        pl.osd_img.draw_string_advanced(10, 44, 20, "%ds  %s" % (remaining, status), color=color)
        pl.show_image()
        maybe_gc()

    print("开始采集!")


def collect_stable(num_frames, label, det_fn, extra_draw=None):
    """
    采集指定帧数, 带扰动检测。
    如果某帧位置跟上一帧跳变超过 JUMP_PX_THRESH, 整个采集重来。
    最多重试 MAX_RETRY 次, 超过就用最后一次结果。
    """
    for attempt in range(MAX_RETRY):
        print("采集中 (%d 帧)... 尝试 %d/%d" % (num_frames, attempt+1, MAX_RETRY))
        cx_list = []
        last_cx = None
        jumped = False

        for i in range(num_frames):
            os.exitpoint()
            img = pl.get_frame()
            det = det_fn(img)

            pl.osd_img.clear()
            if extra_draw:
                extra_draw(pl.osd_img)

            if det:
                cx, cy, w, h, score = det
                cx_list.append(cx)

                # 扰动检测: 跟上一帧比
                if last_cx is not None:
                    dx = abs(cx - last_cx)
                    if dx > JUMP_PX_THRESH:
                        jumped = True
                        print("  扰动! frame %d: dx=%d > %d, 重新采集" % (i, dx, JUMP_PX_THRESH))
                        # 显示扰动警告
                        draw_det_box(det)
                        pl.osd_img.draw_string_advanced(10, 10, 18,
                            "%s JUMP! dx=%d retry" % (label, dx), color=(255, 0, 0))
                        pl.show_image()
                        maybe_gc()
                        drain_frames(1000)  # 停 1 秒让你看到
                        break
                last_cx = cx

                draw_det_box(det)
                info = "%s cx=%d (%d/%d)" % (label, cx, len(cx_list), num_frames)
                pl.osd_img.draw_string_advanced(10, 10, 16, info, color=(255, 255, 0))
            else:
                info = "%s no ball (%d/%d)" % (label, i, num_frames)
                pl.osd_img.draw_string_advanced(10, 10, 16, info, color=(255, 0, 0))
            pl.show_image()
            maybe_gc()

        if not jumped:
            # 没扰动, 采集成功
            if len(cx_list) >= 10:
                cx_list.sort()
                median_cx = cx_list[len(cx_list) // 2]
                print("结果: %s -> cx=%d (%d frames)" % (label, median_cx, len(cx_list)))
                return cx_list, median_cx
            else:
                print("有效帧不够 (%d), 重试" % len(cx_list))
        # 有扰动或帧不够, 继续重试

    # 超过重试次数, 用最后一次结果
    print("超过最大重试次数, 使用最后结果")
    if cx_list:
        cx_list.sort()
        median_cx = cx_list[len(cx_list) // 2]
        return cx_list, median_cx
    return [], None


def drain_frames(duration_ms, draw_fn=None):
    t_start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t_start) < duration_ms:
        os.exitpoint()
        pl.get_frame()
        pl.osd_img.clear()
        if draw_fn:
            draw_fn(pl.osd_img)
        pl.show_image()
        maybe_gc()


# ================================================================
#  Phase 1: ROI 检测
# ================================================================
print("\n" + "=" * 50)
print(" Phase 1: ROI 检测")
print("=" * 50)

wait_seconds(WAIT_SEC, "Phase1: 把球放在管子上", det_fn=detect_ball)

cy_list_raw, _ = collect_stable(30, "ROI", detect_ball)

cy_list = []
ball_h_max = 0
# 重新采集球的高度信息 (collect_stable 只存了 cx, 这里需要 cy/h)
for i in range(30):
    os.exitpoint()
    img = pl.get_frame()
    det = detect_ball(img)
    pl.osd_img.clear()
    if det:
        cx, cy, w, h, score = det
        cy_list.append(cy)
        if h > ball_h_max:
            ball_h_max = h
        draw_det_box(det)
        info = "ROI cy=%d h=%d (%d/30)" % (cy, h, len(cy_list))
        pl.osd_img.draw_string_advanced(10, 10, 16, info, color=(255, 255, 0))
    else:
        pl.osd_img.draw_string_advanced(10, 10, 16, "no ball (%d/30)" % i, color=(255, 0, 0))
    pl.show_image()
    maybe_gc()

if len(cy_list) < 10:
    print("错误: 只检测到 %d 帧有效数据!" % len(cy_list))
    det_app.deinit()
    pl.destroy()
    sys.exit()

cy_list.sort()
median_cy = cy_list[len(cy_list) // 2]
half_h = ball_h_max // 2
roi_y_top = max(0, median_cy - half_h - ROI_MARGIN_TOP)
roi_y_bottom = min(RGB888P_SIZE[1], median_cy + half_h + ROI_MARGIN_BOTTOM)

print("球中心 Y: %d, 球高度: %d" % (median_cy, ball_h_max))
print("ROI: Y[%d ~ %d] (高度 %d)" % (roi_y_top, roi_y_bottom, roi_y_bottom - roi_y_top))

def _draw_roi_confirm(osd):
    draw_roi_lines(roi_y_top, roi_y_bottom)
    info = "ROI: Y[%d~%d] h=%d" % (roi_y_top, roi_y_bottom, roi_y_bottom - roi_y_top)
    osd.draw_string_advanced(10, 10, 16, info, color=(255, 0, 255))

drain_frames(3000, _draw_roi_confirm)
print("Phase 1 完成\n")


# ================================================================
#  Phase 2: 位置标定 (±5cm 五点)
# ================================================================
print("=" * 50)
print(" Phase 2: 位置标定 (+/-5cm 5-point)")
print("=" * 50)
print("标定位置:")
for i, label in enumerate(CALIB_POINTS_LABEL):
    print("  %d. %s (%d mm)" % (i+1, label, CALIB_POINTS_MM[i]))
print()

def _draw_roi_for_calib(osd):
    draw_roi_lines(roi_y_top, roi_y_bottom)

calib_pixels = []

for pt_idx in range(len(CALIB_POINTS_MM)):
    label = CALIB_POINTS_LABEL[pt_idx]
    mm_val = CALIB_POINTS_MM[pt_idx]

    print("-" * 40)
    print("标定点 %d/%d: %s (%d mm)" % (pt_idx+1, len(CALIB_POINTS_MM), label, mm_val))

    wait_seconds(WAIT_SEC, "P%d: 把球放在 %s (%dmm)" % (pt_idx+1, label, mm_val),
                 det_fn=lambda img: detect_ball(img, roi_y_top, roi_y_bottom),
                 extra_draw=_draw_roi_for_calib)

    _, median_cx = collect_stable(
        SAMPLES_PER_POINT, label,
        det_fn=lambda img: detect_ball(img, roi_y_top, roi_y_bottom),
        extra_draw=_draw_roi_for_calib)

    if median_cx is None:
        print("错误: %s 采集失败!" % label)
        median_cx = 0

    calib_pixels.append(median_cx)

    # 每个点采完停 2 秒看结果
    def _draw_result(osd, _label=label, _cx=median_cx):
        draw_roi_lines(roi_y_top, roi_y_bottom)
        osd.draw_string_advanced(10, 10, 18, "%s done: cx=%d" % (_label, _cx), color=(0, 255, 0))
    drain_frames(2000, _draw_result)

print("Phase 2 完成\n")


# ================================================================
#  线性拟合
# ================================================================
print("=" * 50)
print(" 线性拟合")
print("=" * 50)
print("  像素:", calib_pixels)
print("  毫米:", CALIB_POINTS_MM)

n = len(calib_pixels)
sum_x = sum(calib_pixels)
sum_y = sum(CALIB_POINTS_MM)
sum_xy = sum(calib_pixels[i] * CALIB_POINTS_MM[i] for i in range(n))
sum_x2 = sum(calib_pixels[i] ** 2 for i in range(n))

scale = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
offset = (sum_y - scale * sum_x) / n

print("  x_mm = %.6f * pixel + %.4f" % (scale, offset))

max_residual = 0
for i in range(n):
    predicted = scale * calib_pixels[i] + offset
    residual = abs(predicted - CALIB_POINTS_MM[i])
    if residual > max_residual:
        max_residual = residual
    print("  %s: pixel=%d -> %.2fmm, actual=%dmm, err=%.2fmm" % (
        CALIB_POINTS_LABEL[i], calib_pixels[i], predicted, CALIB_POINTS_MM[i], residual))

print("\n  max residual: %.2f mm" % max_residual)
if max_residual > 2.0:
    print("  WARNING: residual > 2mm!")
else:
    print("  OK: residual <= 2mm")


# ================================================================
#  保存配置文件
# ================================================================
cam_config = {
    "sensor": "GC2093",
    "focus": "fixed",
    "roi_y_top": roi_y_top,
    "roi_y_bottom": roi_y_bottom,
    "roi_height": roi_y_bottom - roi_y_top,
    "ball_cy_median": median_cy,
    "ball_h_max": ball_h_max,
    "calibration_date": str(time.time())
}
with open(CAMERA_CONFIG_FILE, 'w') as f:
    ujson.dump(cam_config, f)
print("\n[CAM] saved:", CAMERA_CONFIG_FILE)

cal_data = {
    "calibrated": True,
    "description": "pixel->mm calibration (5-point linear, +/-5cm)",
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
        "x_mm": "center O=0, toward actuator=positive, unit mm",
        "pixel_cx": "ball detection box center x (RGB888 coords)",
        "formula": "x_mm = scale * pixel_cx + offset"
    }
}
with open(CALIB_FILE, 'w') as f:
    ujson.dump(cal_data, f)
print("[CAL] saved:", CALIB_FILE)


# ================================================================
#  总结
# ================================================================
print("\n" + "=" * 50)
print(" All calibration done!")
print("=" * 50)
print("  Sensor: GC2093 (fixed focus)")
print("  ROI:    Y[%d ~ %d] (h=%d)" % (roi_y_top, roi_y_bottom, roi_y_bottom - roi_y_top))
print("  Calib:  x_mm = %.4f * pixel + %.2f" % (scale, offset))
print("  Residual: %.2f mm" % max_residual)
print()
print("Config files saved, main.py will auto-load")
print("=" * 50)

det_app.deinit()
pl.destroy()
