# 音频输入输出示例 Audio input and output example
#
# 注意：运行此示例需要SD卡 Note: You need an SD card to run this example
#
# 可以播放wav文件 You can play wav files

import os
from media.media import *
from media.pyaudio import *
import media.wave as wave
from ybUtils.YbSpeaker import YbSpeaker

# 初始化扬声器 Initialize speaker
spk = YbSpeaker()

def exit_check():
    """
    检查是否需要退出程序
    Check if program needs to exit
    """
    try:
        os.exitpoint()
    except KeyboardInterrupt as e:
        print("用户停止 User stop: ", e)
        return True
    return False


def play_audio(filename):
    """
    播放音频文件
    Play audio file
    
    Args:
        filename: 音频文件路径 Audio file path
    """
    try:
        spk.enable()  # 启用扬声器 Enable speaker
        wf = wave.open(filename, 'rb')  # 打开wav文件 Open wav file
        
        # 设置音频chunk值 - 每秒采样率的1/25
        # Set audio chunk size - 1/25 of sampling rate per second
        CHUNK = int(wf.get_framerate()/25)

        p = PyAudio()
        p.initialize(CHUNK)  # 初始化PyAudio对象 Initialize PyAudio object
        MediaManager.init()  # 初始化vb buffer Initialize vb buffer

        # 创建音频输出流 Create audio output stream
        # 设置的音频参数均为wave中获取到的参数 Audio parameters are obtained from wave file
        stream = p.open(format=p.get_format_from_width(wf.get_sampwidth()),  # 采样格式 Sample format
                    channels=wf.get_channels(),  # 声道数 Number of channels
                    rate=wf.get_framerate(),  # 采样率 Sample rate
                    output=True,  # 输出模式 Output mode
                    frames_per_buffer=CHUNK)  # 缓冲区大小 Buffer size

        # 设置音频输出流的音量(75%) Set volume of audio output stream (75%)
        stream.volume(vol=75)

        # 从wav文件中读取第一帧数据 Read first frame from wav file
        data = wf.read_frames(CHUNK)

        # 循环读取并播放音频数据 Loop to read and play audio data
        while data:
            stream.write(data)  # 将帧数据写入音频输出流 Write frame data to audio output stream
            data = wf.read_frames(CHUNK)  # 读取下一帧数据 Read next frame
            if exit_check():
                break
                
    except BaseException as e:
            print(f"异常 Exception: {e}")
    finally:
        # 清理资源 Clean up resources
        stream.stop_stream()  # 停止音频输出流 Stop audio output stream
        stream.close()  # 关闭音频输出流 Close audio output stream
        p.terminate()  # 释放音频对象 Release audio object
        wf.close()  # 关闭wav文件 Close wav file
        spk.disable()  # 禁用扬声器 Disable speaker

        MediaManager.deinit()  # 释放vb buffer Release vb buffer


if __name__ == "__main__":
    # 启用退出点 Enable exit point
    os.exitpoint(os.EXITPOINT_ENABLE)
    
    print("开始音频播放 Audio play start")
    # 播放指定wav文件 Play specified wav file
    play_audio('/data/audio/audio.wav')

    print("音频播放完成 Audio play done")