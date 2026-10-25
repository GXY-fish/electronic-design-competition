from libs.PipeLine import ScopedTiming  # 用于计时和性能分析的工具类 / Tool class for timing and performance analysis
from libs.AIBase import AIBase         # AI基类，提供模型加载和推理的基础功能 / Base class for AI, provides basic functions for model loading and inference
from libs.AI2D import Ai2d             # AI 2D处理模块，用于图像预处理加速 / AI 2D processing module for accelerating image preprocessing
from media.pyaudio import *            # 音频模块，用于音频输入输出操作 / Audio module for audio input and output operations
from media.media import *              # 软件抽象模块，主要封装媒体数据链路以及媒体缓冲区 / Software abstraction module, mainly encapsulates media data links and buffers
import media.wave as wave              # WAV音频处理模块，用于处理WAV格式音频 / WAV audio processing module for handling WAV format audio
import nncase_runtime as nn            # nncase运行模块，封装了KPU（kmodel推理）和AI2D（图片预处理加速）操作 / nncase runtime module, encapsulates KPU (kmodel inference) and AI2D (image preprocessing acceleration) operations
import ulab.numpy as np                # 类似Python的NumPy操作，但接口有所不同 / Similar to Python's NumPy operations, but with some interface differences
import aidemo                          # aidemo模块，封装AI demo相关前处理、后处理等操作 / aidemo module, encapsulates AI demo-related preprocessing and postprocessing operations
import time                            # 时间统计模块 / Time statistics module
import struct                          # 字节字符转换模块，用于字节与数据类型转换 / Byte-character conversion module for converting between bytes and data types
import gc                              # 垃圾回收模块，用于内存管理 / Garbage collection module for memory management
import os, sys                         # 操作系统接口模块，提供文件和系统操作功能 / Operating system interface module, provides file and system operation functions

from ybUtils.YbSpeaker import YbSpeaker


# 自定义TTS中文编码器类，继承自AIBase基类 / Custom TTS Chinese encoder class, inherits from AIBase base class
class EncoderApp(AIBase):
    def __init__(self, kmodel_path, dict_path, phase_path, mapfile, debug_mode=0):
        super().__init__(kmodel_path)  # 调用基类的构造函数，加载模型 / Call the base class constructor to load the model
        self.kmodel_path = kmodel_path  # 模型文件路径 / Path to the model file
        self.debug_mode = debug_mode    # 是否开启调试模式，0为关闭 / Whether to enable debug mode, 0 means disabled
        # 初始化中文TTS预处理对象 / Initialize Chinese TTS preprocessing object
        self.ttszh = aidemo.tts_zh_create(dict_path, phase_path, mapfile)
        self.data = None                # 预处理后的数据 / Preprocessed data
        self.data_len = 0               # 数据长度 / Data length
        self.durition_sum = 0           # 音素持续时间总和 / Total duration of phonemes

    # 自定义编码器预处理，返回模型输入tensor列表 / Custom encoder preprocessing, returns a list of model input tensors
    def preprocess(self, text):
        with ScopedTiming("encoder preprocess", self.debug_mode > 0):  # 计时预处理过程 / Time the preprocessing process
            preprocess_data = aidemo.tts_zh_preprocess(self.ttszh, text)  # 对输入文本进行预处理 / Preprocess the input text
            self.data = preprocess_data[0]      # 预处理后的序列数据 / Preprocessed sequence data
            self.data_len = preprocess_data[1]  # 序列数据长度 / Length of sequence data
            # 创建编码器模型输入并与模型绑定，编码器包含两个输入 / Create encoder model inputs and bind them to the model, encoder has two inputs
            # 编码器序列数据 / Encoder sequence data
            enc_seq_input_tensor = nn.from_numpy(np.array(self.data))
            # 编码器speaker数据，固定为0.0 / Encoder speaker data, fixed at 0.0
            enc_speaker_input_tensor = nn.from_numpy(np.array([0.0]))
            return [enc_speaker_input_tensor, enc_seq_input_tensor]  # 返回输入tensor列表 / Return list of input tensors

    # 自定义编码器的后处理，results是模型输出ndarray列表 / Custom encoder postprocessing, results is a list of model output ndarrays
    def postprocess(self, results):
        with ScopedTiming("encoder postprocess", self.debug_mode > 0):  # 计时后处理过程 / Time the postprocessing process
            enc_output_0_np = results[0]  # 编码器输出0，音素编码向量 / Encoder output 0, phoneme encoding vectors
            enc_output_1_np = results[1]  # 编码器输出1，音素持续时间 / Encoder output 1, phoneme durations
            # 获取音素持续时间并计算总和 / Get phoneme durations and calculate the total
            duritions = enc_output_1_np[0][:int(self.data_len[0])]
            self.durition_sum = int(np.sum(duritions))
            # 解码器输入维度为（1,600,256），不足部分需要padding / Decoder input dimension is (1,600,256), padding is needed for insufficient parts
            max_value = 13  # 最大持续时间限制 / Maximum duration limit
            while self.durition_sum > 600:  # 如果总持续时间超过600，调整持续时间 / If total duration exceeds 600, adjust durations
                for i in range(len(duritions)):
                    if duritions[i] > max_value:
                        duritions[i] = max_value
                max_value -= 1
                self.durition_sum = np.sum(duritions)
            # 初始化解码器输入并填充数据 / Initialize decoder input and fill data
            dec_input = np.zeros((1, 600, 256), dtype=np.float)
            m_pad = 600 - self.durition_sum  # 计算需要填充的长度 / Calculate the length to pad
            k = 0
            for i in range(len(duritions)):
                for j in range(int(duritions[i])):
                    dec_input[0][k] = enc_output_0_np[0][i]  # 根据持续时间重复音素向量 / Repeat phoneme vectors based on duration
                    k += 1
            return dec_input, self.durition_sum  # 返回解码器输入和总持续时间 / Return decoder input and total duration

# 自定义TTS中文解码器类，继承自AIBase基类 / Custom TTS Chinese decoder class, inherits from AIBase base class
class DecoderApp(AIBase):
    def __init__(self, kmodel_path, debug_mode=0):
        super().__init__(kmodel_path)  # 调用基类的构造函数 / Call the base class constructor
        self.kmodel_path = kmodel_path  # 模型文件路径 / Path to the model file
        self.debug_mode = debug_mode    # 是否开启调试模式 / Whether to enable debug mode

    # 自定义解码器预处理，返回模型输入tensor列表 / Custom decoder preprocessing, returns a list of model input tensors
    def preprocess(self, dec_input):
        with ScopedTiming("decoder preprocess", self.debug_mode > 0):  # 计时预处理过程 / Time the preprocessing process
            dec_input_tensor = nn.from_numpy(dec_input)  # 将输入转换为tensor / Convert input to tensor
            return [dec_input_tensor]  # 返回输入tensor列表 / Return list of input tensors

    # 自定义解码器后处理，results是模型输出ndarray列表 / Custom decoder postprocessing, results is a list of model output ndarrays
    def postprocess(self, results):
        with ScopedTiming("decoder postprocess", self.debug_mode > 0):  # 计时后处理过程 / Time the postprocessing process
            return results[0]  # 返回解码器输出 / Return decoder output

# 自定义HifiGan声码器类，继承自AIBase基类 / Custom HifiGan vocoder class, inherits from AIBase base class
class HifiGanApp(AIBase):
    def __init__(self, kmodel_path, debug_mode=0):
        super().__init__(kmodel_path)  # 调用基类的构造函数 / Call the base class constructor
        self.kmodel_path = kmodel_path  # 模型文件路径 / Path to the model file
        self.debug_mode = debug_mode    # 是否开启调试模式 / Whether to enable debug mode
        self.mel_data = []              # 存储生成的音频数据 / Store generated audio data
        self.subvector_num = 0          # 子向量数量 / Number of sub-vectors
        self.hifi_input = None          # 声码器输入数据 / Vocoder input data

    # 自定义声码器预处理 / Custom vocoder preprocessing
    def preprocess(self, dec_output_np, durition_sum):
        with ScopedTiming("hifigan preprocess", self.debug_mode > 0):  # 计时预处理过程 / Time the preprocessing process
            self.subvector_num = durition_sum // 100  # 计算子向量数量 / Calculate the number of sub-vectors
            remaining = durition_sum % 100
            if remaining > 0:
                self.subvector_num += 1  # 如果有余数，子向量数加1 / If there is a remainder, increment subvector count
            # 初始化声码器输入 / Initialize vocoder input
            self.hifi_input = np.zeros((1, 80, self.subvector_num * 100), dtype=np.float)
            for i in range(durition_sum):
                self.hifi_input[:, :, i] = dec_output_np[:, :, i]  # 填充解码器输出数据 / Fill with decoder output data

    def run(self, dec_output_np, durition_sum):
        self.preprocess(dec_output_np, durition_sum)  # 执行预处理 / Perform preprocessing
        # 依次对每一个子向量进行声码器推理 / Perform vocoder inference for each sub-vector sequentially
        for i in range(self.subvector_num):
            hifi_input_tmp = np.zeros((1, 80, 100), dtype=np.float)  # 初始化临时输入 / Initialize temporary input
            for j in range(80):
                for k in range(i * 100, (i + 1) * 100):
                    hifi_input_tmp[0][j][k - i * 100] = self.hifi_input[0][j][k]  # 提取子向量 / Extract sub-vector
            # 设置模型输入 / Set model input
            hifigan_input_tensor = nn.from_numpy(hifi_input_tmp)
            # 推理 / Inference
            results = self.inference([hifigan_input_tensor])
            self.postprocess(results)  # 后处理 / Postprocessing
        return self.mel_data  # 返回生成的音频数据 / Return generated audio data

    # 自定义声码器后处理 / Custom vocoder postprocessing
    def postprocess(self, results):
        with ScopedTiming("hifigan postprocess", self.debug_mode > 0):  # 计时后处理过程 / Time the postprocessing process
            # 汇总输出数据 / Aggregate output data
            self.mel_data += results[0][0][0].tolist()

# 自定义中文TTS任务类 / Custom Chinese TTS task class
class TTSZH:
    def __init__(self, encoder_kmodel_path, decoder_kmodel_path, hifigan_kmodel_path, dict_path, phase_path, mapfile, save_wav_file, debug_mode):
        self.save_wav_file = save_wav_file  # 生成音频保存路径 / Path to save generated audio
        self.debug_mode = debug_mode        # 是否开启调试模式 / Whether to enable debug mode
        # 初始化编码器、解码器和声码器 / Initialize encoder, decoder, and vocoder
        self.encoder = EncoderApp(encoder_kmodel_path, dict_path, phase_path, mapfile, debug_mode)
        self.decoder = DecoderApp(decoder_kmodel_path, debug_mode)
        self.hifigan = HifiGanApp(hifigan_kmodel_path, debug_mode)

    def run(self, text):
        # 执行编码器推理 / Perform encoder inference
        encoder_output_0, encoder_output_1 = self.encoder.run(text)
        # 执行解码器推理 / Perform decoder inference
        decoder_output_0 = self.decoder.run(encoder_output_0)
        # 执行声码器推理 / Perform vocoder inference
        hifigan_output = self.hifigan.run(decoder_output_0, encoder_output_1)
        # 将生成的音频数据保存为WAV文件 / Save generated audio data as a WAV file
        save_data = hifigan_output[:encoder_output_1 * 256]
        save_len = len(save_data)
        aidemo.save_wav(save_data, save_len, self.save_wav_file, 24000)
        self.play_audio()  # 播放音频 / Play audio

    def play_audio(self):
        with ScopedTiming("play audio", self.debug_mode > 0):  # 计时播放过程 / Time the playback process
            # 有关音频流的宏变量 / Macro variables related to audio stream
            SAMPLE_RATE = 24000         # 采样率 24000Hz，即每秒采样24000次 / Sample rate 24000Hz, i.e., 24000 samples per second
            CHANNELS = 1                # 通道数，1为单声道 / Number of channels, 1 for mono
            FORMAT = paInt16            # 音频输入输出格式 / Audio input/output format
            CHUNK = int(0.3 * 24000)    # 每次读取音频数据的帧数，设置为0.3秒的帧数 / Number of frames to read each time, set to 0.3 seconds of frames
            # 初始化音频流 / Initialize audio stream
            p = PyAudio()
            p.initialize(CHUNK)
            ret = MediaManager.init()
            if ret:
                print("record_audio, buffer_init failed")
            # 用于播放音频 / For playing audio
            output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, output=True, frames_per_buffer=CHUNK)
            wf = wave.open(self.save_wav_file, "rb")  # 打开WAV文件 / Open WAV file
            wav_data = wf.read_frames(CHUNK)          # 读取音频数据 / Read audio data
            while wav_data:
                output_stream.write(wav_data)         # 写入音频流播放 / Write to audio stream for playback
                wav_data = wf.read_frames(CHUNK)      # 继续读取下一段数据 / Continue reading the next segment of data
            time.sleep(2)  # 时间缓冲，用于播放声音 / Time buffer for playing sound
            wf.close()
            output_stream.stop_stream()
            output_stream.close()
            p.terminate()
            MediaManager.deinit()

    def deinit(self):
        # 释放资源 / Release resources
        aidemo.tts_zh_destroy(self.encoder.ttszh)
        self.encoder.deinit()
        self.decoder.deinit()
        self.hifigan.deinit()

if __name__ == "__main__":
    spk = YbSpeaker()
    spk.enable()
    
    os.exitpoint(os.EXITPOINT_ENABLE)  # 设置退出点 / Set exit point
    nn.shrink_memory_pool()            # 缩小内存池 / Shrink memory pool
    # 设置模型路径和其他参数 / Set model paths and other parameters
    encoder_kmodel_path = "/sdcard/kmodel/zh_fastspeech_1_f32.kmodel"  # 中文TTS编码器模型 / Chinese TTS encoder model
    decoder_kmodel_path = "/sdcard/kmodel/zh_fastspeech_2.kmodel"      # 中文TTS解码器模型 / Chinese TTS decoder model
    hifigan_kmodel_path = "/sdcard/kmodel/hifigan.kmodel"              # 中文TTS声码器模型 / Chinese TTS vocoder model
    dict_path = "/sdcard/utils/pinyin.txt"                             # 拼音字典 / Pinyin dictionary
    phase_path = "/sdcard/utils/small_pinyin.txt"                      # 汉字转拼音字典文件 / Chinese character to pinyin dictionary file
    mapfile = "/sdcard/utils/phone_map.txt"                            # 拼音转音素映射文件 / Pinyin to phoneme mapping file
    text = "你好亚博智能科技，我是机器人小亚"                             # 输入中文语句 / Input Chinese sentence
    save_wav_file = "/sdcard/test.wav"                                 # 生成音频存储路径 / Generated audio storage path

    # 初始化自定义中文TTS实例 / Initialize custom Chinese TTS instance
    tts_zh = TTSZH(encoder_kmodel_path, decoder_kmodel_path, hifigan_kmodel_path, dict_path, phase_path, mapfile, save_wav_file, debug_mode=0)
    try:
        with ScopedTiming("total", 1):  # 计时整个过程 / Time the entire process
            tts_zh.run(text)            # 运行TTS任务 / Run TTS task
            gc.collect()                # 垃圾回收 / Garbage collection
    except Exception as e:
        sys.print_exception(e)          # 打印异常信息 / Print exception information
    finally:
        tts_zh.deinit()                 # 释放资源 / Release resources
    spk.disable()