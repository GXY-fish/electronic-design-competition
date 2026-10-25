# K230音频对话+语音合成整合程序
# Audio Chat + TTS Integration for K230
import uos
import time
import gc
import ujson as json
from media.display import *
from media.media import *
from media.pyaudio import *
import media.wave as wave
from ybUtils.YbSpeaker import YbSpeaker
from ybUtils.YbKey import YbKey

# 导入网络请求模块
import YbRequests as requests
import libs.upload_image as upload_image

# 全局扬声器对象
spk_global = YbSpeaker()

# 全局初始化标志
media_manager_initialized = False

API_KEY = ""  # 请替换为您的API密钥
WIFI_SSID = ""
WIFI_KEY = ""

# 音频文件路径
TTS_OUTPUT_FILE = "/data/tts_output.wav"
RECORDED_AUDIO_FILE = f"/data/recorded_audio_{time.ticks_ms()}.wav"

def upload_audio_to_oss(audio_path, max_retries=5):
    """使用稳定的upload_image库上传音频到OSS，支持重试机制"""
    print("开始上传音频到OSS...")
    
    # 上传前进行垃圾回收
    gc.collect()
    
    for attempt in range(1, max_retries + 1):
        try:
            # 显示上传进度
            progress = attempt * 20  # 20%, 40%, 60%, 80%, 100%
            print(f"上传中({progress}%)")
            
            # 使用upload_image库的上传方法，这个库更稳定
            oss_url = upload_image.upload_image_to_dashscope(API_KEY, audio_path, "qwen-audio-turbo")
            
            # 上传成功时显示100%
            print("上传中(100%)")
            print(f"音频上传成功! OSS地址: {oss_url}")
            
            # 上传成功后进行垃圾回收
            gc.collect()
            return oss_url
        except Exception as e:
            # 隐藏具体的错误信息，失败后也进行垃圾回收
            gc.collect()
            if attempt < max_retries:
                # 递增等待时间：1秒、2秒、3秒、4秒
                wait_time = 0.1
                time.sleep(wait_time)
            else:
                print("上传失败，请检查网络连接")
                raise e

def record_with_button_and_upload(filename, key, left_volume=85, right_volume=85):
    """按键录音并上传，返回OSS链接"""
    global media_manager_initialized
    
    print("按下按键开始录音，松开按键停止录音...")

    # 等待按键按下
    while not key.is_pressed():
        time.sleep_ms(10)

    # 录音参数
    FORMAT = paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = RATE // 25
    frames = []

    # 初始化音频
    p = PyAudio()
    p.initialize(CHUNK)
    
    # 只在第一次初始化MediaManager
    if not media_manager_initialized:
        MediaManager.init()
        media_manager_initialized = True
        print("MediaManager 初始化完成")
    else:
        print("MediaManager 已初始化，跳过重复初始化")

    # 打开输入流
    input_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    input_stream.volume(LEFT, left_volume)
    input_stream.volume(RIGHT, right_volume)

    print("开始录音...")
    # 录音直到按键松开
    while key.is_pressed():
        try:
            data = input_stream.read(CHUNK)
            frames.append(data)
        except Exception as e:
            print(f"录音帧读取错误: {e}")
            break
        time.sleep_ms(10)

    print("停止录音...")
    try:
        input_stream.stop_stream()
        input_stream.close()
    except:
        pass

    # 录音完成后进行垃圾回收
    gc.collect()

    # 保存到WAV
    try:
        print(f"正在保存录音文件到: {filename}")
        wf = wave.open(filename, 'wb')
        wf.set_channels(CHANNELS)
        wf.set_sampwidth(p.get_sample_size(FORMAT))
        wf.set_framerate(RATE)
        wf.write_frames(b''.join(frames))
        wf.close()
        print("录音文件保存完成")
        
        # 文件保存后进行垃圾回收
        gc.collect()
    except Exception as e:
        print(f"保存录音失败: {e}")
        return None

    # 上传到OSS
    try:
        oss_url = upload_audio_to_oss(filename)
        return oss_url
    except Exception as e:
        print(f"上传录音失败: {e}")
        return None

def connect_wifi():
    """连接WiFi网络"""
    print("正在连接WiFi...")
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        if not wlan.isconnected():
            wlan.connect(WIFI_SSID, WIFI_KEY)
            
            # 等待连接
            timeout = 15
            while not wlan.isconnected() and timeout > 0:
                time.sleep(1)
                timeout -= 1
                print(f"连接中... 剩余时间: {timeout}s")
            
            if wlan.isconnected():
                print(f"WiFi连接成功! IP: {wlan.ifconfig()[0]}")
                return True
            else:
                print("WiFi连接超时")
                return False
        else:
            print("WiFi已连接")
            return True
            
    except Exception as e:
        print(f"WiFi连接失败: {e}")
        return False

def call_audio_api(oss_url):
    """调用音频API获取AI回复"""
    print("开始调用音频API...")
    
    # API调用前进行垃圾回收
    gc.collect()
    
    # API URL
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    
    # 请求头
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-OssResourceResolve": "enable"
    }
    
    # 请求数据
    data = {
        "model": "qwen-audio-turbo-latest",
        "input": {
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {"text": "You are a helpful assistant."}
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"audio": oss_url}
                    ]
                }
            ]
        }
    }
    
    try:
        # 发送POST请求
        print("发送POST请求...")
        response = requests.post(url, headers=headers, json_data=data, timeout=60)
        
        print(f"响应状态码: {response.status_code}, {response.content}")
        
        if response.status_code == 200:
            print("音频API请求成功!")
            
            # 直接使用手动JSON解析，避免response.json的问题
            try:
                # 获取响应文本并手动解析
                response_text = response.text
                if isinstance(response_text, bytes):
                    response_text = response_text.decode('utf-8')
                
                result = json.loads(response_text)
                print(f"JSON解析成功")
                
                # 提取AI回复文本
                if 'output' in result and 'choices' in result['output']:
                    choices = result['output']['choices']
                    if len(choices) > 0 and 'message' in choices[0]:
                        content_list = choices[0]['message']['content']
                        if len(content_list) > 0 and 'text' in content_list[0]:
                            ai_text = content_list[0]['text']
                            print(f"提取到AI回复文本: {ai_text}")
                            # API成功后进行垃圾回收
                            gc.collect()
                            return True, ai_text
                        else:
                            return False, "响应格式错误：缺少text内容"
                    else:
                        return False, "响应格式错误：缺少message内容"
                else:
                    return False, "响应格式错误：缺少output或choices"
                    
            except Exception as json_error:
                print(f"JSON解析错误: {json_error}")
                # 异常时也进行垃圾回收
                gc.collect()
                return False, f"JSON解析失败: {json_error}"
        else:
            print(f"音频API请求失败，状态码: {response.status_code}")
            # 失败时也进行垃圾回收
            gc.collect()
            return False, f"API请求失败: {response.status_code}"
            
    except Exception as e:
        print(f"音频API请求异常: {e}")
        # 异常时也进行垃圾回收
        gc.collect()
        return False, f"请求异常: {e}"

def synthesize_speech(text, voice="Cherry"):
    """调用DashScope TTS API进行语音合成"""
    print(f"开始语音合成: {text[:50]}...")
    
    try:
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "qwen3-tts-flash",
            "input": {
                "text": text,
                "voice": voice,
                "language_type": "Chinese"
            }
        }
        
        print("发送TTS请求...")
        response = requests.post(url, headers=headers, json_data=data, timeout=60)
        
        if response.status_code == 200:
            print("TTS请求成功!")
            
            try:
                # 手动解析JSON
                response_text = response.text
                if isinstance(response_text, bytes):
                    response_text = response_text.decode('utf-8')
                
                result = json.loads(response_text)
                print("TTS JSON解析成功")
                 
                # 根据官方文档，音频URL在 output.audio.url 路径下
                if (result and 'output' in result and 
                    'audio' in result['output'] and 
                    'url' in result['output']['audio']):
                    
                    audio_url = result['output']['audio']['url']
                    print(f"获取音频URL成功: {audio_url}")
                    
                    # 下载音频文件
                    print("下载音频文件...")
                    audio_response = requests.get(audio_url, timeout=30)
                    
                    if audio_response.status_code == 200:
                        # 保存音频文件
                        with open(TTS_OUTPUT_FILE, 'wb') as f:
                            f.write(audio_response.content)
                        
                        print(f"音频文件保存成功: {TTS_OUTPUT_FILE}")
                        return True, "语音合成成功"
                    else:
                        return False, f"音频下载失败: {audio_response.status_code}"
                else:
                    return False, f"TTS响应格式错误，未找到音频URL: {result}"
                    
            except Exception as json_error:
                print(f"TTS JSON解析错误: {json_error}")
                return False, f"TTS JSON解析失败: {json_error}"
        else:
            return False, f"TTS API请求失败: {response.status_code}"
            
    except Exception as e:
        error_msg = str(e)
        print(f"语音合成异常: {error_msg}")
        return False, f"语音合成失败: {error_msg}"

def play_audio():
    """播放合成的音频"""
    # 检查音频文件是否存在
    try:
        with open(TTS_OUTPUT_FILE, 'rb') as f:
            pass  # 文件存在
    except OSError:
        return False, "音频文件不存在"
    
    print(f"开始播放音频: {TTS_OUTPUT_FILE}")
    
    try:
        spk_global.enable()  # 启用扬声器
        wf = wave.open(TTS_OUTPUT_FILE, 'rb')  # 打开wav文件
        
        # 设置音频chunk值
        CHUNK = int(wf.get_framerate()/25)

        p = PyAudio()
        p.initialize(CHUNK)  # 初始化PyAudio对象
        # MediaManager.init() 已在录音阶段初始化，无需重复调用

        # 创建音频输出流
        stream = p.open(format=p.get_format_from_width(wf.get_sampwidth()),
                    channels=wf.get_channels(),
                    rate=wf.get_framerate(),
                    output=True,
                    frames_per_buffer=CHUNK)

        # 设置音频输出流的音量(75%)
        stream.volume(vol=100)

        # 从wav文件中读取第一帧数据
        data = wf.read_frames(CHUNK)

        # 循环读取并播放音频数据
        while data:
            stream.write(data)
            data = wf.read_frames(CHUNK)
                
    except BaseException as e:
        print(f"播放异常: {e}")
        return False, f"播放失败: {e}"
    finally:
        # 清理资源
        try:
            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()
            spk_global.disable()
            # 注意：不要调用MediaManager.deinit()，因为我们需要在整个程序生命周期中保持初始化状态
        except:
            pass
        
    print("音频播放完成")
    return True, "播放完成"

def main():
    """主函数 - 持续的音频对话+语音合成循环"""
    print("=" * 60)
    print("K230音频对话+语音合成整合程序")
    print("Audio Chat + TTS Integration for K230")
    print("持续对话模式 - 按键录音，松开停止")
    print("=" * 60)
    
    try:
        # 步骤1: 连接WiFi（只需连接一次）
        print("\n步骤1: 连接WiFi...")
        if not connect_wifi():
            print("网络连接失败，程序结束")
            return
        
        print("网络连接成功！")
        time.sleep(1)
        
        # 初始化按键（只需初始化一次）
        key = YbKey()
        
        # 对话计数器
        conversation_count = 0
        
        print("\n=== 进入持续对话模式 ===")
        print("提示：按下按键开始录音，松开按键停止录音并开始AI对话")
        print("程序将持续运行，等待您的每次录音...")
        
        # 持续对话循环
        while True:
            try:
                conversation_count += 1
                print(f"\n{'='*50}")
                print(f"第 {conversation_count} 次对话")
                print(f"{'='*50}")
                
                # 生成新的录音文件名（避免文件冲突）
                current_audio_file = f"/data/recorded_audio_{time.ticks_ms()}.wav"
                
                # 步骤2: 按键录音并上传
                print("\n等待按键录音...")
                oss_url = record_with_button_and_upload(current_audio_file, key)
                if not oss_url:
                    print("录音或上传失败，跳过本次对话，等待下一次...")
                    time.sleep(2)
                    continue

                print(f"录音上传成功: {oss_url}")

                # 步骤3: 调用音频API获取AI回复
                print("\n正在获取AI回复...")
                success, ai_text = call_audio_api(oss_url)
                
                if not success:
                    print(f"音频API调用失败: {ai_text}")
                    print("跳过本次对话，等待下一次...")
                    time.sleep(2)
                    continue
                
                print(f"AI回复: {ai_text}")
                time.sleep(1)
                
                # 步骤4: 语音合成
                print("\n正在合成语音...")
                success, message = synthesize_speech(ai_text)
                
                if not success:
                    print(f"语音合成失败: {message}")
                    print("跳过语音播放，等待下一次对话...")
                    time.sleep(2)
                    continue
                
                print("语音合成完成！")
                time.sleep(1)
                
                # 步骤5: 播放音频
                print("\n正在播放AI回复...")
                success, message = play_audio()
                
                if not success:
                    print(f"音频播放失败: {message}")
                else:
                    print("音频播放完成！")
                
                print(f"\n第 {conversation_count} 次对话完成！")
                print("准备下一次对话...")
                time.sleep(1)
                
                # 清理临时录音文件
                try:
                    uos.remove(current_audio_file)
                except:
                    pass
                    
            except KeyboardInterrupt:
                print("\n\n检测到键盘中断，退出程序...")
                break
            except Exception as e:
                print(f"\n对话过程中出现异常: {e}")
                print("跳过本次对话，等待下一次...")
                
                # 清理可能的临时文件
                try:
                    uos.remove(current_audio_file)
                except:
                    pass
                
                time.sleep(2)
                continue
        
    except Exception as e:
        print(f"程序初始化异常: {e}")
    
    print(f"\n程序结束，共完成 {conversation_count} 次对话")

if __name__ == "__main__":
    main()