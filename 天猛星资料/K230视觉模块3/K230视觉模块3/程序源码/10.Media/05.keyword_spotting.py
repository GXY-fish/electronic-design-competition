from libs.PipeLine import ScopedTiming        # 导入性能计时工具类 / Import performance timing utility class
from libs.AIBase import AIBase                # 导入AI基础类 / Import AI base class
from libs.AI2D import Ai2d                    # 导入AI 2D处理类 / Import AI 2D processing class
from media.pyaudio import *                   # 导入音频模块，用于音频输入输出 / Import audio module for audio I/O
from media.media import *                     # 导入媒体软件抽象模块，主要封装媒体数据链路及缓冲区 
                                              # Import media abstraction module, mainly encapsulates media data links and buffers
import media.wave as wave                     # 导入wav音频处理模块 / Import wav audio processing module
import nncase_runtime as nn                   # 导入nncase运行模块，封装了kpu（kmodel推理）和ai2d（图像预处理加速）操作
                                              # Import nncase runtime module, which encapsulates kpu (kmodel inference) and ai2d (image preprocessing acceleration) operations
import ulab.numpy as np                       # 导入类numpy操作模块，提供类似numpy的数组操作但接口可能有所不同
                                              # Import numpy-like operation module, providing similar array operations with potentially different interfaces
import aidemo                                 # 导入aidemo模块，封装AI演示相关的前处理、后处理等操作
                                              # Import aidemo module, which encapsulates preprocessing and postprocessing operations for AI demos
import time                                   # 导入时间模块，用于时间统计 / Import time module for time statistics
import struct                                 # 导入字节字符转换模块，用于处理二进制数据 / Import byte-character conversion module for handling binary data
import gc                                     # 导入垃圾回收模块，用于内存管理 / Import garbage collection module for memory management
import os,sys                                 # 导入操作系统接口模块，提供系统级功能 / Import OS interface modules, providing system-level functionality

# 自定义关键词唤醒类，继承自AIBase基类
# Custom keyword wake-up class, inheriting from AIBase base class
class KWSApp(AIBase):
    def __init__(self, kmodel_path, threshold, debug_mode=0):
        super().__init__(kmodel_path)          # 调用基类的构造函数初始化模型
                                               # Call the constructor of the base class to initialize the model
        self.kmodel_path = kmodel_path         # 保存模型文件路径 / Save the path to the model file
        self.threshold = threshold             # 设置唤醒词检测阈值 / Set the detection threshold for wake words
        self.debug_mode = debug_mode           # 设置调试模式，用于控制日志输出 / Set debug mode for controlling log output
        self.cache_np = np.zeros((1, 256, 105), dtype=np.float)  # 初始化缓存数组，用于存储模型状态
                                                                  # Initialize cache array to store model state

    # 自定义预处理方法，将音频数据转换为模型输入格式
    # Custom preprocessing method to convert audio data to model input format
    def preprocess(self, pcm_data):
        pcm_data_list = []
        # 获取音频流数据并转换格式
        # Get audio stream data and convert format
        for i in range(0, len(pcm_data), 2):
            # 每两个字节组织成一个有符号整数，然后将其转换为浮点数
            # Organize every two bytes into a signed integer, then convert it to a floating point number
            int_pcm_data = struct.unpack("<h", pcm_data[i:i+2])[0]  # 使用小端格式解析16位有符号整数
                                                                     # Parse 16-bit signed integer in little-endian format
            float_pcm_data = float(int_pcm_data)                     # 转换为浮点数 / Convert to float
            pcm_data_list.append(float_pcm_data)                     # 添加到列表中 / Add to list
            
        # 将pcm数据处理为模型输入的特征向量
        # Process PCM data into feature vectors for model input
        mp_feats = aidemo.kws_preprocess(fp, pcm_data_list)[0]       # 调用aidemo模块的预处理函数提取音频特征
                                                                      # Call aidemo module's preprocessing function to extract audio features
        mp_feats_np = np.array(mp_feats).reshape((1, 30, 40))        # 重塑数组形状为模型所需的输入维度
                                                                      # Reshape array to required input dimensions for the model
        audio_input_tensor = nn.from_numpy(mp_feats_np)              # 将numpy数组转换为nncase的tensor
                                                                      # Convert numpy array to nncase tensor
        cache_input_tensor = nn.from_numpy(self.cache_np)            # 将缓存数组转换为nncase的tensor
                                                                      # Convert cache array to nncase tensor
        return [audio_input_tensor, cache_input_tensor]               # 返回模型需要的输入tensor列表
                                                                      # Return list of input tensors needed by the model

    # 自定义后处理方法，处理模型输出结果
    # Custom postprocessing method to handle model output results
    def postprocess(self, results):
        with ScopedTiming("postprocess", self.debug_mode > 0):       # 使用计时工具测量后处理耗时（仅在调试模式开启时）
                                                                      # Use timing tool to measure postprocessing time (only when debug mode is on)
            logits_np = results[0]                                    # 获取第一个输出结果（预测概率） 
                                                                      # Get the first output result (prediction probabilities)
            self.cache_np = results[1]                                # 更新缓存数组，用于下一次推理
                                                                      # Update cache array for next inference
            max_logits = np.max(logits_np, axis=1)[0]                 # 获取每个样本的最大概率值
                                                                      # Get the maximum probability value for each sample
            max_p = np.max(max_logits)                                # 获取最大概率值 / Get the maximum probability
            idx = np.argmax(max_logits)                               # 获取最大概率对应的索引 / Get the index of maximum probability
            
            # 如果分数大于阈值，且idx==1(即包含唤醒词)，返回1表示检测到唤醒词
            # If the score is greater than the threshold and idx==1 (contains wake word), return 1 indicating wake word detected
            if max_p > self.threshold and idx == 1:
                return 1
            else:
                return 0                                              # 否则返回0表示未检测到唤醒词
                                                                      # Otherwise return 0 indicating no wake word detected


if __name__ == "__main__":
    os.exitpoint(os.EXITPOINT_ENABLE)                                # 启用退出点检查，允许程序被外部中断
                                                                      # Enable exit point check, allowing the program to be interrupted externally
    nn.shrink_memory_pool()                                           # 收缩内存池，释放不必要的内存
                                                                      # Shrink memory pool to free unnecessary memory
    # 设置模型路径和其他参数
    # Set model path and other parameters
    kmodel_path = "/sdcard/kmodel/kws.kmodel"                # 模型文件路径 / Path to the model file
    
    # 其它参数 / Other parameters
    THRESH = 0.5                                                      # 检测阈值，概率大于此值被认为是有效检测
                                                                      # Detection threshold, probability greater than this is considered valid detection
    SAMPLE_RATE = 16000                                               # 采样率16000Hz，即每秒采样16000次
                                                                      # Sampling rate 16000Hz, i.e., 16000 samples per second
    CHANNELS = 1                                                      # 通道数 1为单声道，2为立体声
                                                                      # Number of channels, 1 for mono, 2 for stereo
    FORMAT = paInt16                                                  # 音频输入输出格式 paInt16（16位整数）
                                                                      # Audio I/O format paInt16 (16-bit integer)
    CHUNK = int(0.3 * 16000)                                          # 每次读取音频数据的帧数，设置为0.3秒的帧数
                                                                      # Number of frames to read each time, set to frames for 0.3 seconds
    reply_wav_file = "/sdcard/utils/wozai.wav"               # 唤醒词识别成功后播放的回复音频路径
                                                                      # Path to reply audio file played after successful wake word detection

    # 初始化音频预处理接口
    # Initialize audio preprocessing interface
    fp = aidemo.kws_fp_create()                                       # 创建音频特征处理器
                                                                      # Create audio feature processor
    # 初始化音频流
    # Initialize audio stream
    p = PyAudio()                                                     # 创建PyAudio实例 / Create PyAudio instance
    p.initialize(CHUNK)                                               # 使用指定的帧大小初始化 / Initialize with specified frame size
    MediaManager.init()                                               # 初始化媒体管理器（vb buffer）
                                                                      # Initialize media manager (vb buffer)
    
    # 用于采集实时音频数据
    # For collecting real-time audio data
    input_stream = p.open(format=FORMAT,                              # 打开输入音频流，配置格式、通道数、采样率等参数
                          channels=CHANNELS,                          # Open input audio stream with specified format, channels, sampling rate, etc.
                          rate=SAMPLE_RATE,
                          input=True,
                          frames_per_buffer=CHUNK)
    input_stream.volume(vol = 100)                                    # 设置输入音量为100% / Set input volume to 100%
    
    # 用于播放回复音频
    # For playing reply audio
    output_stream = p.open(format=FORMAT,                             # 打开输出音频流，配置格式、通道数、采样率等参数
                           channels=CHANNELS,                         # Open output audio stream with specified format, channels, sampling rate, etc.
                           rate=SAMPLE_RATE,
                           output=True,
                           frames_per_buffer=CHUNK)
    output_stream.volume(vol = 100) 
    # 初始化自定义关键词唤醒实例
    # Initialize custom keyword wake-up instance
    kws = KWSApp(kmodel_path, threshold=THRESH, debug_mode=0)         # 创建KWSApp实例，配置模型路径、阈值和调试模式
                                                                      # Create KWSApp instance with specified model path, threshold, and debug mode

    try:
        while True:
            os.exitpoint()                                            # 检查是否有退出信号 / Check for exit signal
            with ScopedTiming("total", 1):                            # 测量整个循环的执行时间 / Measure execution time of the entire loop
                pcm_data = input_stream.read()                        # 读取音频数据 / Read audio data
                res = kws.run(pcm_data)                               # 运行关键词检测 / Run keyword detection
                if res:
                    print("====Detected XiaonanXiaonan!====")         # 打印检测到的唤醒词信息
                                                                      # Print information about detected wake word
                    wf = wave.open(reply_wav_file, "rb")              # 打开回复音频文件 / Open reply audio file
                    wav_data = wf.read_frames(CHUNK)                  # 读取音频帧 / Read audio frames
                    while wav_data:                                   # 循环读取并播放音频 / Loop to read and play audio
                        output_stream.write(wav_data)                 # 播放音频数据 / Play audio data
                        wav_data = wf.read_frames(CHUNK)              # 读取下一帧 / Read next frame
                    time.sleep(1)                                     # 时间缓冲，用于播放回复声音
                                                                      # Time buffer for playing reply sound
                    wf.close()                                        # 关闭音频文件 / Close audio file
                else:
                    print("Deactivated!")                             # 打印未检测到唤醒词信息
                                                                      # Print information about no wake word detected
                gc.collect()                                          # 执行垃圾回收，释放内存
                                                                      # Perform garbage collection to free memory
    except Exception as e:
        sys.print_exception(e)                                        # 打印异常信息 / Print exception information
    finally:
        # 清理资源，关闭所有打开的流和接口
        # Clean up resources, close all opened streams and interfaces
        input_stream.stop_stream()                                    # 停止输入流 / Stop input stream
        output_stream.stop_stream()                                   # 停止输出流 / Stop output stream
        input_stream.close()                                          # 关闭输入流 / Close input stream
        output_stream.close()                                         # 关闭输出流 / Close output stream
        p.terminate()                                                 # 终止PyAudio / Terminate PyAudio
        MediaManager.deinit()                                         # 反初始化媒体管理器，释放vb buffer
                                                                      # Deinitialize media manager, free vb buffer
        aidemo.kws_fp_destroy(fp)                                     # 销毁音频特征处理器 / Destroy audio feature processor
        kws.deinit()                                                  # 反初始化KWS应用，释放模型资源
                                                                      # Deinitialize KWS application, free model resources