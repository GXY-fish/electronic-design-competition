from media.mp4format import *
import os
import time

class MP4Recorder:
    """
    MP4视频录制类 
    MP4 video recorder class
    """
    def __init__(self, width=640, height=480, max_record_time=10):
        """
        初始化MP4录制器 Initialize MP4 recorder
        
        Args:
            width: 视频宽度 Video width
            height: 视频高度 Video height
            max_record_time: 最大录制时间(秒) Maximum recording time in seconds
        """
        self.width = width  # 视频宽度 Video width
        self.height = height  # 视频高度 Video height
        self.max_record_time = max_record_time  # 最大录制时间 Maximum recording time
        self.mp4_muxer = None  # MP4封装器 MP4 muxer
        self.frame_count = 0  # 已处理帧计数 Processed frame counter
        
    def start_recording(self, file_path):
        """
        开始录制视频 Start video recording
        
        Args:
            file_path: MP4文件保存路径 MP4 file save path
        """
        print("开始MP4录制... Starting MP4 recording...")
        
        # 初始化MP4 muxer Initialize MP4 muxer
        self.mp4_muxer = Mp4Container()
        # 创建MP4配置对象 Create MP4 configuration object
        mp4_cfg = Mp4CfgStr(self.mp4_muxer.MP4_CONFIG_TYPE_MUXER)
        
        # 配置MP4封装参数 Configure MP4 muxer parameters
        if mp4_cfg.type == self.mp4_muxer.MP4_CONFIG_TYPE_MUXER:
            mp4_cfg.SetMuxerCfg(
                file_path,  # 文件路径 File path
                self.mp4_muxer.MP4_CODEC_ID_H265,  # 视频编码格式 Video codec
                self.width,  # 视频宽度 Video width
                self.height,  # 视频高度 Video height
                self.mp4_muxer.MP4_CODEC_ID_G711U  # 音频编码格式 Audio codec
            )
            
        # 创建并启动muxer Create and start muxer
        self.mp4_muxer.Create(mp4_cfg)
        self.mp4_muxer.Start()
        
        # 记录开始时间 Record start time
        start_time_ms = time.ticks_ms()
        
        try:
            while True:
                os.exitpoint()
                
                # 处理音视频数据 Process audio and video data
                self.mp4_muxer.Process()
                
                # 更新帧计数 Update frame counter
                self.frame_count += 1
                print(f"已处理帧数 Processed frames: {self.frame_count}")
                
                # 检查是否超过最大录制时间 Check if exceeded maximum recording time
                elapsed_time = time.ticks_ms() - start_time_ms
                if elapsed_time >= self.max_record_time * 1000:
                    print("录制已达到最大时长,正在保存... Maximum recording time reached, saving...")
                    break
                    
        except BaseException as e:
            print(f"录制过程出错 Recording error: {e}")
            
        finally:
            self.stop_recording()
            
    def stop_recording(self):
        """
        停止录制并清理资源
        Stop recording and clean up resources
        """
        if self.mp4_muxer:
            self.mp4_muxer.Stop()  # 停止录制 Stop recording
            self.mp4_muxer.Destroy()  # 释放资源 Release resources
            print("MP4录制完成,文件已保存! MP4 recording completed, file saved!")
            self.mp4_muxer = None
            
    def __del__(self):
        """
        析构函数确保资源被释放
        Destructor ensures resources are released
        """
        self.stop_recording()

def ensure_dir(directory):
    """
    递归创建目录，适用于MicroPython环境
    """
    # 如果目录为空字符串或根目录，直接返回
    if not directory or directory == '/':
        return
    
    # 处理路径分隔符，确保使用标准格式
    directory = directory.rstrip('/')
    
    try:
        # 尝试获取目录状态，如果目录存在就直接返回
        print(os.stat(directory))
        print(f'目录已存在: {directory}')
        return
    except OSError:
        # 目录不存在，需要创建
        # 分割路径以获取父目录
        if '/' in directory:
            parent = directory[:directory.rindex('/')]
            if parent and parent != directory:  # 避免无限递归
                ensure_dir(parent)
        
        try:
            os.mkdir(directory)
            print(f'已创建目录: {directory}')
        except OSError as e:
            # 可能是并发创建导致的冲突，再次检查目录是否存在
            try:
                os.stat(directory)
                print(f'目录已被其他进程创建: {directory}')
            except:
                # 如果仍然不存在，则确实出错了
                print(f'创建目录时出错: {e}')
    except Exception as e:
        print(f'处理目录时出错: {e}')
        
def main():
    """
    主函数 - 使用示例
    Main function - Usage example
    """
    # 启用退出点 Enable exit point
    os.exitpoint(os.EXITPOINT_ENABLE)
    
    # 创建录制器实例 Create recorder instance
    recorder = MP4Recorder(
        width=640,  # 视频宽度 Video width
        height=480,  # 视频高度 Video height
        max_record_time=10  # 录制时间(秒) Maximum recording time in seconds
    )
    
    ensure_dir("/data/video/")  # 确保目录存在 Ensure directory exists
    
    # 开始录制 Start recording
    recorder.start_recording("/data/video/test.mp4")

if __name__ == "__main__":
    main()