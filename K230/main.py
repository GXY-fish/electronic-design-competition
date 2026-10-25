"""
K230 H题 钢球视觉测量 (PipeLine版)
==================================================
功能:
  1. YOLO 钢球检测 (Pro-Hmf 模型)
  2. 像素→毫米标定 (5点线性)
  3. alpha-beta 速度滤波 + 帧间差分速度 (双速度对比)
  4. 15字节二进制 UART 帧发送给 MSPM0 (含双速度)
  5. WiFi AP (RTSP 后续再加)
  6. IDE 预览 + OSD 叠加检测框/位置/速度

硬件接线:
  K230 TXD (IO9)  -> MSPM0 PA25 (UART RX)
  K230 RXD (IO10) -> MSPM0 PA26 (UART TX)
  K230 GND         -> MSPM0 GND

部署步骤:
  1. 拷贝以下文件到 K230 SD 卡 /sdcard/kmodel/:
     - best_AnchorBaseDet_can2_5_s_20260726145328.kmodel
     - deploy_config.json
     - calibration.json
  2. 用 CanMV IDE 运行本脚本
"""

import network
import os
import time
import gc
import ujson
from libs.PipeLine import PipeLine, ScopedTiming
from libs.PlatTasks import DetectionApp
from libs.Utils import *
from ybUtils.YbUart import YbUart
from media.sensor import *
from media.media import *

# ====================================================================
#  配置常量
# ====================================================================

# --- WiFi AP 配置 (RTSP 暂未启用, 先开着热点方便后续测试) ---
WIFI_SSID = "K230_H"
WIFI_PASS = "12345678"

# --- 传感器分辨率 ---
RGB888P_SIZE = [640, 480]
DISPLAY_SIZE = [640, 480]
DISPLAY_MODE = "st7701"

# --- UART 配置 ---
UART_BAUD = 115200

# --- 摄像头配置 ---
# GC2093 是定焦传感器, 不支持 focus_pos / auto_focus
# 不需要任何对焦设置, 固定焦距由镜头硬件决定
CAM_AUTO_EXPOSURE = False    # False=关闭自动曝光
CAM_EXPOSURE_US = None       # None=不设置, 数字=手动曝光时间(us), 典型 5000~20000

# --- ROI 遮罩配置 ---
# 只保留白管区域 (水平条带), 上下填黑, 减少环境干扰
# 优先从 camera_config.json 加载; 这里设 None 表示从配置文件读取
ROI_Y_TOP = None             # None=从配置文件加载, 数字=手动指定 (RGB888 坐标系 Y)
ROI_Y_BOTTOM = None          # None=从配置文件加载

# --- 模型路径 ---
KMODEL_DIR = "/sdcard/kmodel/"
CALIB_FILE = KMODEL_DIR + "calibration.json"
CAMERA_CONFIG_FILE = KMODEL_DIR + "camera_config.json"

# --- Alpha-Beta 滤波参数 ---
# 调参说明: alpha 越大位置跟踪越快但噪声越大; beta 越大速度收敛越快但噪声越大
# 老师手册建议: alpha=0.65~0.85, beta=0.05~0.20
# 之前 alpha=0.75/beta=0.10 速度严重滞后, 调高以加快跟踪
ALPHA = 0.85   # 位置修正系数
BETA = 0.35    # 速度修正系数 (0.18→0.35: 40fps下速度收敛快一倍)
RESIDUAL_CLAMP_MM = 80  # 速度更新残差限幅(mm), 防止丢球重出现时速度尖峰
LOST_REINIT_FRAMES = 3  # 丢球超过这么多帧, 重新出现时重置滤波器

# --- 帧间差分速度参数 ---
# 帧间差分 = (当前位置 - 上帧位置) / dt, 零滞后
# 一阶低通压噪: v_filt = LP_ALPHA * v_raw + (1-LP_ALPHA) * v_prev
V_DIFF_LP_ALPHA = 0.6   # 低通系数 (0.6=新值权重, 截止约10Hz@33fps)

# --- 诊断模式 ---
# 开启后每帧打印推理耗时、dt、滤波前后位置/速度, 用于定位瓶颈
DIAG_MODE = False
DIAG_INTERVAL = 10  # 每10帧打印一次诊断 (避免刷屏)

# --- 安全参数 ---
V_MAX = 1500          # 速度限幅 mm/s
X_MAX = 120           # 位置限幅 mm (摆杆 ±12cm)
CONF_MIN = 50         # 最低置信度阈值
LOST_TIMEOUT_MS = 200 # 丢球超时 ms

# --- 关联逻辑参数 ---
# NOTE: 最近邻关联 (MAX_JUMP_PX) 已移除 — 会误拒快速移动的有效检测, 导致螺旋丢失
#       如比赛中误检横跳严重, 可加回软关联: 不硬拒, 而是降低远处检测的置信度
MIN_BOX_W = 10        # 检测框最小宽度 (像素), 排除噪点
MAX_BOX_W = 100       # 检测框最大宽度 (像素), 排除大片反光
MIN_BOX_H = 10        # 检测框最小高度
MAX_BOX_H = 100       # 检测框最大高度

# --- UART 帧标志位 ---
FLAG_VALID = 0x01
FLAG_LOST  = 0x02
FLAG_CAL_OK = 0x04


# ====================================================================
#  CRC8 校验
# ====================================================================
def crc8(data):
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


# ====================================================================
#  UART 二进制帧打包 (15字节, 双速度)
#  [AA][55][0B][SEQ][T_MS×2][X_MM×2][V_AB×2][V_DF×2][CONF][FLAGS][CRC8]
#  V_AB = alpha-beta 滤波速度, V_DF = 帧间差分速度
# ====================================================================
def pack_ball_frame(seq, t_ms, x_mm, v_ab, v_df, conf, flags):
    buf = bytearray(15)
    buf[0] = 0xAA
    buf[1] = 0x55
    buf[2] = 0x0B  # LEN: SEQ~FLAGS 共 11 字节
    buf[3] = seq & 0xFF
    buf[4] = t_ms & 0xFF
    buf[5] = (t_ms >> 8) & 0xFF
    buf[6] = x_mm & 0xFF
    buf[7] = (x_mm >> 8) & 0xFF
    buf[8] = v_ab & 0xFF
    buf[9] = (v_ab >> 8) & 0xFF
    buf[10] = v_df & 0xFF
    buf[11] = (v_df >> 8) & 0xFF
    buf[12] = conf & 0xFF
    buf[13] = flags & 0xFF
    buf[14] = crc8(buf[2:14])  # CRC: LEN~FLAGS 共 12 字节
    return bytes(buf)


def clamp_int16(val):
    if val > 32767: return 32767
    if val < -32768: return -32768
    return val


def clamp_x(val):
    """位置限幅到 ±X_MAX"""
    if val > X_MAX: return X_MAX
    if val < -X_MAX: return -X_MAX
    return val


# ====================================================================
#  Alpha-Beta 速度滤波器
# ====================================================================
class AlphaBetaFilter:
    def __init__(self, alpha=0.75, beta=0.10):
        self.alpha = alpha
        self.beta = beta
        self.x_est = 0.0
        self.v_est = 0.0
        self.last_t_ms = None
        self.initialized = False
        self.lost_count = 0

    def update(self, x_meas_mm, t_ms, confidence=100):
        if confidence < CONF_MIN:
            self.lost_count += 1
            return clamp_x(self._predict(t_ms)), 0

        # ★丢球太久, 重新出现时重置滤波器, 防止位置跳变导致速度尖峰
        if self.lost_count > LOST_REINIT_FRAMES:
            self.x_est = float(x_meas_mm)
            self.v_est = 0.0
            self.last_t_ms = t_ms
            self.lost_count = 0
            self.initialized = True
            return clamp_x(int(self.x_est)), 0

        self.lost_count = 0

        if not self.initialized:
            self.x_est = float(x_meas_mm)
            self.v_est = 0.0
            self.last_t_ms = t_ms
            self.initialized = True
            return clamp_x(int(self.x_est)), 0

        dt = (t_ms - self.last_t_ms) / 1000.0
        if dt < 0.001: dt = 0.001
        if dt > 0.050: dt = 0.050

        x_pred = self.x_est + self.v_est * dt
        residual = float(x_meas_mm) - x_pred

        self.x_est = x_pred + self.alpha * residual

        # ★残差限幅: 防止大跳变时速度爆炸
        r_clamped = residual
        if r_clamped > RESIDUAL_CLAMP_MM: r_clamped = RESIDUAL_CLAMP_MM
        if r_clamped < -RESIDUAL_CLAMP_MM: r_clamped = -RESIDUAL_CLAMP_MM
        self.v_est = self.v_est + (self.beta / dt) * r_clamped

        if self.v_est > V_MAX: self.v_est = V_MAX
        if self.v_est < -V_MAX: self.v_est = -V_MAX

        self.last_t_ms = t_ms
        return clamp_x(int(self.x_est)), int(self.v_est)

    def get_state(self):
        """返回当前内部状态, 供诊断使用"""
        return self.x_est, self.v_est, self.initialized, self.lost_count

    def _predict(self, t_ms):
        if not self.initialized: return 0
        dt = (t_ms - self.last_t_ms) / 1000.0
        if dt < 0.001: dt = 0.001
        if dt > 0.050: dt = 0.050
        self.x_est = self.x_est + self.v_est * dt
        self.last_t_ms = t_ms
        if self.lost_count > 2:
            self.v_est *= 0.5
        if self.lost_count > 5:
            self.v_est = 0.0
        return int(self.x_est)

    def reset(self):
        self.x_est = 0.0
        self.v_est = 0.0
        self.last_t_ms = None
        self.initialized = False
        self.lost_count = 0


# ====================================================================
#  标定: 像素 → 毫米
# ====================================================================
def load_calibration():
    try:
        with open(CALIB_FILE, 'r') as f:
            cal = ujson.load(f)
        if cal.get("calibrated", False):
            print("[CAL] 标定已加载: scale=%.4f offset=%.2f" % (cal["scale"], cal["offset"]))
            return cal
        else:
            print("[CAL] 标定文件存在但未标定, 使用默认值")
            return None
    except Exception as e:
        print("[CAL] 无标定文件, 使用默认值")
        return None


# ====================================================================
#  摄像头配置加载 (焦距 + ROI)
# ====================================================================
def load_camera_config():
    """从 camera_config.json 加载ROI (由 auto_setup.py 生成)"""
    roi_top = ROI_Y_TOP
    roi_bot = ROI_Y_BOTTOM
    try:
        with open(CAMERA_CONFIG_FILE, 'r') as f:
            cfg = ujson.load(f)
        if roi_top is None:
            roi_top = cfg.get("roi_y_top", None)
        if roi_bot is None:
            roi_bot = cfg.get("roi_y_bottom", None)
        if roi_top is not None and roi_bot is not None:
            print("[CAM] 从配置加载ROI: Y[%d~%d]" % (roi_top, roi_bot))
    except Exception as e:
        print("[CAM] 无 camera_config.json, 使用代码中的值")
    return roi_top, roi_bot


# NOTE: ROI 遮罩 (apply_roi_mask) 已移除
# 原因: ulab.numpy 不支持多维切片赋值 img[c,:y_top,:]=0,
#   fallback 逐行填零在 640x480 图像上极慢, 导致严重卡顿
# 替代方案: 在检测结果后处理层面做 Y 坐标过滤 (见主循环 8b)


def pixel_to_mm(pixel_cx, cal):
    """
    像素坐标 → 毫米位置
    中心 O 为 0, 向执行机构端为正
    """
    if cal is None:
        # 默认: 中心像素320=0mm, 每像素0.5mm (与 calibration.json 模板一致)
        x_mm = int((pixel_cx - 320) * 0.5)
    else:
        x_mm = int(cal["scale"] * pixel_cx + cal["offset"])
    # 无论哪种情况都限幅
    return clamp_x(x_mm)


# ====================================================================
#  WiFi AP 模式启动
# ====================================================================
def setup_wifi_ap():
    print("[WIFI] 启动 AP 模式...")
    ap = network.WLAN(network.AP_IF)
    try:
        ap.active(True)
    except:
        pass  # "Network is always active" 报错可忽略
    ap.config(ssid=WIFI_SSID, key=WIFI_PASS)
    time.sleep(3)
    try:
        ip = ap.ifconfig()[0]
    except:
        ip = "192.168.169.1"
    print("[WIFI] AP 就绪, SSID=%s, IP=%s" % (WIFI_SSID, ip))
    return ip


# ====================================================================
#  主程序
# ====================================================================
def main():
    print("=" * 50)
    print(" K230 H题 钢球视觉测量 (PipeLine版)")
    print("=" * 50)

    # === 1. WiFi AP (RTSP 后续再加, 先开热点) ===
    setup_wifi_ap()

    # === 2. 加载标定 ===
    cal = load_calibration()

    # === 2b. 加载摄像头配置 (ROI) ===
    roi_y_top, roi_y_bottom = load_camera_config()

    # === 3. 读取模型配置 ===
    print("[MODEL] 加载 deploy_config.json...")
    deploy_conf = read_json(KMODEL_DIR + "deploy_config.json")
    kmodel_path = KMODEL_DIR + deploy_conf["kmodel_path"]
    labels = deploy_conf["categories"]
    conf_thresh = deploy_conf["confidence_threshold"]
    nms_thresh = deploy_conf["nms_threshold"]
    model_input_size = deploy_conf["img_size"]
    model_type = deploy_conf["model_type"]
    anchors = deploy_conf["anchors"][0] + deploy_conf["anchors"][1] + deploy_conf["anchors"][2]

    print("[MODEL] kmodel:", kmodel_path)
    print("[MODEL] labels:", labels)
    print("[MODEL] input:", model_input_size)
    print("[MODEL] conf_thresh:", conf_thresh)

    # === 4. UART 初始化 (二进制帧) ===
    print("[UART] 初始化, baudrate=%d..." % UART_BAUD)
    try:
        yb_uart = YbUart(baudrate=UART_BAUD)
        raw_uart = None
        for attr in ('uart', '_uart', 'dev', '_dev'):
            if hasattr(yb_uart, attr):
                raw_uart = getattr(yb_uart, attr)
                break
        if raw_uart is None:
            print("[UART] 使用 YbUart.send() 模式")
            raw_uart = yb_uart
        else:
            print("[UART] 获取到底层 UART 对象")
    except Exception as e:
        print("[UART] 初始化失败:", e)
        raw_uart = None

    def uart_send(data_bytes):
        if raw_uart is None: return
        try:
            if hasattr(raw_uart, 'write'):
                raw_uart.write(data_bytes)
            elif hasattr(raw_uart, 'send'):
                raw_uart.send(data_bytes)
        except Exception as e:
            print("[UART] 发送错误:", e)

    # === 5. PipeLine 初始化 (传感器 + 显示 + AI帧) ===
    print("[PIPE] 初始化 PipeLine...")

    # 创建自定义 Sensor 实例, 在 run() 之前设置对焦/曝光
    cam_sensor = Sensor()
    cam_sensor.reset()

    # --- 5a. 对焦控制 (GC2093 定焦, 跳过) ---
    print("[CAM] GC2093 定焦传感器, 无对焦控制")

    # --- 5b. 曝光控制 (auto_exposure 必须在 run() 之前) ---
    try:
        if not CAM_AUTO_EXPOSURE:
            cam_sensor.auto_exposure(False)
            print("[CAM] 自动曝光: 关闭")
        else:
            cam_sensor.auto_exposure(True)
            print("[CAM] 自动曝光: 开启")
    except Exception as e:
        print("[CAM] 曝光设置失败:", e)

    # 传入自定义 sensor 给 PipeLine
    pl = PipeLine(rgb888p_size=RGB888P_SIZE, display_size=DISPLAY_SIZE,
                  display_mode=DISPLAY_MODE)
    pl.create(sensor=cam_sensor)
    display_size = pl.get_display_size()
    print("[PIPE] PipeLine 就绪, display_size=%s" % str(display_size))

    # --- 5c. 手动设置曝光时间 (必须在 run() 之后) ---
    if not CAM_AUTO_EXPOSURE and CAM_EXPOSURE_US is not None:
        try:
            cam_sensor.exposure(CAM_EXPOSURE_US)
            print("[CAM] 固定曝光: %d us" % CAM_EXPOSURE_US)
        except Exception as e:
            print("[CAM] 曝光设置失败:", e)

    # === 6. DetectionApp 初始化 ===
    print("[DET] 初始化 DetectionApp...")
    det_app = DetectionApp(
        "video", kmodel_path, labels, model_input_size,
        anchors, model_type, conf_thresh, nms_thresh,
        RGB888P_SIZE, display_size, debug_mode=0
    )
    det_app.config_preprocess()
    print("[DET] DetectionApp 就绪")

    # === 7. 初始化滤波器和状态 ===
    ab_filter = AlphaBetaFilter(ALPHA, BETA)
    seq = 0
    frame_count = 0
    fps_count = 0
    fps_timer = time.ticks_ms()
    fps_value = 0
    last_detect_t = 0
    lost_frame_count = 0

    # 帧间差分速度状态
    prev_x_mm = None      # 上帧原始位置 (mm)
    prev_t_ms = None       # 上帧时间戳 (ms)
    v_diff_filt = 0.0      # 差分速度低通滤波值

    # 诊断计时
    t_inf_total = 0   # 累计推理时间
    t_osd_total = 0   # 累计OSD时间
    t_uart_total = 0  # 累计UART时间
    diag_count = 0    # 诊断帧计数

    time.sleep(1)  # 等传感器稳定
    print("[MAIN] 主循环开始!")
    print("-" * 50)

    # === 8. 主循环 ===
    try:
        while True:
            os.exitpoint()  # ← 必须! CanMV IDE 靠这个停止脚本

            t_now = time.ticks_ms()

            # --- 8a. 获取帧 → YOLO 推理 ---
            # NOTE: 不做 numpy 层面的 ROI 遮罩 (ulab 不支持切片赋值, 会导致卡顿)
            #       ROI 过滤在后处理层面做 (见 8b 的 Y 坐标过滤)
            t_inf_start = time.ticks_ms()
            img = pl.get_frame()
            res = det_app.run(img)
            t_inf_end = time.ticks_ms()

            pl.osd_img.clear()

            # --- 8b. 筛选钢球检测 (尺寸过滤 + 最高置信度) ---
            best_cx = None
            best_conf = 0
            best_box = None

            if res:
                boxes = res.get('boxes', [])
                scores = res.get('scores', [])
                idx = res.get('idx', [])

                for i, box in enumerate(boxes):
                    if scores[i] < conf_thresh:
                        continue
                    if len(idx) > 0 and idx[i] != 0:
                        continue
                    x1, y1, x2, y2 = box
                    w = x2 - x1
                    h = y2 - y1
                    # 尺寸过滤: 排除过大/过小的检测框
                    if w < MIN_BOX_W or w > MAX_BOX_W:
                        continue
                    if h < MIN_BOX_H or h > MAX_BOX_H:
                        continue
                    # ROI 软过滤: 检测中心Y必须在白管区域内
                    cy_det = (y1 + y2) // 2
                    if roi_y_top is not None and roi_y_bottom is not None:
                        if cy_det < roi_y_top or cy_det > roi_y_bottom:
                            continue
                    if scores[i] > best_conf:
                        best_conf = scores[i]
                        best_cx = (x1 + x2) // 2
                        best_box = (int(x1), int(y1), int(w), int(h))

                if best_cx is not None:
                    best_conf = int(best_conf * 100)

            # --- 8c. 标定 + 双速度计算 ---
            x_meas_mm = None  # 诊断用: 原始测量值
            if best_cx is not None:
                x_mm_raw = pixel_to_mm(best_cx, cal)
                x_meas_mm = x_mm_raw

                # (1) Alpha-Beta 滤波器: 位置 + 速度 (有滞后, 但平滑)
                x_mm, v_ab = ab_filter.update(x_mm_raw, t_now, best_conf)

                # (2) 帧间差分速度: 零滞后, 轻量低通压噪
                if prev_x_mm is not None:
                    dt_diff = (t_now - prev_t_ms) / 1000.0
                    if dt_diff < 0.001: dt_diff = 0.001
                    if dt_diff > 0.050: dt_diff = 0.050
                    v_raw_diff = (x_mm_raw - prev_x_mm) / dt_diff
                    v_diff_filt = V_DIFF_LP_ALPHA * v_raw_diff + (1.0 - V_DIFF_LP_ALPHA) * v_diff_filt
                else:
                    v_diff_filt = 0.0
                prev_x_mm = x_mm_raw
                prev_t_ms = t_now

                flags = FLAG_VALID
                if cal is not None:
                    flags |= FLAG_CAL_OK
                lost_frame_count = 0
                last_detect_t = t_now
            else:
                lost_frame_count += 1
                x_mm, v_ab = ab_filter.update(0, t_now, 0)
                # 丢球时差分速度衰减
                v_diff_filt *= 0.5
                if (t_now - last_detect_t) > LOST_TIMEOUT_MS:
                    flags = FLAG_LOST
                else:
                    flags = FLAG_VALID

            x_mm = clamp_int16(x_mm)
            v_ab = clamp_int16(v_ab)
            v_diff = clamp_int16(int(v_diff_filt))
            if v_diff > V_MAX: v_diff = V_MAX
            if v_diff < -V_MAX: v_diff = -V_MAX

            # --- 8d. 发送 UART 二进制帧 (15字节, 双速度) ---
            t_uart_start = time.ticks_ms()
            t_ms = t_now & 0xFFFF
            conf_send = best_conf if best_cx is not None else 0
            frame = pack_ball_frame(seq, t_ms, x_mm, v_ab, v_diff, conf_send, flags)
            uart_send(frame)
            seq = (seq + 1) & 0xFF
            t_uart_end = time.ticks_ms()

            # --- 8e. 画 OSD (检测框 + 信息) ---
            if best_box is not None:
                x1, y1, w, h = best_box
                # 坐标从 rgb888p 缩放到 display_size
                x1_d = int(x1 * display_size[0] // RGB888P_SIZE[0])
                y1_d = int(y1 * display_size[1] // RGB888P_SIZE[1])
                w_d = int(w * display_size[0] // RGB888P_SIZE[0])
                h_d = int(h * display_size[1] // RGB888P_SIZE[1])
                pl.osd_img.draw_rectangle(x1_d, y1_d, w_d, h_d,
                                          color=(0, 255, 0), thickness=3)

            # 信息文字
            x_cm = x_mm / 10.0
            v_ab_cm = v_ab / 10.0
            v_df_cm = v_diff / 10.0
            status = "OK"
            if flags & FLAG_LOST:
                status = "LOST"
            elif flags == 0:
                status = "WAIT"

            info = "x=%.1fcm vab=%.1f vdf=%.1fcm/s conf=%d %s fps=%d" % (
                x_cm, v_ab_cm, v_df_cm, conf_send, status, fps_value)
            pl.osd_img.draw_string_advanced(10, 10, 16, info, color=(255, 255, 0))

            # ROI 指示线 (品红色横线标示白管区域)
            if roi_y_top is not None and roi_y_bottom is not None:
                y_top_d = int(roi_y_top * display_size[1] // RGB888P_SIZE[1])
                y_bot_d = int(roi_y_bottom * display_size[1] // RGB888P_SIZE[1])
                pl.osd_img.draw_line(0, y_top_d, display_size[0]-1, y_top_d, color=(255, 0, 255), thickness=1)
                pl.osd_img.draw_line(0, y_bot_d, display_size[0]-1, y_bot_d, color=(255, 0, 255), thickness=1)

            pl.show_image()
            t_osd_end = time.ticks_ms()

            # --- 8f. 调试输出 + 诊断 ---
            frame_count += 1

            # 累计各阶段耗时
            t_inf_total += time.ticks_diff(t_inf_end, t_inf_start)
            t_osd_total += time.ticks_diff(t_osd_end, t_uart_end)
            t_uart_total += time.ticks_diff(t_uart_end, t_uart_start)
            diag_count += 1

            # 常规输出 (每50帧)
            if frame_count % 50 == 0:
                print("[DET] x=%.1fcm vab=%.1f vdf=%.1fcm/s conf=%d flags=0x%02X fps=%d" % (
                    x_cm, v_ab_cm, v_df_cm, conf_send, flags, fps_value))

            # 诊断输出 (DIAG_MODE开启时)
            if DIAG_MODE and frame_count % DIAG_INTERVAL == 0:
                x_est_f, v_est_f, init_f, lost_f = ab_filter.get_state()
                dt_ms = time.ticks_diff(t_now, ab_filter.last_t_ms) if ab_filter.last_t_ms else 0
                meas_str = "%d" % x_meas_mm if x_meas_mm is not None else "none"
                print("[DIAG] inf=%dms osd=%dms uart=%dms | dt=%dms meas=%s est=%.1f v_ab=%.1f v_df=%.1f | fps=%d" % (
                    time.ticks_diff(t_inf_end, t_inf_start),
                    time.ticks_diff(t_osd_end, t_uart_end),
                    time.ticks_diff(t_uart_end, t_uart_start),
                    dt_ms, meas_str, x_est_f, v_est_f, v_diff_filt, fps_value))

            # 周期性汇总 (每100帧)
            if frame_count % 100 == 0 and diag_count > 0:
                print("[PERF] avg: inf=%.1fms osd=%.1fms uart=%.1fms total=%.1fms → est_fps=%.0f" % (
                    t_inf_total / diag_count,
                    t_osd_total / diag_count,
                    t_uart_total / diag_count,
                    (t_inf_total + t_osd_total + t_uart_total) / diag_count,
                    1000.0 / ((t_inf_total + t_osd_total + t_uart_total) / diag_count)))
                t_inf_total = 0
                t_osd_total = 0
                t_uart_total = 0
                diag_count = 0

            # --- 8g. FPS 统计 ---
            fps_count += 1
            if time.ticks_diff(time.ticks_ms(), fps_timer) >= 1000:
                fps_value = fps_count
                fps_count = 0
                fps_timer = time.ticks_ms()

            # gc.collect() 每30帧一次, 不再每帧调用 (节省2-5ms/帧)
            if frame_count % 30 == 0:
                gc.collect()

    except KeyboardInterrupt:
        print("\n[MAIN] 用户中断")
    except Exception as e:
        print("[MAIN] 异常:", e)
    finally:
        print("[MAIN] 清理资源...")
        try:
            det_app.deinit()
        except:
            pass
        try:
            pl.destroy()
        except:
            pass
        print("[MAIN] 已退出")


# ====================================================================
#  入口
# ====================================================================
if __name__ == "__main__":
    os.exitpoint(os.EXITPOINT_ENABLE)
    main()
