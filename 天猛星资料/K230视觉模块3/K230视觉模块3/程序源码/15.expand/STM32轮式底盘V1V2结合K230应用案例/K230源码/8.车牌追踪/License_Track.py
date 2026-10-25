# 导入所需的库文件 Import required libraries
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
import utime
import image
import random
import gc
import sys
import aidemo

from libs.YbProtocol import YbProtocol
from ybUtils.YbUart import YbUart
# uart = None
uart = YbUart(baudrate=115200)
pto = YbProtocol()


# 车牌检测类 License Plate Detection Class
class LicenceDetectionApp(AIBase):
    """
    车牌检测应用类，继承自AIBase
    License plate detection application class, inherited from AIBase
    """
    def __init__(self, kmodel_path, model_input_size, confidence_threshold=0.5, nms_threshold=0.2, rgb888p_size=[224,224], display_size=[1920,1080], debug_mode=0):
        """
        初始化函数 Initialization function
        参数 Parameters:
            kmodel_path: 模型路径 Model path
            model_input_size: 模型输入尺寸 Model input size
            confidence_threshold: 置信度阈值 Confidence threshold
            nms_threshold: NMS阈值 NMS threshold
            rgb888p_size: 输入图像尺寸 Input image size
            display_size: 显示尺寸 Display size
            debug_mode: 调试模式 Debug mode
        """
        super().__init__(kmodel_path, model_input_size, rgb888p_size, debug_mode)
        self.kmodel_path = kmodel_path
        self.model_input_size = model_input_size
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        # 确保宽度是16的倍数 Ensure width is multiple of 16
        self.rgb888p_size = [ALIGN_UP(rgb888p_size[0], 16), rgb888p_size[1]]
        self.display_size = [ALIGN_UP(display_size[0], 16), display_size[1]]
        self.debug_mode = debug_mode

        # 初始化AI2D实例用于图像预处理 Initialize AI2D instance for image preprocessing
        self.ai2d = Ai2d(debug_mode)
        self.ai2d.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT, nn.ai2d_format.NCHW_FMT, np.uint8, np.uint8)

    def config_preprocess(self, input_image_size=None):
        """
        配置图像预处理参数 Configure image preprocessing parameters
        """
        with ScopedTiming("set preprocess config", self.debug_mode > 0):
            ai2d_input_size = input_image_size if input_image_size else self.rgb888p_size
            # 配置双线性插值方法 Configure bilinear interpolation method
            self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
            self.ai2d.build([1,3,ai2d_input_size[1],ai2d_input_size[0]],[1,3,self.model_input_size[1],self.model_input_size[0]])

    def postprocess(self, results):
        """
        后处理函数 Postprocessing function
        对模型输出结果进行处理 Process model output results
        """
        with ScopedTiming("postprocess", self.debug_mode > 0):
            det_res = aidemo.licence_det_postprocess(results,
                                                   [self.rgb888p_size[1], self.rgb888p_size[0]],
                                                   self.model_input_size,
                                                   self.confidence_threshold,
                                                   self.nms_threshold)
            return det_res

    def draw_result(self, pl, dets):
        """
        绘制检测结果 Draw detection results
        参数 Parameters:
            pl: PipeLine实例 PipeLine instance
            dets: 检测结果 Detection results
        """
        with ScopedTiming("display_draw", self.debug_mode > 0):
            if dets:
                pl.osd_img.clear()
                point_8 = np.zeros((8), dtype=np.int16)
                for det in dets:
                    # 坐标转换 Coordinate conversion
                    for i in range(4):
                        x = det[i * 2 + 0] / self.rgb888p_size[0] * self.display_size[0]
                        y = det[i * 2 + 1] / self.rgb888p_size[1] * self.display_size[1]
                        point_8[i * 2 + 0] = int(x)
                        point_8[i * 2 + 1] = int(y)
                    # 绘制检测框 Draw detection box
                    for i in range(4):
                        pl.osd_img.draw_line(point_8[i * 2 + 0],
                                           point_8[i * 2 + 1],
                                           point_8[(i + 1) % 4 * 2 + 0],
                                           point_8[(i + 1) % 4 * 2 + 1],
                                           color=(255, 0, 255, 0),
                                           thickness=4)

                    pto_data = pto.get_licence_detect_data(point_8)
                    uart.send(pto_data)
                    print(pto_data)
            else:
                pl.osd_img.clear()

def exce_demo(pl):
    """
    执行演示函数 Execute demo function
    """
    global licence_det
    kmodel_path="/sdcard/kmodel/LPD_640.kmodel"
    confidence_threshold = 0.2
    nms_threshold = 0.2

    try:
        # 初始化车牌检测实例 Initialize license plate detection instance
        licence_det=LicenceDetectionApp(kmodel_path,
                                      model_input_size=[640,640],
                                      confidence_threshold=confidence_threshold,
                                      nms_threshold=nms_threshold,
                                      rgb888p_size=rgb888p_size,
                                      display_size=display_size,
                                      debug_mode=0)
        licence_det.config_preprocess()

        while True:
            with ScopedTiming("total", 0):
                img=pl.get_frame()  # 获取图像帧 Get image frame
                res=licence_det.run(img)  # 执行检测 Run detection
                licence_det.draw_result(pl,res)  # 绘制结果 Draw results
                pl.show_image()  # 显示图像 Show image
                gc.collect()  # 垃圾回收 Garbage collection

    except Exception as e:
        print("车牌检测功能退出 License plate detection exit")
    finally:
        licence_det.deinit()  # 释放资源 Release resources

def exit_demo():
    """
    退出演示函数 Exit demo function
    """
    global licence_det
    licence_det.deinit()

if __name__=="__main__":
    # 设置显示参数 Set display parameters
    rgb888p_size=[640,360]  # 输入图像尺寸 Input image size
    display_size=[640,480]    # 显示尺寸 Display size
    display_mode="lcd"        # 显示模式 Display mode

    # 创建并初始化PipeLine Create and initialize PipeLine
    pl=PipeLine(rgb888p_size=rgb888p_size,
                display_size=display_size,
                display_mode=display_mode)
    pl.create()

    # 执行演示程序 Execute demo program
    exce_demo(pl)
