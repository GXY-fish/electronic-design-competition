from libs.PipeLine import PipeLine, ScopedTiming  # 导入Pipeline和计时工具类 (Import Pipeline and timing tool class)
from libs.AIBase import AIBase  # 导入AI基础类 (Import AI base class)
from libs.AI2D import Ai2d  # 导入Ai2d图像预处理类 (Import Ai2d image preprocessing class)
import os  # 导入操作系统接口模块 (Import operating system interface module)
import ujson  # 导入json处理模块（microPython版本的json库）(Import json processing module - microPython version of json library)
from media.media import *  # 导入媒体处理相关类 (Import media processing related classes)
from time import *  # 导入时间相关函数 (Import time-related functions)
import nncase_runtime as nn  # 导入nncase运行时库 (Import nncase runtime library)
import ulab.numpy as np  # 导入微型numpy库（针对嵌入式设备优化）(Import tiny numpy library optimized for embedded devices)
import time  # 导入时间模块 (Import time module)
import utime  # 导入microPython特定的时间模块 (Import microPython-specific time module)
import image  # 导入图像处理模块 (Import image processing module)
import random  # 导入随机数生成模块 (Import random number generation module)
import gc  # 导入垃圾回收模块 (Import garbage collection module)
import sys  # 导入系统模块 (Import system module)
import aidemo,math  # 导入自定义AI演示库和数学库 (Import custom AI demo library and math library)

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

    def analyze_pose(self, kpses):
        """
        分析人体姿势，判断手臂的伸直/弯曲状态及朝向
        Analyze human pose, determine arm straight/bent state and direction

        Args:
            kpses: 关键点数据，格式为 [num_persons, num_keypoints, 3]，每个关键点包含 (x, y, confidence)
                  (Keypoint data in format [num_persons, num_keypoints, 3], each keypoint contains (x, y, confidence))
        Returns:
            pose_results: 包含每个人的姿势分析结果的列表 (List containing pose analysis results for each person)
        """
        pose_results = []
        for i in range(len(kpses)):  # 遍历每个检测到的人 (Iterate through each detected person)
            person_kps = kpses[i]
            person_pose = {}

            # 左臂分析（关键点 5: 左肩, 7: 左肘, 9: 左手腕）
            # Left arm analysis (keypoint 5: left shoulder, 7: left elbow, 9: left wrist)
            left_arm_result = self._analyze_arm(
                shoulder=person_kps[5],  # 关键点索引从1开始，数组从0开始 (Keypoint index starts from 1, array starts from 0)
                elbow=person_kps[7],
                wrist=person_kps[9]
            )
            person_pose["left_arm"] = left_arm_result

            # 右臂分析（关键点 6: 右肩, 8: 右肘, 10: 右手腕）
            # Right arm analysis (keypoint 6: right shoulder, 8: right elbow, 10: right wrist)
            right_arm_result = self._analyze_arm(
                shoulder=person_kps[6],
                elbow=person_kps[8],
                wrist=person_kps[10]
            )
            person_pose["right_arm"] = right_arm_result

            pose_results.append(person_pose)

        return pose_results

    def _analyze_arm(self, shoulder, elbow, wrist):
        """
        分析单条手臂的姿势
        Analyze the pose of a single arm

        Args:
            shoulder: 肩关节坐标 (x, y, confidence) (Shoulder joint coordinates (x, y, confidence))
            elbow: 肘关节坐标 (x, y, confidence) (Elbow joint coordinates (x, y, confidence))
            wrist: 手腕坐标 (x, y, confidence) (Wrist coordinates (x, y, confidence))
        Returns:
            result: 包含伸直/弯曲状态和朝向的字典 (Dictionary containing straight/bent state and direction)
        """
        result = {"state": "unknown", "direction": "unknown"}

        # 检查关键点是否有效（置信度 > 0）(Check if keypoints are valid (confidence > 0))
        if shoulder[2] <= 0 or elbow[2] <= 0 or wrist[2] <= 0:
            return result

        # 计算肩-肘向量和肘-腕向量 (Calculate shoulder-elbow vector and elbow-wrist vector)
        vec_shoulder_to_elbow = np.array([elbow[0] - shoulder[0], elbow[1] - shoulder[1]])
        vec_elbow_to_wrist = np.array([wrist[0] - elbow[0], wrist[1] - elbow[1]])

        # 计算向量模长 (Calculate vector magnitudes)
        norm_se = np.linalg.norm(vec_shoulder_to_elbow)
        norm_ew = np.linalg.norm(vec_elbow_to_wrist)

        # 避免除零 (Avoid division by zero)
        if norm_se == 0 or norm_ew == 0:
            return result

        # 计算夹角（角度）(Calculate angle (in degrees))
        cos_theta = np.dot(vec_shoulder_to_elbow, vec_elbow_to_wrist) / (norm_se * norm_ew)
        cos_theta = min(1.0, max(-1.0, cos_theta))  # 限制cos值范围 (Restrict cos value range)
        angle = math.degrees(math.acos(cos_theta))

        # 判断手臂伸直或弯曲 (Determine if arm is straight or bent)
        if angle <= 60:
            result["state"] = "straight"
        elif angle > 60:
            result["state"] = "bent"

        # 判断手臂朝向 (Determine arm direction)
        dx = elbow[0] - shoulder[0]
        dy = elbow[1] - shoulder[1]
        if abs(dx) > abs(dy):
            # 水平方向为主 (Primarily horizontal direction)
            result["direction"] = "left" if dx > 0 else "right"
        else:
            # 垂直方向为主 (Primarily vertical direction)
            result["direction"] = "down" if dy > 0 else "up"

        return result

    def draw_result(self, pl, res, pose_results=None):
        """
        绘制结果，包括骨骼、关键点和姿势信息
        Draw results including skeleton, keypoints and pose information

        Args:
            pl: PipeLine实例 (PipeLine instance)
            res: 检测结果 (Detection results)
            pose_results: 姿势分析结果 (Pose analysis results)
        """
        with ScopedTiming("display_draw", self.debug_mode > 0):
            if res[0]:  # 如果检测到人 (If persons are detected)
                pl.osd_img.clear()
                kpses = res[1]
                for i in range(len(res[0])):
                    # 绘制关键点和骨骼（原有逻辑）(Draw keypoints and skeleton (original logic))
                    for k in range(17+2):
                        if k < 17:
                            kps_x, kps_y, kps_s = round(kpses[i][k][0]), round(kpses[i][k][1]), kpses[i][k][2]
                            kps_x1 = int(float(kps_x) * self.display_size[0] // self.rgb888p_size[0])
                            kps_y1 = int(float(kps_y) * self.display_size[1] // self.rgb888p_size[1])
                            if kps_s > 0:
                                pl.osd_img.draw_circle(kps_x1, kps_y1, 5, self.KPS_COLORS[k], 4)

                        ske = self.SKELETON[k]
                        pos1_x, pos1_y = round(kpses[i][ske[0]-1][0]), round(kpses[i][ske[0]-1][1])
                        pos1_x_ = int(float(pos1_x) * self.display_size[0] // self.rgb888p_size[0])
                        pos1_y_ = int(float(pos1_y) * self.display_size[1] // self.rgb888p_size[1])

                        pos2_x, pos2_y = round(kpses[i][(ske[1]-1)][0]), round(kpses[i][(ske[1]-1)][1])
                        pos2_x_ = int(float(pos2_x) * self.display_size[0] // self.rgb888p_size[0])
                        pos2_y_ = int(float(pos2_y) * self.display_size[1] // self.rgb888p_size[1])

                        pos1_s, pos2_s = kpses[i][(ske[0]-1)][2], kpses[i][(ske[1]-1)][2]
                        if pos1_s > 0.0 and pos2_s > 0.0:
                            pl.osd_img.draw_line(pos1_x_, pos1_y_, pos2_x_, pos2_y_, self.LIMB_COLORS[k], 4)

                    # 绘制姿势信息 (Draw pose information)
                    if pose_results and i < len(pose_results):
                        pose = pose_results[i]
                        # 显示左臂信息 (Display left arm information)
                        left_arm_text = f"Left Arm: {pose['left_arm']['state']}, {pose['left_arm']['direction']}"
                        pl.osd_img.draw_string_advanced(
                            10, 10 + i * 60, 20, left_arm_text, (255, 255, 255, 255)
                        )
                        # 显示右臂信息 (Display right arm information)
                        right_arm_text = f"Right Arm: {pose['right_arm']['state']}, {pose['right_arm']['direction']}"
                        pl.osd_img.draw_string_advanced(
                            10, 30 + i * 60, 20, right_arm_text, (255, 255, 255, 255)
                        )
                gc.collect()
            else:
                pl.osd_img.clear()

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
        img = pl.get_frame()  # 获取一帧图像 (Get a frame)
        res = person_kp.run(img)  # 运行人体关键点检测 (Run person keypoint detection)
        # 分析姿势 (Analyze pose)
        pose_results = person_kp.analyze_pose(res[1]) if res[0] else []
        # 绘制结果，包括姿势信息 (Draw results including pose information)
        person_kp.draw_result(pl, res, pose_results)
        pl.show_image()  # 显示图像 (Display image)
        gc.collect()  # 执行垃圾回收 (Perform garbage collection)

    person_kp.deinit()  # 释放资源 (Release resources)
    pl.destroy()  # 销毁PipeLine (Destroy PipeLine)
