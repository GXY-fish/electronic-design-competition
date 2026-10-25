from libs.PipeLine import PipeLine, ScopedTiming  # 导入Pipeline和计时工具类
from libs.AIBase import AIBase  # 导入AI基础类
from libs.AI2D import Ai2d  # 导入Ai2d图像预处理类
import os  # 导入操作系统接口模块
import ujson  # 导入json处理模块（microPython版本的json库）
from media.media import *  # 导入媒体处理相关类
from time import *  # 导入时间相关函数
import nncase_runtime as nn  # 导入nncase运行时库
import ulab.numpy as np  # 导入微型numpy库（针对嵌入式设备优化）
import time  # 导入时间模块
import utime  # 导入microPython特定的时间模块
import image  # 导入图像处理模块
import random  # 导入随机数生成模块
import gc  # 导入垃圾回收模块
import sys  # 导入系统模块
import aidemo  # 导入自定义AI演示库

# 自定义人体关键点检测类
# Custom person keypoint detection class
class PersonKeyPointApp(AIBase):
    def __init__(self, kmodel_path, model_input_size, confidence_threshold=0.2, nms_threshold=0.5, rgb888p_size=[1280,720], display_size=[640,360], debug_mode=0):
        """
        初始化人体关键点检测应用
        Initialize the person keypoint detection application
        
        Args:
            kmodel_path: 模型文件路径 (path to the model file)
            model_input_size: 模型输入尺寸 (model input size)
            confidence_threshold: 置信度阈值 (confidence threshold)
            nms_threshold: 非极大值抑制阈值 (non-maximum suppression threshold)
            rgb888p_size: RGB888P图像尺寸 (RGB888P image size)
            display_size: 显示尺寸 (display size)
            debug_mode: 调试模式 (debug mode level)
        """
        super().__init__(kmodel_path, model_input_size, rgb888p_size, debug_mode)
        self.kmodel_path = kmodel_path
        # 模型输入分辨率 (model input resolution)
        self.model_input_size = model_input_size
        # 置信度阈值设置 (confidence threshold setting)
        self.confidence_threshold = confidence_threshold
        # nms阈值设置 (non-maximum suppression threshold setting)
        self.nms_threshold = nms_threshold
        # sensor给到AI的图像分辨率，进行16对齐 (image resolution from sensor to AI, aligned to 16)
        self.rgb888p_size = [ALIGN_UP(rgb888p_size[0], 16), rgb888p_size[1]]
        # 显示分辨率，进行16对齐 (display resolution, aligned to 16)
        self.display_size = [ALIGN_UP(display_size[0], 16), display_size[1]]
        self.debug_mode = debug_mode
        
        # 骨骼信息，连接的关键点对 (skeleton information, connected keypoint pairs)
        self.SKELETON = [(16, 14), (14, 12), (17, 15), (15, 13), (12, 13), (6, 12), (7, 13), (6, 7), (6, 8), 
                         (7, 9), (8, 10), (9, 11), (2, 3), (1, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7)]
        
        # 肢体颜色，RGBA格式 (limb colors in RGBA format)
        self.LIMB_COLORS = [(255, 51, 153, 255), (255, 51, 153, 255), (255, 51, 153, 255), (255, 51, 153, 255),
                           (255, 255, 51, 255), (255, 255, 51, 255), (255, 255, 51, 255), (255, 255, 128, 0),
                           (255, 255, 128, 0), (255, 255, 128, 0), (255, 255, 128, 0), (255, 255, 128, 0),
                           (255, 0, 255, 0), (255, 0, 255, 0), (255, 0, 255, 0), (255, 0, 255, 0),
                           (255, 0, 255, 0), (255, 0, 255, 0), (255, 0, 255, 0)]
        
        # 关键点颜色，RGBA格式，共17个 (keypoint colors in RGBA format, 17 in total)
        self.KPS_COLORS = [(255, 0, 255, 0), (255, 0, 255, 0), (255, 0, 255, 0), (255, 0, 255, 0),
                          (255, 0, 255, 0), (255, 255, 128, 0), (255, 255, 128, 0), (255, 255, 128, 0),
                          (255, 255, 128, 0), (255, 255, 128, 0), (255, 255, 128, 0), (255, 51, 153, 255),
                          (255, 51, 153, 255), (255, 51, 153, 255), (255, 51, 153, 255), (255, 51, 153, 255),
                          (255, 51, 153, 255)]

        # Ai2d实例，用于实现模型预处理 (Ai2d instance for model preprocessing)
        self.ai2d = Ai2d(debug_mode)
        # 设置Ai2d的输入输出格式和类型 (Set Ai2d input/output format and type)
        self.ai2d.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT, nn.ai2d_format.NCHW_FMT, np.uint8, np.uint8)

    # 配置预处理操作，这里使用了pad和resize
    # Configure preprocessing operations, using pad and resize here
    # Ai2d支持crop/shift/pad/resize/affine，具体代码请打开/sdcard/app/libs/AI2D.py查看
    # Ai2d supports crop/shift/pad/resize/affine, see /sdcard/app/libs/AI2D.py for details
    def config_preprocess(self, input_image_size=None):
        with ScopedTiming("set preprocess config", self.debug_mode > 0):
            # 初始化ai2d预处理配置，默认为sensor给到AI的尺寸，您可以通过设置input_image_size自行修改输入尺寸
            # Initialize ai2d preprocessing configuration, default is the size from sensor to AI
            # You can modify the input size by setting input_image_size
            ai2d_input_size = input_image_size if input_image_size else self.rgb888p_size
            top, bottom, left, right = self.get_padding_param()
            self.ai2d.pad([0, 0, 0, 0, top, bottom, left, right], 0, [0, 0, 0])
            self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
            self.ai2d.build([1, 3, ai2d_input_size[1], ai2d_input_size[0]], 
                            [1, 3, self.model_input_size[1], self.model_input_size[0]])

    # 自定义当前任务的后处理
    # Custom post-processing for the current task
    def postprocess(self, results):
        with ScopedTiming("postprocess", self.debug_mode > 0):
            # 这里使用了aidemo库的person_kp_postprocess接口
            # Using person_kp_postprocess interface from aidemo library
            results = aidemo.person_kp_postprocess(
                results[0], 
                [self.rgb888p_size[1], self.rgb888p_size[0]], 
                self.model_input_size, 
                self.confidence_threshold, 
                self.nms_threshold
            )
            return results

    # 绘制结果，绘制人体关键点
    # Draw results, drawing human body keypoints
    def draw_result(self, pl, res):
        with ScopedTiming("display_draw", self.debug_mode > 0):
            if res[0]:  # 如果检测到人 (If person detected)
                pl.osd_img.clear()  # 清除OSD图像 (Clear OSD image)
                kpses = res[1]  # 获取关键点数据 (Get keypoint data)
                for i in range(len(res[0])):  # 遍历每个检测到的人 (Iterate through each detected person)
                    for k in range(17+2):  # 遍历关键点和骨架 (Iterate through keypoints and skeleton)
                        if (k < 17):  # 如果是关键点 (If it's a keypoint)
                            kps_x, kps_y, kps_s = round(kpses[i][k][0]), round(kpses[i][k][1]), kpses[i][k][2]
                            # 将坐标转换到显示尺寸 (Convert coordinates to display size)
                            kps_x1 = int(float(kps_x) * self.display_size[0] // self.rgb888p_size[0])
                            kps_y1 = int(float(kps_y) * self.display_size[1] // self.rgb888p_size[1])
                            if (kps_s > 0):  # 如果置信度大于0 (If confidence is greater than 0)
                                # 绘制关键点圆 (Draw keypoint circle)
                                pl.osd_img.draw_circle(kps_x1, kps_y1, 5, self.KPS_COLORS[k], 4)
                        
                        # 绘制骨骼线 (Draw skeleton lines)
                        ske = self.SKELETON[k]
                        # 获取连接线两端的关键点坐标 (Get coordinates of keypoints at both ends of connection line)
                        pos1_x, pos1_y = round(kpses[i][ske[0]-1][0]), round(kpses[i][ske[0]-1][1])
                        pos1_x_ = int(float(pos1_x) * self.display_size[0] // self.rgb888p_size[0])
                        pos1_y_ = int(float(pos1_y) * self.display_size[1] // self.rgb888p_size[1])

                        pos2_x, pos2_y = round(kpses[i][(ske[1]-1)][0]), round(kpses[i][(ske[1]-1)][1])
                        pos2_x_ = int(float(pos2_x) * self.display_size[0] // self.rgb888p_size[0])
                        pos2_y_ = int(float(pos2_y) * self.display_size[1] // self.rgb888p_size[1])

                        # 获取两端点的置信度 (Get confidence of both endpoints)
                        pos1_s, pos2_s = kpses[i][(ske[0]-1)][2], kpses[i][(ske[1]-1)][2]
                        if (pos1_s > 0.0 and pos2_s > 0.0):  # 如果两端点都可见 (If both endpoints are visible)
                            # 绘制骨骼线 (Draw skeleton line)
                            pl.osd_img.draw_line(pos1_x_, pos1_y_, pos2_x_, pos2_y_, self.LIMB_COLORS[k], 4)
                    gc.collect()  # 垃圾回收 (Garbage collection)
            else:
                pl.osd_img.clear()  # 如果没有检测到人，清除OSD图像 (If no person detected, clear OSD image)

    # 计算padding参数
    # Calculate padding parameters
    def get_padding_param(self):
        """
        计算在保持宽高比的情况下，需要填充的像素数量
        Calculate the number of pixels to pad while maintaining aspect ratio
        
        Returns:
            top, bottom, left, right: 填充参数 (padding parameters)
        """
        dst_w = self.model_input_size[0]  # 目标宽度 (target width)
        dst_h = self.model_input_size[1]  # 目标高度 (target height)
        input_width = self.rgb888p_size[0]  # 输入宽度 (input width)
        input_high = self.rgb888p_size[1]  # 输入高度 (input height)
        
        # 计算宽高缩放比例 (Calculate width and height scaling ratios)
        ratio_w = dst_w / input_width
        ratio_h = dst_h / input_high
        
        # 选择较小的缩放比例，保持宽高比 (Choose the smaller scaling ratio to maintain aspect ratio)
        if ratio_w < ratio_h:
            ratio = ratio_w
        else:
            ratio = ratio_h
            
        # 计算新的宽高 (Calculate new width and height)
        new_w = (int)(ratio * input_width)
        new_h = (int)(ratio * input_high)
        
        # 计算需要填充的像素数量 (Calculate the number of pixels to pad)
        dw = (dst_w - new_w) / 2
        dh = (dst_h - new_h) / 2
        
        # 将填充量转换为整数 (Convert padding amounts to integers)
        top = int(round(dh - 0.1))
        bottom = int(round(dh + 0.1))
        left = int(round(dw - 0.1))
        right = int(round(dw - 0.1))
        
        return top, bottom, left, right

if __name__ == "__main__":
    # 显示模式，默认"hdmi"，可以选择"hdmi"和"lcd"
    # Display mode, default "hdmi", can choose "hdmi" or "lcd"
    display_mode = "lcd"
    rgb888p_size=[640,480]  # RGB图像尺寸 (RGB image size)

    if display_mode == "hdmi":
        display_size = [640, 360]  # HDMI显示尺寸 (HDMI display size)
    else:
        display_size = [640, 480]  # LCD显示尺寸 (LCD display size)
        
    # 模型路径 (Model path)
    kmodel_path = "/sdcard/kmodel/yolov8n-pose.kmodel"
    # 其它参数设置 (Other parameter settings)
    confidence_threshold = 0.2  # 置信度阈值 (Confidence threshold)
    nms_threshold = 0.5  # 非极大值抑制阈值 (NMS threshold)
    
    # 初始化PipeLine (Initialize PipeLine)
    pl = PipeLine(rgb888p_size=rgb888p_size, display_size=display_size, display_mode=display_mode)
    pl.create()
    
    # 初始化自定义人体关键点检测实例 (Initialize custom person keypoint detection instance)
    person_kp = PersonKeyPointApp(
        kmodel_path, 
        model_input_size=[320, 320], 
        confidence_threshold=confidence_threshold, 
        nms_threshold=nms_threshold, 
        rgb888p_size=rgb888p_size, 
        display_size=display_size, 
        debug_mode=0
    )
    
    person_kp.config_preprocess()  # 配置预处理 (Configure preprocessing)
    
    while True:
        with ScopedTiming("total", 1):
            # 获取当前帧数据 (Get current frame data)
            img = pl.get_frame()
            # 推理当前帧 (Infer current frame)
            res = person_kp.run(img)
            # 绘制结果到PipeLine的osd图像 (Draw results to PipeLine's osd image)
            person_kp.draw_result(pl, res)
            # 显示当前的绘制结果 (Show current drawing results)
            pl.show_image()
            gc.collect()  # 垃圾回收 (Garbage collection)
            
    # 释放资源 (Release resources)
    person_kp.deinit()
    pl.destroy()