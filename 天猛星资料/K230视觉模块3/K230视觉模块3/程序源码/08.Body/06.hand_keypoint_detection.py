from libs.PipeLine import PipeLine, ScopedTiming  # 导入Pipeline和计时器类 / Import Pipeline and timing classes
from libs.AIBase import AIBase  # 导入AI基础类 / Import AI base class
from libs.AI2D import Ai2d  # 导入AI2D类用于图像预处理 / Import AI2D for image preprocessing
import os
import ujson
from media.media import *  # 导入媒体相关模块 / Import media related modules
from time import *
import nncase_runtime as nn  # 导入nncase运行时环境 / Import nncase runtime
import ulab.numpy as np  # 导入numpy的兼容库 / Import numpy compatible library
import time
import image
import aicube  # 导入aicube库，用于AI推理后处理 / Import aicube for AI post-processing
import random
import gc  # 导入垃圾回收模块 / Import garbage collection
import sys

import _thread


# 自定义手掌检测任务类 / Custom hand detection task class
class HandDetApp(AIBase):
    def __init__(self, kmodel_path, labels, model_input_size, anchors, confidence_threshold=0.2, nms_threshold=0.5, nms_option=False, strides=[8,16,32], rgb888p_size=[1920,1080], display_size=[1920,1080], debug_mode=0):
        """
        初始化手掌检测应用 / Initialize hand detection application
        
        参数说明 / Parameters:
        kmodel_path: 模型文件路径 / Path to the model file
        labels: 检测目标类别标签 / Detection target class labels
        model_input_size: 模型输入尺寸 / Model input size
        anchors: 预设的锚框 / Preset anchor boxes
        confidence_threshold: 置信度阈值 / Confidence threshold
        nms_threshold: 非极大值抑制阈值 / Non-maximum suppression threshold
        nms_option: NMS选项，True表示类间NMS，False表示类内NMS / NMS option, True for inter-class NMS, False for intra-class NMS
        strides: 特征图下采样倍数 / Feature map downsampling ratios
        rgb888p_size: 输入图像尺寸 / Input image size
        display_size: 显示尺寸 / Display size
        debug_mode: 调试模式等级 / Debug mode level
        """
        super().__init__(kmodel_path, model_input_size, rgb888p_size, debug_mode)
        # kmodel路径 / kmodel path
        self.kmodel_path = kmodel_path
        self.labels = labels
        # 检测模型输入分辨率 / Detection model input resolution
        self.model_input_size = model_input_size
        # 置信度阈值 / Confidence threshold
        self.confidence_threshold = confidence_threshold
        # nms阈值 / nms threshold
        self.nms_threshold = nms_threshold
        # 锚框,目标检测任务使用 / Anchor boxes used for object detection
        self.anchors = anchors
        # 特征下采样倍数 / Feature downsampling ratios
        self.strides = strides
        # NMS选项，如果为True做类间NMS,如果为False做类内NMS / NMS option, True for inter-class NMS, False for intra-class NMS
        self.nms_option = nms_option
        # sensor给到AI的图像分辨率，宽16字节对齐 / Image resolution from sensor to AI, width aligned to 16 bytes
        self.rgb888p_size = [ALIGN_UP(rgb888p_size[0], 16), rgb888p_size[1]]
        # 视频输出VO分辨率，宽16字节对齐 / Video output resolution, width aligned to 16 bytes
        self.display_size = [ALIGN_UP(display_size[0], 16), display_size[1]]
        # debug模式 / debug mode
        self.debug_mode = debug_mode
        # Ai2d实例用于实现预处理 / Ai2d instance for preprocessing
        self.ai2d = Ai2d(debug_mode)
        # 设置ai2d的输入输出的格式和数据类型 / Set input/output formats and data types for ai2d
        self.ai2d.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT, nn.ai2d_format.NCHW_FMT, np.uint8, np.uint8)

    # 配置预处理操作，这里使用了pad和resize，Ai2d支持crop/shift/pad/resize/affine，具体代码请打开/sdcard/app/libs/AI2D.py查看
    # Configure preprocessing operations, using pad and resize here. Ai2d supports crop/shift/pad/resize/affine. See /sdcard/app/libs/AI2D.py for details
    def config_preprocess(self, input_image_size=None):
        with ScopedTiming("set preprocess config", self.debug_mode > 0):
            # 初始化ai2d预处理配置，默认为sensor给到AI的尺寸，可以通过设置input_image_size自行修改输入尺寸
            # Initialize ai2d preprocessing config, default is the size from sensor to AI, can be modified by setting input_image_size
            ai2d_input_size = input_image_size if input_image_size else self.rgb888p_size
            # 计算padding参数并应用pad操作，以确保输入图像尺寸与模型输入尺寸匹配
            # Calculate padding parameters and apply pad operation to ensure input image size matches model input size
            top, bottom, left, right = self.get_padding_param()
            self.ai2d.pad([0, 0, 0, 0, top, bottom, left, right], 0, [114, 114, 114])
            # 使用双线性插值进行resize操作，调整图像尺寸以符合模型输入要求
            # Use bilinear interpolation for resize operation to adjust image size to meet model input requirements
            self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
            # 构建预处理流程,参数为预处理输入tensor的shape和预处理输出的tensor的shape
            # Build preprocessing pipeline, parameters are the shape of input tensor and output tensor
            self.ai2d.build([1, 3, ai2d_input_size[1], ai2d_input_size[0]], [1, 3, self.model_input_size[1], self.model_input_size[0]])

    # 自定义当前任务的后处理，用于处理模型输出结果，这里使用了aicube库的anchorbasedet_post_process接口
    # Custom post-processing for the current task to process model output, using anchorbasedet_post_process interface from aicube library
    def postprocess(self, results):
        with ScopedTiming("postprocess", self.debug_mode > 0):
            dets = aicube.anchorbasedet_post_process(results[0], results[1], results[2], self.model_input_size, self.rgb888p_size, self.strides, len(self.labels), self.confidence_threshold, self.nms_threshold, self.anchors, self.nms_option)
            # 返回手掌检测结果 / Return hand detection results
            return dets

    # 计算padding参数，确保输入图像尺寸与模型输入尺寸匹配
    # Calculate padding parameters to ensure input image size matches model input size
    def get_padding_param(self):
        # 根据目标宽度和高度计算比例因子 / Calculate scale factors based on target width and height
        dst_w = self.model_input_size[0]
        dst_h = self.model_input_size[1]
        input_width = self.rgb888p_size[0]
        input_high = self.rgb888p_size[1]
        ratio_w = dst_w / input_width
        ratio_h = dst_h / input_high
        # 选择较小的比例因子，以确保图像内容完整 / Choose the smaller scale factor to ensure image content is complete
        if ratio_w < ratio_h:
            ratio = ratio_w
        else:
            ratio = ratio_h
        # 计算新的宽度和高度 / Calculate new width and height
        new_w = int(ratio * input_width)
        new_h = int(ratio * input_high)
        # 计算宽度和高度的差值，并确定padding的位置 / Calculate width and height differences and determine padding position
        dw = (dst_w - new_w) / 2
        dh = (dst_h - new_h) / 2
        top = int(round(dh - 0.1))
        bottom = int(round(dh + 0.1))
        left = int(round(dw - 0.1))
        right = int(round(dw + 0.1))
        return top, bottom, left, right

# 自定义手势关键点检测任务类 / Custom hand keypoint detection task class
class HandKPDetApp(AIBase):
    def __init__(self, kmodel_path, model_input_size, rgb888p_size=[1920, 1080], display_size=[1920, 1080], debug_mode=0):
        """
        初始化手掌关键点检测应用 / Initialize hand keypoint detection application
        
        参数说明 / Parameters:
        kmodel_path: 模型文件路径 / Path to the model file
        model_input_size: 模型输入尺寸 / Model input size
        rgb888p_size: 输入图像尺寸 / Input image size
        display_size: 显示尺寸 / Display size
        debug_mode: 调试模式等级 / Debug mode level
        """
        super().__init__(kmodel_path, model_input_size, rgb888p_size, debug_mode)
        # kmodel路径 / kmodel path
        self.kmodel_path = kmodel_path
        # 检测模型输入分辨率 / Detection model input resolution
        self.model_input_size = model_input_size
        # sensor给到AI的图像分辨率，宽16字节对齐 / Image resolution from sensor to AI, width aligned to 16 bytes
        self.rgb888p_size = [ALIGN_UP(rgb888p_size[0], 16), rgb888p_size[1]]
        # 视频输出VO分辨率，宽16字节对齐 / Video output resolution, width aligned to 16 bytes
        self.display_size = [ALIGN_UP(display_size[0], 16), display_size[1]]
        self.crop_params = []
        # debug模式 / debug mode
        self.debug_mode = debug_mode
        # Ai2d实例用于实现预处理 / Ai2d instance for preprocessing
        self.ai2d = Ai2d(debug_mode)
        # 设置ai2d的输入输出的格式和数据类型 / Set input/output formats and data types for ai2d
        self.ai2d.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT, nn.ai2d_format.NCHW_FMT, np.uint8, np.uint8)

    # 配置预处理操作，这里使用了crop和resize，Ai2d支持crop/shift/pad/resize/affine，具体代码请打开/sdcard/app/libs/AI2D.py查看
    # Configure preprocessing operations, using crop and resize here. Ai2d supports crop/shift/pad/resize/affine. See /sdcard/app/libs/AI2D.py for details
    def config_preprocess(self, det, input_image_size=None):
        with ScopedTiming("set preprocess config", self.debug_mode > 0):
            ai2d_input_size = input_image_size if input_image_size else self.rgb888p_size
            # 获取裁剪参数 / Get crop parameters
            self.crop_params = self.get_crop_param(det)
            # 应用裁剪操作 / Apply crop operation
            self.ai2d.crop(self.crop_params[0], self.crop_params[1], self.crop_params[2], self.crop_params[3])
            # 使用双线性插值进行resize操作 / Use bilinear interpolation for resize operation
            self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
            # 构建预处理流程 / Build preprocessing pipeline
            self.ai2d.build([1, 3, ai2d_input_size[1], ai2d_input_size[0]], [1, 3, self.model_input_size[1], self.model_input_size[0]])

    # 自定义后处理，results是模型输出的array列表 / Custom post-processing, results is the array list output by the model
    def postprocess(self, results):
        with ScopedTiming("postprocess", self.debug_mode > 0):
            # 重塑模型输出结果 / Reshape the model output results
            results = results[0].reshape(results[0].shape[0] * results[0].shape[1])
            results_show = np.zeros(results.shape, dtype=np.int16)
            # 将相对坐标转换为绝对坐标 / Convert relative coordinates to absolute coordinates
            results_show[0::2] = results[0::2] * self.crop_params[3] + self.crop_params[0]
            results_show[1::2] = results[1::2] * self.crop_params[2] + self.crop_params[1]
            # 调整坐标以适应显示尺寸 / Adjust coordinates to fit display size
            results_show[0::2] = results_show[0::2] * (self.display_size[0] / self.rgb888p_size[0])
            results_show[1::2] = results_show[1::2] * (self.display_size[1] / self.rgb888p_size[1])
            return results_show

    # 计算crop参数 / Calculate crop parameters
    def get_crop_param(self, det_box):
        # 从检测框中获取坐标 / Get coordinates from detection box
        x1, y1, x2, y2 = det_box[2], det_box[3], det_box[4], det_box[5]
        w, h = int(x2 - x1), int(y2 - y1)
        # 转换检测框到显示尺寸 / Convert detection box to display size
        w_det = int(float(x2 - x1) * self.display_size[0] // self.rgb888p_size[0])
        h_det = int(float(y2 - y1) * self.display_size[1] // self.rgb888p_size[1])
        x_det = int(x1 * self.display_size[0] // self.rgb888p_size[0])
        y_det = int(y1 * self.display_size[1] // self.rgb888p_size[1])
        # 计算裁剪参数 / Calculate crop parameters
        length = max(w, h) / 2
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        ratio_num = 1.26 * length
        # 确保裁剪区域在图像范围内 / Ensure crop area is within image boundaries
        x1_kp = int(max(0, cx - ratio_num))
        y1_kp = int(max(0, cy - ratio_num))
        x2_kp = int(min(self.rgb888p_size[0] - 1, cx + ratio_num))
        y2_kp = int(min(self.rgb888p_size[1] - 1, cy + ratio_num))
        w_kp = int(x2_kp - x1_kp + 1)
        h_kp = int(y2_kp - y1_kp + 1)
        return [x1_kp, y1_kp, w_kp, h_kp]

# 手掌关键点检测任务 / Hand keypoint detection task
class HandKeyPointDet:
    def __init__(self, hand_det_kmodel, hand_kp_kmodel, det_input_size, kp_input_size, labels, anchors, confidence_threshold=0.25, nms_threshold=0.3, nms_option=False, strides=[8, 16, 32], rgb888p_size=[1280, 720], display_size=[1920, 1080], debug_mode=0):
        """
        初始化手掌关键点检测任务 / Initialize hand keypoint detection task
        
        参数说明 / Parameters:
        hand_det_kmodel: 手掌检测模型路径 / Path to hand detection model
        hand_kp_kmodel: 手掌关键点模型路径 / Path to hand keypoint model
        det_input_size: 检测模型输入尺寸 / Detection model input size
        kp_input_size: 关键点模型输入尺寸 / Keypoint model input size
        labels: 检测目标类别标签 / Detection target class labels
        anchors: 预设的锚框 / Preset anchor boxes
        confidence_threshold: 置信度阈值 / Confidence threshold
        nms_threshold: 非极大值抑制阈值 / Non-maximum suppression threshold
        nms_option: NMS选项 / NMS option
        strides: 特征图下采样倍数 / Feature map downsampling ratios
        rgb888p_size: 输入图像尺寸 / Input image size
        display_size: 显示尺寸 / Display size
        debug_mode: 调试模式等级 / Debug mode level
        """
        # 手掌检测模型路径 / Path to hand detection model
        self.hand_det_kmodel = hand_det_kmodel
        # 手掌关键点模型路径 / Path to hand keypoint model
        self.hand_kp_kmodel = hand_kp_kmodel
        # 手掌检测模型输入分辨率 / Hand detection model input resolution
        self.det_input_size = det_input_size
        # 手掌关键点模型输入分辨率 / Hand keypoint model input resolution
        self.kp_input_size = kp_input_size
        self.labels = labels
        # anchors
        self.anchors = anchors
        # 置信度阈值 / Confidence threshold
        self.confidence_threshold = confidence_threshold
        # nms阈值 / nms threshold
        self.nms_threshold = nms_threshold
        # nms选项 / nms option
        self.nms_option = nms_option
        # 特征图对于输入的下采样倍数 / Feature map downsampling ratios for input
        self.strides = strides
        # sensor给到AI的图像分辨率，宽16字节对齐 / Image resolution from sensor to AI, width aligned to 16 bytes
        self.rgb888p_size = [ALIGN_UP(rgb888p_size[0], 16), rgb888p_size[1]]
        # 视频输出VO分辨率，宽16字节对齐 / Video output resolution, width aligned to 16 bytes
        self.display_size = [ALIGN_UP(display_size[0], 16), display_size[1]]
        # debug_mode模式 / debug_mode
        self.debug_mode = debug_mode
        # 初始化手掌检测和关键点检测实例 / Initialize hand detection and keypoint detection instances
        self.hand_det = HandDetApp(self.hand_det_kmodel, self.labels, model_input_size=self.det_input_size, anchors=self.anchors, confidence_threshold=self.confidence_threshold, nms_threshold=self.nms_threshold, nms_option=self.nms_option, strides=self.strides, rgb888p_size=self.rgb888p_size, display_size=self.display_size, debug_mode=0)
        self.hand_kp = HandKPDetApp(self.hand_kp_kmodel, model_input_size=self.kp_input_size, rgb888p_size=self.rgb888p_size, display_size=self.display_size)
        # 配置手掌检测预处理 / Configure hand detection preprocessing
        self.hand_det.config_preprocess()

    # run函数 / run function
    def run(self, input_np):
        """
        运行手掌关键点检测 / Run hand keypoint detection
        
        参数 / Parameters:
        input_np: 输入图像 / Input image
        
        返回 / Returns:
        boxes: 检测到的手掌框 / Detected hand boxes
        hand_res: 手掌关键点结果 / Hand keypoint results
        """
        # 手掌检测 / Hand detection
        det_boxes = self.hand_det.run(input_np)
        hand_res = []
        boxes = []
        for det_box in det_boxes:
            # 对检测到的每个手掌执行手势关键点识别 / Perform gesture keypoint detection for each detected hand
            x1, y1, x2, y2 = det_box[2], det_box[3], det_box[4], det_box[5]
            w, h = int(x2 - x1), int(y2 - y1)
            # 丢弃不合理的框 / Discard unreasonable boxes
            if (h < (0.1 * self.rgb888p_size[1])):
                continue
            if (w < (0.25 * self.rgb888p_size[0]) and ((x1 < (0.03 * self.rgb888p_size[0])) or (x2 > (0.97 * self.rgb888p_size[0])))):
                continue
            if (w < (0.15 * self.rgb888p_size[0]) and ((x1 < (0.01 * self.rgb888p_size[0])) or (x2 > (0.99 * self.rgb888p_size[0])))):
                continue
            # 配置关键点检测预处理 / Configure keypoint detection preprocessing
            self.hand_kp.config_preprocess(det_box)
            # 执行关键点检测 / Perform keypoint detection
            results_show = self.hand_kp.run(input_np)
            boxes.append(det_box)
            hand_res.append(results_show)
        return boxes, hand_res

    # 绘制效果，绘制手掌关键点、检测框 / Draw results, including hand keypoints and detection boxes
    def draw_result(self, pl, dets, hand_res):
        """
        绘制检测结果 / Draw detection results
        
        参数 / Parameters:
        pl: Pipeline实例 / Pipeline instance
        dets: 检测到的手掌框 / Detected hand boxes
        hand_res: 手掌关键点结果 / Hand keypoint results
        """
        pl.osd_img.clear()
        if dets:
            for k in range(len(dets)):
                det_box = dets[k]
                x1, y1, x2, y2 = det_box[2], det_box[3], det_box[4], det_box[5]
                w, h = int(x2 - x1), int(y2 - y1)
                # 转换检测框到显示尺寸 / Convert detection box to display size
                w_det = int(float(x2 - x1) * self.display_size[0] // self.rgb888p_size[0])
                h_det = int(float(y2 - y1) * self.display_size[1] // self.rgb888p_size[1])
                x_det = int(x1 * self.display_size[0] // self.rgb888p_size[0])
                y_det = int(y1 * self.display_size[1] // self.rgb888p_size[1])
                # 绘制检测框 / Draw detection box
                pl.osd_img.draw_rectangle(x_det, y_det, w_det, h_det, color=(255, 0, 255, 0), thickness=2)

                # 绘制关键点 / Draw keypoints
                results_show = hand_res[k]
                for i in range(len(results_show) // 2):
                    pl.osd_img.draw_circle(results_show[i * 2], results_show[i * 2 + 1], 1, color=(255, 0, 255, 0), fill=False)
                
                # 绘制手指连线 / Draw finger connections
                for i in range(5):
                    j = i * 8
                    # 为每个手指设置不同颜色 / Set different colors for each finger
                    if i == 0:
                        R = 255; G = 0; B = 0      # 拇指红色 / Thumb red
                    if i == 1:
                        R = 255; G = 0; B = 255    # 食指洋红 / Index finger magenta
                    if i == 2:
                        R = 255; G = 255; B = 0    # 中指黄色 / Middle finger yellow
                    if i == 3:
                        R = 0; G = 255; B = 0      # 无名指绿色 / Ring finger green
                    if i == 4:
                        R = 0; G = 0; B = 255      # 小指蓝色 / Little finger blue
                    
                    # 绘制手掌到指根的连线 / Draw line from palm to finger base
                    pl.osd_img.draw_line(results_show[0], results_show[1], results_show[j + 2], results_show[j + 3], color=(255, R, G, B), thickness=3)
                    # 绘制手指各关节之间的连线 / Draw lines between finger joints
                    pl.osd_img.draw_line(results_show[j + 2], results_show[j + 3], results_show[j + 4], results_show[j + 5], color=(255, R, G, B), thickness=3)
                    pl.osd_img.draw_line(results_show[j + 4], results_show[j + 5], results_show[j + 6], results_show[j + 7], color=(255, R, G, B), thickness=3)
                    pl.osd_img.draw_line(results_show[j + 6], results_show[j + 7], results_show[j + 8], results_show[j + 9], color=(255, R, G, B), thickness=3)



if __name__ == "__main__":
    # 显示模式，默认"hdmi",可以选择"hdmi"和"lcd" / Display mode, default is "hdmi", can be "hdmi" or "lcd"
    display_mode = "lcd"
    
    rgb888p_size=[640,480]

    # 根据显示模式设置显示尺寸 / Set display size based on display mode
    if display_mode == "hdmi":
        display_size = [1920, 1080]
    else:
        display_size = [640, 480]
    # 手掌检测模型路径 / Path to hand detection model
    hand_det_kmodel_path = "/sdcard/kmodel/hand_det.kmodel"
    # 手部关键点模型路径 / Path to hand keypoint model
    hand_kp_kmodel_path = "/sdcard/kmodel/handkp_det.kmodel"
    # 其它参数 / Other parameters
    anchors_path = "/sdcard/utils/prior_data_320.bin"
    hand_det_input_size = [512, 512]
    hand_kp_input_size = [256, 256]
    confidence_threshold = 0.2
    nms_threshold = 0.5
    labels = ["hand"]
    anchors = [26, 27, 53, 52, 75, 71, 80, 99, 106, 82, 99, 134, 140, 113, 161, 172, 245, 276]

    # 初始化PipeLine，只关注传给AI的图像分辨率，显示的分辨率 
    # Initialize PipeLine, focusing only on the image resolution passed to AI and the display resolution
    pl = PipeLine(rgb888p_size=rgb888p_size, display_size=display_size, display_mode=display_mode)
    pl.create()
    # 初始化手掌关键点检测任务 / Initialize hand keypoint detection task
    hkd = HandKeyPointDet(hand_det_kmodel_path, hand_kp_kmodel_path, det_input_size=hand_det_input_size, kp_input_size=hand_kp_input_size, labels=labels, anchors=anchors, confidence_threshold=confidence_threshold, nms_threshold=nms_threshold, nms_option=False, strides=[8, 16, 32], rgb888p_size=rgb888p_size, display_size=display_size)
    
    # 主循环 / Main loop
    while True:
        with ScopedTiming("total", 1):
            img = pl.get_frame()                       # 获取当前帧 / Get current frame
            det_boxes, hand_res = hkd.run(img)         # 推理当前帧 / Process current frame
            hkd.draw_result(pl, det_boxes, hand_res)   # 绘制推理结果 / Draw inference results
            pl.show_image()                            # 展示推理结果 / Show inference results
            gc.collect()                               # 执行垃圾回收 / Perform garbage collection
            time.sleep_ms(5)                           # 短暂休眠减少CPU占用 / Brief sleep to reduce CPU usage
    pl.destroy()
    hkd.hand_det.deinit()
    hkd.hand_kp.deinit()       