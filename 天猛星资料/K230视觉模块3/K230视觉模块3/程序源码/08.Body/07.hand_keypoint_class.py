from libs.PipeLine import PipeLine, ScopedTiming
from libs.AIBase import AIBase
from libs.AI2D import Ai2d
import os
import ujson
from media.media import *
from time import *
import nncase_runtime as nn
import ulab.numpy as np
import time
import image
import aicube
import random
import gc
import sys

# 自定义手掌检测任务类
# Custom hand detection task class
class HandDetApp(AIBase):
    def __init__(self,kmodel_path,labels,model_input_size,anchors,confidence_threshold=0.2,nms_threshold=0.5,nms_option=False, strides=[8,16,32],rgb888p_size=[1920,1080],display_size=[1920,1080],debug_mode=0):
        super().__init__(kmodel_path,model_input_size,rgb888p_size,debug_mode)
        # kmodel路径
        # Path to kmodel file
        self.kmodel_path=kmodel_path
        # 标签列表
        # List of labels
        self.labels=labels
        # 检测模型输入分辨率
        # Detection model input resolution
        self.model_input_size=model_input_size
        # 置信度阈值：用于过滤低置信度的检测框
        # Confidence threshold: used to filter out detection boxes with low confidence
        self.confidence_threshold=confidence_threshold
        # nms阈值：用于非极大值抑制，消除重复框
        # NMS threshold: used for non-maximum suppression to eliminate duplicate boxes
        self.nms_threshold=nms_threshold
        # 锚框：目标检测任务使用的预定义边界框
        # Anchors: predefined boundary boxes used for object detection tasks
        self.anchors=anchors
        # 特征下采样倍数：各个特征图的步长
        # Feature downsampling factors: strides for each feature map
        self.strides = strides
        # NMS选项：如果为True做类间NMS，如果为False做类内NMS
        # NMS option: If True, perform inter-class NMS; if False, perform intra-class NMS
        self.nms_option = nms_option
        # sensor给到AI的图像分辨率，宽16字节对齐
        # Image resolution from sensor to AI, width aligned to 16 bytes
        self.rgb888p_size=[ALIGN_UP(rgb888p_size[0],16),rgb888p_size[1]]
        # 视频输出VO分辨率，宽16字节对齐
        # Video output resolution, width aligned to 16 bytes
        self.display_size=[ALIGN_UP(display_size[0],16),display_size[1]]
        # debug模式：控制是否打印调试信息
        # Debug mode: controls whether to print debug information
        self.debug_mode=debug_mode
        # Ai2d实例用于实现预处理
        # Ai2d instance used for preprocessing
        self.ai2d=Ai2d(debug_mode)
        # 设置ai2d的输入输出的格式和数据类型
        # Set the format and data type of ai2d input and output
        self.ai2d.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT,nn.ai2d_format.NCHW_FMT,np.uint8, np.uint8)

    # 配置预处理操作，这里使用了pad和resize，Ai2d支持crop/shift/pad/resize/affine，具体代码请打开/sdcard/app/libs/AI2D.py查看
    # Configure preprocessing operations. Here, pad and resize are used. Ai2d supports crop/shift/pad/resize/affine.
    # See /sdcard/app/libs/AI2D.py for details
    def config_preprocess(self,input_image_size=None):
        with ScopedTiming("set preprocess config",self.debug_mode > 0):
            # 初始化ai2d预处理配置，默认为sensor给到AI的尺寸，可以通过设置input_image_size自行修改输入尺寸
            # Initialize ai2d preprocessing configuration. Default is the size from sensor to AI,
            # can be modified via input_image_size parameter
            ai2d_input_size = input_image_size if input_image_size else self.rgb888p_size
            # 计算padding参数并应用pad操作，以确保输入图像尺寸与模型输入尺寸匹配
            # Calculate padding parameters and apply pad operation to ensure input image size matches model input size
            top, bottom, left, right = self.get_padding_param()
            self.ai2d.pad([0, 0, 0, 0, top, bottom, left, right], 0, [114, 114, 114])
            # 使用双线性插值进行resize操作，调整图像尺寸以符合模型输入要求
            # Use bilinear interpolation for resize operation to adjust image size to meet model input requirements
            self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
            # 构建预处理流程,参数为预处理输入tensor的shape和预处理输出的tensor的shape
            # Build preprocessing pipeline. Parameters are the shape of input tensor and output tensor
            self.ai2d.build([1,3,ai2d_input_size[1],ai2d_input_size[0]],[1,3,self.model_input_size[1],self.model_input_size[0]])

    # 自定义当前任务的后处理，用于处理模型输出结果，这里使用了aicube库的anchorbasedet_post_process接口
    # Custom postprocessing for the current task to process model output results
    # Here, anchorbasedet_post_process from aicube library is used
    def postprocess(self,results):
        with ScopedTiming("postprocess",self.debug_mode > 0):
            dets = aicube.anchorbasedet_post_process(results[0], results[1], results[2], self.model_input_size, self.rgb888p_size, self.strides, len(self.labels), self.confidence_threshold, self.nms_threshold, self.anchors, self.nms_option)
            # 返回手掌检测结果
            # Return hand detection results
            return dets

    # 计算padding参数，确保输入图像尺寸与模型输入尺寸匹配
    # Calculate padding parameters to ensure input image size matches model input size
    def get_padding_param(self):
        # 根据目标宽度和高度计算比例因子
        # Calculate scale factors based on target width and height
        dst_w = self.model_input_size[0]
        dst_h = self.model_input_size[1]
        input_width = self.rgb888p_size[0]
        input_high = self.rgb888p_size[1]
        ratio_w = dst_w / input_width
        ratio_h = dst_h / input_high
        # 选择较小的比例因子，以确保图像内容完整
        # Select the smaller scale factor to ensure image content is complete
        if ratio_w < ratio_h:
            ratio = ratio_w
        else:
            ratio = ratio_h
        # 计算新的宽度和高度
        # Calculate new width and height
        new_w = int(ratio * input_width)
        new_h = int(ratio * input_high)
        # 计算宽度和高度的差值，并确定padding的位置
        # Calculate width and height differences and determine padding position
        dw = (dst_w - new_w) / 2
        dh = (dst_h - new_h) / 2
        top = int(round(dh - 0.1))
        bottom = int(round(dh + 0.1))
        left = int(round(dw - 0.1))
        right = int(round(dw + 0.1))
        return top, bottom, left, right

# 自定义手势关键点分类任务类
# Custom hand keypoint classification task class
class HandKPClassApp(AIBase):
    def __init__(self,kmodel_path,model_input_size,rgb888p_size=[1920,1080],display_size=[1920,1080],debug_mode=0):
        super().__init__(kmodel_path,model_input_size,rgb888p_size,debug_mode)
        # kmodel路径
        # Path to kmodel file
        self.kmodel_path=kmodel_path
        # 检测模型输入分辨率
        # Detection model input resolution
        self.model_input_size=model_input_size
        # sensor给到AI的图像分辨率，宽16字节对齐
        # Image resolution from sensor to AI, width aligned to 16 bytes
        self.rgb888p_size=[ALIGN_UP(rgb888p_size[0],16),rgb888p_size[1]]
        # 视频输出VO分辨率，宽16字节对齐
        # Video output resolution, width aligned to 16 bytes
        self.display_size=[ALIGN_UP(display_size[0],16),display_size[1]]
        # 裁剪参数：存储图像裁剪的位置和大小
        # Crop parameters: store the position and size of image cropping
        self.crop_params=[]
        # debug模式：控制是否打印调试信息
        # Debug mode: controls whether to print debug information
        self.debug_mode=debug_mode
        # Ai2d实例用于实现预处理
        # Ai2d instance used for preprocessing
        self.ai2d=Ai2d(debug_mode)
        # 设置ai2d的输入输出的格式和数据类型
        # Set the format and data type of ai2d input and output
        self.ai2d.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT,nn.ai2d_format.NCHW_FMT,np.uint8, np.uint8)

    # 配置预处理操作，这里使用了crop和resize，Ai2d支持crop/shift/pad/resize/affine，具体代码请打开/sdcard/app/libs/AI2D.py查看
    # Configure preprocessing operations. Here, crop and resize are used. Ai2d supports crop/shift/pad/resize/affine.
    # See /sdcard/app/libs/AI2D.py for details
    def config_preprocess(self,det,input_image_size=None):
        with ScopedTiming("set preprocess config",self.debug_mode > 0):
            # 设置输入图像尺寸
            # Set input image size
            ai2d_input_size=input_image_size if input_image_size else self.rgb888p_size
            # 获取裁剪参数
            # Get crop parameters
            self.crop_params = self.get_crop_param(det)
            # 配置裁剪操作
            # Configure crop operation
            self.ai2d.crop(self.crop_params[0],self.crop_params[1],self.crop_params[2],self.crop_params[3])
            # 配置调整大小操作
            # Configure resize operation
            self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
            # 构建预处理流程
            # Build preprocessing pipeline
            self.ai2d.build([1,3,ai2d_input_size[1],ai2d_input_size[0]],[1,3,self.model_input_size[1],self.model_input_size[0]])

    # 自定义后处理，得到手掌手势结果和手掌关键点数据
    # Custom postprocessing to get hand gesture results and hand keypoint data
    def postprocess(self,results):
        with ScopedTiming("postprocess",self.debug_mode > 0):
            # 重塑模型输出结果
            # Reshape model output results
            results=results[0].reshape(results[0].shape[0]*results[0].shape[1])
            # 创建结果显示数组
            # Create result display array
            results_show = np.zeros(results.shape,dtype=np.int16)
            # 将关键点坐标映射回原始图像空间
            # Map keypoint coordinates back to original image space
            results_show[0::2] = results[0::2] * self.crop_params[3] + self.crop_params[0]
            results_show[1::2] = results[1::2] * self.crop_params[2] + self.crop_params[1]
            # 根据关键点识别手势
            # Recognize gesture based on keypoints
            gesture=self.hk_gesture(results_show)
            # 将坐标进一步映射到显示尺寸
            # Further map coordinates to display size
            results_show[0::2] = results_show[0::2] * (self.display_size[0] / self.rgb888p_size[0])
            results_show[1::2] = results_show[1::2] * (self.display_size[1] / self.rgb888p_size[1])
            return results_show,gesture

    # 计算crop参数
    # Calculate crop parameters
    def get_crop_param(self,det_box):
        # 获取检测框坐标
        # Get detection box coordinates
        x1, y1, x2, y2 = det_box[2],det_box[3],det_box[4],det_box[5]
        # 计算宽高
        # Calculate width and height
        w,h= int(x2 - x1),int(y2 - y1)
        # 计算在显示尺寸中的宽高和位置
        # Calculate width, height and position in display size
        w_det = int(float(x2 - x1) * self.display_size[0] // self.rgb888p_size[0])
        h_det = int(float(y2 - y1) * self.display_size[1] // self.rgb888p_size[1])
        x_det = int(x1*self.display_size[0] // self.rgb888p_size[0])
        y_det = int(y1*self.display_size[1] // self.rgb888p_size[1])
        # 计算长边，用于确定裁剪区域
        # Calculate long side to determine crop area
        length = max(w, h)/2
        # 计算中心点
        # Calculate center point
        cx = (x1+x2)/2
        cy = (y1+y2)/2
        # 调整裁剪比例
        # Adjust crop ratio
        ratio_num = 1.26*length
        # 计算裁剪区域的左上角和右下角坐标，确保不超出图像边界
        # Calculate top-left and bottom-right coordinates of crop area, ensure not exceeding image boundaries
        x1_kp = int(max(0,cx-ratio_num))
        y1_kp = int(max(0,cy-ratio_num))
        x2_kp = int(min(self.rgb888p_size[0]-1, cx+ratio_num))
        y2_kp = int(min(self.rgb888p_size[1]-1, cy+ratio_num))
        # 计算裁剪区域的宽高
        # Calculate width and height of crop area
        w_kp = int(x2_kp - x1_kp + 1)
        h_kp = int(y2_kp - y1_kp + 1)
        return [x1_kp, y1_kp, w_kp, h_kp]

    # 求两个vector之间的夹角
    # Calculate the angle between two vectors
    def hk_vector_2d_angle(self,v1,v2):
        with ScopedTiming("hk_vector_2d_angle",self.debug_mode > 0):
            try:
                # 获取向量的坐标
                # Get coordinates of vectors
                v1_x,v1_y,v2_x,v2_y = v1[0],v1[1],v2[0],v2[1]
                # 计算向量的范数
                # Calculate vector norms
                v1_norm = np.sqrt(v1_x * v1_x+ v1_y * v1_y)
                v2_norm = np.sqrt(v2_x * v2_x + v2_y * v2_y)
                # 计算点积
                # Calculate dot product
                dot_product = v1_x * v2_x + v1_y * v2_y
                # 计算夹角的余弦值
                # Calculate cosine of angle
                cos_angle = dot_product/(v1_norm*v2_norm)
                # 将余弦值转换为角度
                # Convert cosine to angle in degrees
                angle = np.acos(cos_angle)*180/np.pi
                return angle
            except Exception as e:
                return 0

    # 根据手掌关键点检测结果判断手势类别
    # Determine gesture category based on hand keypoint detection results
    def hk_gesture(self,results):
        with ScopedTiming("hk_gesture",self.debug_mode > 0):
            # 初始化角度列表
            # Initialize angle list
            angle_list = []
            # 计算每个手指的角度
            # Calculate angle for each finger
            for i in range(5):
                angle = self.hk_vector_2d_angle([(results[0]-results[i*8+4]), (results[1]-results[i*8+5])],[(results[i*8+6]-results[i*8+8]),(results[i*8+7]-results[i*8+9])])
                angle_list.append(angle)
            # 设置角度阈值和初始手势字符串
            # Set angle thresholds and initial gesture string
            thr_angle,thr_angle_thumb,thr_angle_s,gesture_str = 65.,53.,49.,None
            # 如果所有角度都有效，则根据角度判断手势
            # If all angles are valid, determine gesture based on angles
            if 65535. not in angle_list:
                # 拳头：所有手指都弯曲
                # Fist: all fingers are bent
                if (angle_list[0]>thr_angle_thumb)  and (angle_list[1]>thr_angle) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]>thr_angle):
                    gesture_str = "fist"
                # 五指张开：所有手指都伸展
                # Five fingers open: all fingers are extended
                elif (angle_list[0]<thr_angle_s)  and (angle_list[1]<thr_angle_s) and (angle_list[2]<thr_angle_s) and (angle_list[3]<thr_angle_s) and (angle_list[4]<thr_angle_s):
                    gesture_str = "five"
                # 手枪：拇指和食指伸展，其他手指弯曲
                # Gun: thumb and index finger extended, other fingers bent
                elif (angle_list[0]<thr_angle_s)  and (angle_list[1]<thr_angle_s) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]>thr_angle):
                    gesture_str = "gun"
                # 爱心：拇指、食指和小指伸展，其他手指弯曲
                # Love: thumb, index finger and pinky extended, other fingers bent
                elif (angle_list[0]<thr_angle_s)  and (angle_list[1]<thr_angle_s) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]<thr_angle_s):
                    gesture_str = "love"
                # 数字一：食指伸展，其他手指弯曲
                # Number one: index finger extended, other fingers bent
                elif (angle_list[0]>5)  and (angle_list[1]<thr_angle_s) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]>thr_angle):
                    gesture_str = "one"
                # 数字六：拇指和小指伸展，其他手指弯曲
                # Number six: thumb and pinky extended, other fingers bent
                elif (angle_list[0]<thr_angle_s)  and (angle_list[1]>thr_angle) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]<thr_angle_s):
                    gesture_str = "six"
                # 数字三：拇指弯曲，食指、中指和无名指伸展，小指弯曲
                # Number three: thumb bent, index, middle and ring fingers extended, pinky bent
                elif (angle_list[0]>thr_angle_thumb)  and (angle_list[1]<thr_angle_s) and (angle_list[2]<thr_angle_s) and (angle_list[3]<thr_angle_s) and (angle_list[4]>thr_angle):
                    gesture_str = "three"
                # 竖大拇指：拇指伸展，其他手指弯曲
                # Thumbs up: thumb extended, other fingers bent
                elif (angle_list[0]<thr_angle_s)  and (angle_list[1]>thr_angle) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]>thr_angle):
                    gesture_str = "thumbUp"
                # 耶：拇指弯曲，食指和中指伸展，其他手指弯曲
                # Yeah: thumb bent, index and middle fingers extended, other fingers bent
                elif (angle_list[0]>thr_angle_thumb)  and (angle_list[1]<thr_angle_s) and (angle_list[2]<thr_angle_s) and (angle_list[3]>thr_angle) and (angle_list[4]>thr_angle):
                    gesture_str = "yeah"
            return gesture_str

# 手掌关键点分类任务
# Hand keypoint classification task
class HandKeyPointClass:
    def __init__(self,hand_det_kmodel,hand_kp_kmodel,det_input_size,kp_input_size,labels,anchors,confidence_threshold=0.25,nms_threshold=0.3,nms_option=False,strides=[8,16,32],rgb888p_size=[1280,720],display_size=[1920,1080],debug_mode=0):
        # 手掌检测模型路径
        # Path to hand detection model
        self.hand_det_kmodel=hand_det_kmodel
        # 手掌关键点模型路径
        # Path to hand keypoint model
        self.hand_kp_kmodel=hand_kp_kmodel
        # 手掌检测模型输入分辨率
        # Hand detection model input resolution
        self.det_input_size=det_input_size
        # 手掌关键点模型输入分辨率
        # Hand keypoint model input resolution
        self.kp_input_size=kp_input_size
        # 标签列表
        # List of labels
        self.labels=labels
        # anchors
        # Anchors
        self.anchors=anchors
        # 置信度阈值
        # Confidence threshold
        self.confidence_threshold=confidence_threshold
        # nms阈值
        # NMS threshold
        self.nms_threshold=nms_threshold
        # NMS选项
        # NMS option
        self.nms_option=nms_option
        # 特征下采样倍数
        # Feature downsampling factors
        self.strides=strides
        # sensor给到AI的图像分辨率，宽16字节对齐
        # Image resolution from sensor to AI, width aligned to 16 bytes
        self.rgb888p_size=[ALIGN_UP(rgb888p_size[0],16),rgb888p_size[1]]
        # 视频输出VO分辨率，宽16字节对齐
        # Video output resolution, width aligned to 16 bytes
        self.display_size=[ALIGN_UP(display_size[0],16),display_size[1]]
        # debug_mode模式
        # Debug mode
        self.debug_mode=debug_mode
        # 创建手掌检测和手掌关键点识别对象
        # Create hand detection and hand keypoint recognition objects
        self.hand_det=HandDetApp(self.hand_det_kmodel,self.labels,model_input_size=self.det_input_size,anchors=self.anchors,confidence_threshold=self.confidence_threshold,nms_threshold=self.nms_threshold,nms_option=self.nms_option,strides=self.strides,rgb888p_size=self.rgb888p_size,display_size=self.display_size,debug_mode=0)
        self.hand_kp=HandKPClassApp(self.hand_kp_kmodel,model_input_size=self.kp_input_size,rgb888p_size=self.rgb888p_size,display_size=self.display_size)
        # 配置手掌检测的预处理
        # Configure preprocessing for hand detection
        self.hand_det.config_preprocess()

    # run函数：执行手掌检测和关键点识别的完整流程
    # Run function: execute the complete process of hand detection and keypoint recognition
    def run(self,input_np):
        # 执行手掌检测
        # Perform hand detection
        det_boxes=self.hand_det.run(input_np)
        # 初始化结果列表
        # Initialize result lists
        boxes=[]
        gesture_res=[]
        # 对于检测到的每一个手掌执行关键点识别
        # Perform keypoint recognition for each detected hand
        for det_box in det_boxes:
            # 获取检测框坐标
            # Get detection box coordinates
            x1, y1, x2, y2 = det_box[2],det_box[3],det_box[4],det_box[5]
            # 计算宽高
            # Calculate width and height
            w,h= int(x2 - x1),int(y2 - y1)
            # 过滤太小的手掌或位于边缘的手掌
            # Filter out hands that are too small or at the edge
            if (h<(0.1*self.rgb888p_size[1])):
                continue
            if (w<(0.25*self.rgb888p_size[0]) and ((x1<(0.03*self.rgb888p_size[0])) or (x2>(0.97*self.rgb888p_size[0])))):
                continue
            if (w<(0.15*self.rgb888p_size[0]) and ((x1<(0.01*self.rgb888p_size[0])) or (x2>(0.99*self.rgb888p_size[0])))):
                continue
            # 配置关键点识别的预处理
            # Configure preprocessing for keypoint recognition
            self.hand_kp.config_preprocess(det_box)
            # 执行关键点识别
            # Perform keypoint recognition
            results_show,gesture=self.hand_kp.run(input_np)
            # 保存结果
            # Save results
            gesture_res.append((results_show,gesture))
            boxes.append(det_box)
        return boxes,gesture_res

    # 绘制效果，绘制关键点、手掌检测框和识别结果
    # Draw results, including keypoints, hand detection boxes and recognition results
    def draw_result(self,pl,dets,gesture_res):
        # 清除OSD图像
        # Clear OSD image
        pl.osd_img.clear()
        # 如果检测到手掌，则绘制结果
        # If hands are detected, draw results
        if len(dets)>0:
            # 遍历每个检测结果
            # Iterate through each detection result
            for k in range(len(dets)):
                # 获取检测框
                # Get detection box
                det_box=dets[k]
                # 获取检测框坐标
                # Get detection box coordinates
                x1, y1, x2, y2 = det_box[2],det_box[3],det_box[4],det_box[5]
                # 计算宽高
                # Calculate width and height
                w,h= int(x2 - x1),int(y2 - y1)
                # 过滤太小的手掌或位于边缘的手掌
                # Filter out hands that are too small or at the edge
                if (h<(0.1*self.rgb888p_size[1])):
                    continue
                if (w<(0.25*self.rgb888p_size[0]) and ((x1<(0.03*self.rgb888p_size[0])) or (x2>(0.97*self.rgb888p_size[0])))):
                    continue
                if (w<(0.15*self.rgb888p_size[0]) and ((x1<(0.01*self.rgb888p_size[0])) or (x2>(0.99*self.rgb888p_size[0])))):
                    continue
                # 计算在显示尺寸中的宽高和位置
                # Calculate width, height and position in display size
                w_det = int(float(x2 - x1) * self.display_size[0] // self.rgb888p_size[0])
                h_det = int(float(y2 - y1) * self.display_size[1] // self.rgb888p_size[1])
                x_det = int(x1*self.display_size[0] // self.rgb888p_size[0])
                y_det = int(y1*self.display_size[1] // self.rgb888p_size[1])
                # 绘制检测框
                # Draw detection box
                pl.osd_img.draw_rectangle(x_det, y_det, w_det, h_det, color=(255, 0, 255, 0), thickness = 2)

                # 获取关键点结果
                # Get keypoint results
                results_show=gesture_res[k][0]
                # 绘制每个关键点
                # Draw each keypoint
                for i in range(len(results_show)/2):
                    pl.osd_img.draw_circle(results_show[i*2], results_show[i*2+1], 1, color=(255, 0, 255, 0),fill=False)
                # 为每个手指绘制连接线，使用不同颜色区分
                # Draw connection lines for each finger, using different colors
                for i in range(5):
                    j = i*8
                    if i==0:
                        R = 255; G = 0; B = 0
                    if i==1:
                        R = 255; G = 0; B = 255
                    if i==2:
                        R = 255; G = 255; B = 0
                    if i==3:
                        R = 0; G = 255; B = 0
                    if i==4:
                        R = 0; G = 0; B = 255
                    # 绘制手指各关节之间的连接线
                    # Draw connection lines between finger joints
                    pl.osd_img.draw_line(results_show[0], results_show[1], results_show[j+2], results_show[j+3], color=(255,R,G,B), thickness = 3)
                    pl.osd_img.draw_line(results_show[j+2], results_show[j+3], results_show[j+4], results_show[j+5], color=(255,R,G,B), thickness = 3)
                    pl.osd_img.draw_line(results_show[j+4], results_show[j+5], results_show[j+6], results_show[j+7], color=(255,R,G,B), thickness = 3)
                    pl.osd_img.draw_line(results_show[j+6], results_show[j+7], results_show[j+8], results_show[j+9], color=(255,R,G,B), thickness = 3)

                # 获取手势结果并显示
                # Get gesture result and display it
                gesture_str=gesture_res[k][1]
                pl.osd_img.draw_string_advanced( x_det , y_det-50,32, " " + str(gesture_str), color=(255,0, 255, 0))



if __name__=="__main__":
    # 显示模式，默认"hdmi"，可以选择"hdmi"和"lcd"
    # Display mode, default is "hdmi", can choose between "hdmi" and "lcd"
    display_mode="lcd"
    # 设置输入图像分辨率
    # Set input image resolution
    rgb888p_size=[640,480]

    # 根据显示模式设置显示分辨率
    # Set display resolution based on display mode
    if display_mode=="hdmi":
        display_size=[1920,1080]
    else:
        display_size=[640,480]
    # 手掌检测模型路径
    # Path to hand detection model
    hand_det_kmodel_path="/sdcard/kmodel/hand_det.kmodel"
    # 手掌关键点模型路径
    # Path to hand keypoint model
    hand_kp_kmodel_path="/sdcard/kmodel/handkp_det.kmodel"
    # 设置锚框文件路径
    # Set path to anchors file
    anchors_path="/sdcard/utils/prior_data_320.bin"
    # 设置模型输入尺寸
    # Set model input sizes
    hand_det_input_size=[512,512]
    hand_kp_input_size=[256,256]
    # 设置阈值
    # Set thresholds
    confidence_threshold=0.2
    nms_threshold=0.5
    # 设置标签和锚框
    # Set labels and anchors
    labels=["hand"]
    anchors = [26,27, 53,52, 75,71, 80,99, 106,82, 99,134, 140,113, 161,172, 245,276]

    # 初始化PipeLine，只关注传给AI的图像分辨率，显示的分辨率
    # Initialize PipeLine, only focus on the image resolution passed to AI and the display resolution
    pl=PipeLine(rgb888p_size=rgb888p_size,display_size=display_size,display_mode=display_mode)
    # 创建Pipeline
    # Create Pipeline
    pl.create()
    # 创建手掌关键点分类对象
    # Create hand keypoint classification object
    hkc=HandKeyPointClass(hand_det_kmodel_path,hand_kp_kmodel_path,det_input_size=hand_det_input_size,kp_input_size=hand_kp_input_size,labels=labels,anchors=anchors,confidence_threshold=confidence_threshold,nms_threshold=nms_threshold,nms_option=False,strides=[8,16,32],rgb888p_size=rgb888p_size,display_size=display_size)
    # 主循环
    # Main loop
    while True:
        with ScopedTiming("total",1):
            img=pl.get_frame()                          # 获取当前帧 / Get current frame
            det_boxes,gesture_res=hkc.run(img)          # 推理当前帧 / Run inference on current frame
            hkc.draw_result(pl,det_boxes,gesture_res)   # 绘制当前帧推理结果 / Draw inference results on current frame
            pl.show_image()                             # 展示推理结果 / Show inference results
            gc.collect()                                # 进行垃圾回收 / Perform garbage collection
    # 释放资源
    # Release resources
    hkc.hand_det.deinit()
    hkc.hand_kp.deinit()
    pl.destroy()