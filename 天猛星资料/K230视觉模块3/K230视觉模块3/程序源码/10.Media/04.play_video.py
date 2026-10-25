# play mp4 file example
# MP4文件播放示例
#
# Note: You will need an SD card to run this example.
# 注意：运行此示例需要SD卡。
#
# You can load local files to play. The current version only supports MP4 format, video supports 264/265, and audio supports g711a/g711u.
# 你可以加载本地文件进行播放。当前版本仅支持MP4格式，视频支持264/265编码，音频支持g711a/g711u编码。

from media.player import * # 导入播放器模块，用于播放mp4文件
                           # Import player module for playing mp4 files
from media.display import * # 导入显示模块，用于设置显示输出
                            # Import display module for setting up display output
import os # 导入操作系统模块，提供与操作系统交互的功能
          # Import os module for OS interactions
# from ybUtils.YbSpeaker import YbSpeaker # 导入YbSpeaker模块（已注释）
                                         # Import YbSpeaker module (commented out)

# # 初始化扬声器 Initialize speaker
# spk = YbSpeaker() # 创建扬声器对象实例
                   # Create speaker object instance
# spk.enable()  # 启用扬声器 Enable speaker

start_play = False # 播放状态标志，用于跟踪视频是否正在播放
                   # Playback status flag, used to track whether video is playing

def player_event(event, data):
    """
    播放器事件回调函数，用于处理播放器事件
    Player event callback function for handling player events
    """
    global start_play # 声明使用全局变量start_play
                      # Declare use of global variable start_play
    if(event == K_PLAYER_EVENT_EOF): # 检测到播放结束事件（End Of File）
                                     # Detected end of file event
        start_play = False # 设置播放结束标识
                           # Set playback ended flag

def play_mp4_test(filename):
    """
    播放MP4文件的测试函数
    Function for testing MP4 playback
    
    参数:
    filename: MP4文件路径
    
    Parameters:
    filename: Path to MP4 file
    """
    global start_play # 声明使用全局变量start_play
                      # Declare use of global variable start_play
    
#    player=Player(Display.VIRT) # 使用IDE作为输出显示，可以设定任意分辨率
                                # Use IDE as output display, can set any resolution
    player=Player(Display.ST7701) # 使用ST7701 LCD屏作为输出显示，最大分辨率640*480
                                  # Use ST7701 LCD screen as output display, max resolution 640*480
    print("display") # 打印调试信息，表示显示已初始化
                     # Print debug info indicating display initialized
    
    player.load(filename) # 加载mp4文件
                          # Load mp4 file
    print("load") # 打印调试信息，表示文件已加载
                  # Print debug info indicating file loaded
    
    player.set_event_callback(player_event) # 设置播放器事件回调函数
                                            # Set player event callback function
    print("start") # 打印调试信息，表示准备开始播放
                   # Print debug info indicating ready to start playback
    
    player.start() # 开始播放视频
                   # Start video playback
    start_play = True # 设置播放状态为开始播放
                      # Set playback status to started
    print("play") # 打印调试信息，表示播放已开始
                  # Print debug info indicating playback started
    
    # 等待播放结束
    # Wait for playback to finish
    try:
        while(start_play): # 当播放状态为True时循环等待
                           # Loop waiting while playback status is True
            time.sleep(0.1) # 休眠0.1秒，减少CPU占用
                            # Sleep for 0.1 seconds to reduce CPU usage
            os.exitpoint() # 处理退出点，允许程序正常退出
                           # Process exit point, allows program to exit normally
    except KeyboardInterrupt as e: # 捕获键盘中断异常（用户按Ctrl+C）
                                   # Catch keyboard interrupt exception (user pressed Ctrl+C)
        print("user stop: ", e) # 打印用户停止信息
                                # Print user stop information
    except BaseException as e: # 捕获所有其他异常
                               # Catch all other exceptions
        import sys # 导入sys模块用于异常处理
                   # Import sys module for exception handling
        sys.print_exception(e) # 打印详细异常信息
                               # Print detailed exception information

    player.stop() # 停止播放视频
                  # Stop video playback
    print("play over") # 打印调试信息，表示播放已结束
                       # Print debug info indicating playback ended

if __name__ == "__main__": # 当作为主程序运行时执行以下代码
                           # Execute following code when run as main program
    os.exitpoint(os.EXITPOINT_ENABLE) # 启用退出点，允许程序正常退出
                                      # Enable exit points, allows program to exit normally
    play_mp4_test("/data/video/test.mp4") # 播放指定路径的mp4文件
                                          # Play mp4 file at specified path
    # spk.disable() # 禁用扬声器（已注释）
                   # Disable speaker (commented out)