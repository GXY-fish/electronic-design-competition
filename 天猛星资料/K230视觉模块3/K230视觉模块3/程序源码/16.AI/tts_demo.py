# Voice Synthesis Demo - DashScope TTS API
import uos
import time
import gc
import ujson as json
from media.display import *
from media.media import *
from media.pyaudio import *
import media.wave as wave
from ybUtils.YbSpeaker import YbSpeaker

import YbRequests as requests

spk_global = YbSpeaker()

API_KEY = ""
WIFI_SSID = ""
WIFI_KEY = ""

DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

network_connected = False

UI_COLORS = {
    'background': (248, 248, 248),
    'card_bg': (255, 255, 255),
    'primary': (0, 122, 255),
    'text_primary': (28, 28, 30),
    'text_secondary': (99, 99, 102),
    'success': (52, 199, 89),
    'error': (255, 59, 48),
    'warning': (255, 149, 0),
    'separator': (229, 229, 234),
    'playing': (255, 45, 85),
}


TEXT = "你好，我叫小亚，是亚博智能研发的K230视觉模块"

DEFAULT_VOICE = "Cherry"

class TTSState:
    def __init__(self):
        self.program_state = "idle"
        self.status_message = "正在初始化..."
        self.audio_file_path = "/data/tts_output.wav"
        self.loading_frame = 0

state = TTSState()

def connect_wifi():
    global network_connected
    
    print("正在连接WiFi...")
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        if not wlan.isconnected():
            wlan.connect(WIFI_SSID, WIFI_KEY)
            
            timeout = 10
            while not wlan.isconnected() and timeout > 0:
                time.sleep(1)
                timeout -= 1
                print(f"连接中... 剩余时间: {timeout}s")
            
            if wlan.isconnected():
                print(f"WiFi连接成功! IP: {wlan.ifconfig()[0]}")
                network_connected = True
                return True
            else:
                print("WiFi连接超时")
                return False
        else:
            print("WiFi已连接")
            network_connected = True
            return True
            
    except Exception as e:
        print(f"WiFi连接失败: {e}")
        return False

def draw_rounded_rect(img, x, y, width, height, color, corner_radius=12, fill=True):
    if fill:
        img.draw_rectangle(x + corner_radius, y, width - 2 * corner_radius, height, color, fill=True)
        img.draw_rectangle(x, y + corner_radius, width, height - 2 * corner_radius, color, fill=True)
        
        img.draw_circle(x + corner_radius, y + corner_radius, corner_radius, color, fill=True)
        img.draw_circle(x + width - corner_radius, y + corner_radius, corner_radius, color, fill=True)
        img.draw_circle(x + corner_radius, y + height - corner_radius, corner_radius, color, fill=True)
        img.draw_circle(x + width - corner_radius, y + height - corner_radius, corner_radius, color, fill=True)

def draw_audio_wave_animation(img, x, y, frame):
    import math
    
    wave_width = 200
    wave_height = 40
    center_y = y + wave_height // 2
    
    draw_rounded_rect(img, x, y, wave_width, wave_height, UI_COLORS['separator'], corner_radius=8, fill=True)
    
    bar_count = 20
    bar_width = 6
    bar_spacing = (wave_width - bar_count * bar_width) // (bar_count - 1)
    
    for i in range(bar_count):
        bar_x = x + 10 + i * (bar_width + bar_spacing)
        
        wave_offset = (frame * 0.3) + (i * 0.5)
        bar_height = int(15 + 10 * abs(math.sin(wave_offset)))
        bar_y = center_y - bar_height // 2
        
        if bar_height > 20:
            bar_color = UI_COLORS['playing']
        elif bar_height > 15:
            bar_color = UI_COLORS['warning']
        else:
            bar_color = UI_COLORS['primary']
        
        img.draw_rectangle(bar_x, bar_y, bar_width, bar_height, bar_color, fill=True)

def draw_speaker_icon(img, x, y, frame):
    import math
    
    speaker_color = UI_COLORS['primary']
    img.draw_rectangle(x, y + 10, 15, 20, speaker_color, fill=True)
    img.draw_rectangle(x + 15, y + 5, 10, 30, speaker_color, fill=True)
    
    for i in range(3):
        wave_radius = 15 + i * 8
        alpha_factor = 1.0 - (i * 0.3)
        wave_alpha = int(255 * alpha_factor * (0.5 + 0.5 * abs(math.sin(frame * 0.2 + i * 0.5))))
        
        wave_x = x + 25
        wave_y = y + 20
        
        for angle in range(-30, 31, 10):
            rad = math.radians(angle)
            point_x = wave_x + int(wave_radius * math.cos(rad))
            point_y = wave_y + int(wave_radius * math.sin(rad))
            
            if 0 <= point_x < DISPLAY_WIDTH and 0 <= point_y < DISPLAY_HEIGHT:
                img.draw_circle(point_x, point_y, 2, speaker_color, fill=True)

def draw_loading_spinner(img, x, y, frame):
    import math
    
    center_x, center_y = x + 20, y + 20
    radius = 15
    dot_count = 8
    
    for i in range(dot_count):
        angle = (i * 2 * math.pi / dot_count) + (frame * 0.2)
        dot_x = center_x + int(radius * math.cos(angle))
        dot_y = center_y + int(radius * math.sin(angle))
        
        alpha = int(255 * (i + 1) / dot_count)
        dot_color = (UI_COLORS['primary'][0], UI_COLORS['primary'][1], UI_COLORS['primary'][2])
        
        img.draw_circle(dot_x, dot_y, 3, dot_color, fill=True)

def draw_text_with_wrapping(img, x, y, width, height, text, font_size=16, color=(28, 28, 30)):
    if not text:
        return
    
    line_height = font_size + 6
    max_lines = (height - 20) // line_height
    
    available_width = width - 40
    char_width = font_size * 1.1
    chars_per_line = max(1, int(available_width / char_width))
    
    lines = []
    current_line = ""
    current_width = 0
    
    for char in text:
        if char == '\n':
            lines.append(current_line)
            current_line = ""
            current_width = 0
        else:
            if ord(char) > 127:
                char_pixel_width = font_size * 1.0
            else:
                char_pixel_width = font_size * 0.6
            
            if current_width + char_pixel_width > available_width and current_line:
                lines.append(current_line)
                current_line = char
                current_width = char_pixel_width
            else:
                current_line += char
                current_width += char_pixel_width
    
    if current_line:
        lines.append(current_line)
    
    display_lines = lines[:max_lines]
    
    for i, line in enumerate(display_lines):
        text_y = y + 10 + i * line_height
        if text_y + font_size <= y + height - 10:
            img.draw_string_advanced(x + 20, text_y, font_size, line, color=color)

def draw_main_interface(img, animation_frame=0):
    img.draw_rectangle(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, UI_COLORS['background'], fill=True)
    
    status_bar_height = 44
    img.draw_rectangle(0, 0, DISPLAY_WIDTH, status_bar_height, UI_COLORS['card_bg'], fill=True)
    
    img.draw_string_advanced(20, 14, 20, "语音合成", color=UI_COLORS['text_primary'])
    
    status_color = UI_COLORS['success'] if network_connected else UI_COLORS['error']
    img.draw_circle(DISPLAY_WIDTH - 30, 22, 6, status_color, fill=True)
    
    network_status = "已连接" if network_connected else "未连接"
    img.draw_string_advanced(DISPLAY_WIDTH - 80, 14, 12, network_status, color=status_color)
    
    status_y = status_bar_height + 20
    
    if state.program_state == "error":
        status_bg_color = UI_COLORS['error']
    elif state.program_state == "completed":
        status_bg_color = UI_COLORS['success']
    elif state.program_state == "playing":
        status_bg_color = UI_COLORS['playing']
    elif state.program_state in ["connecting", "synthesizing"]:
        status_bg_color = UI_COLORS['warning']
    else:
        status_bg_color = UI_COLORS['separator']
    
    draw_rounded_rect(img, 20, status_y, DISPLAY_WIDTH - 40, 40, 
                     status_bg_color, corner_radius=8, fill=True)
    
    if state.program_state in ["error", "completed", "playing", "connecting", "synthesizing"]:
        text_color = UI_COLORS['card_bg']
    else:
        text_color = UI_COLORS['text_secondary']
    
    img.draw_string_advanced(40, status_y + 12, 16, state.status_message, color=text_color)
    
    content_info_y = status_y + 60
    content_info_height = DISPLAY_HEIGHT - content_info_y - 40
    
    draw_rounded_rect(img, 20, content_info_y, DISPLAY_WIDTH - 40, content_info_height, 
                     UI_COLORS['card_bg'], corner_radius=12, fill=True)
    
    img.draw_string_advanced(40, content_info_y + 20, 18, "语音合成内容:", color=UI_COLORS['text_secondary'])
    
    speaker_x = 200
    speaker_y = content_info_y + 15
    if state.program_state == "playing":
        draw_speaker_icon(img, speaker_x, speaker_y, animation_frame)
    
    text_area_y = content_info_y + 60
    text_area_height = content_info_height - 80
    
    display_text = TEXT
    if state.program_state == "playing":
        display_text = TEXT
    
    draw_text_with_wrapping(img, 40, text_area_y, DISPLAY_WIDTH - 80, text_area_height, 
                          display_text, font_size=18, color=UI_COLORS['text_primary'])

def synthesize_speech(text, voice="Cherry"):
    if not network_connected:
        return False, "网络未连接"
    
    try:
        print(f"开始语音合成: {text[:50]}...")
        
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
            print(f"API响应状态码: {response.status_code}")
            print(f"响应内容长度: {len(response.content) if hasattr(response, 'content') else 'N/A'}")
            print(f"响应内容: {response.content[:500] if hasattr(response, 'content') else 'N/A'}...")
            
            try:
                if hasattr(response, 'json') and callable(response.json):
                    result = response.json()
                elif hasattr(response, 'json'):
                    result = response.json
                else:
                    import ujson
                    result = ujson.loads(response.content.decode('utf-8'))
                
                print(f"解析后的JSON结果: {result}")
                 
                if (result and 'output' in result and 
                    'audio' in result['output'] and 
                    'url' in result['output']['audio']):
                    
                    audio_url = result['output']['audio']['url']
                    print(f"获取音频URL成功: {audio_url}")
                    
                    print("下载音频文件...")
                    audio_response = requests.get(audio_url, timeout=30)
                    
                    if audio_response.status_code == 200:
                        with open(state.audio_file_path, 'wb') as f:
                            f.write(audio_response.content)
                        
                        print(f"音频文件保存成功: {state.audio_file_path}")
                        return True, "语音合成成功"
                    else:
                        return False, f"音频下载失败: {audio_response.status_code}"
                else:
                    return False, f"API响应格式错误，未找到音频URL: {result}"
                    
            except Exception as json_error:
                print(f"JSON解析错误: {json_error}")
                return False, f"JSON解析失败: {json_error}"
        else:
            return False, f"API请求失败: {response.status_code}"
            
    except Exception as e:
        error_msg = str(e)
        print(f"语音合成异常: {error_msg}")
        return False, f"语音合成失败: {error_msg}"

def play_audio():
    try:
        with open(state.audio_file_path, 'rb') as f:
            pass
    except OSError:
        return False, "音频文件不存在"
    
    print(f"开始播放音频: {state.audio_file_path}")
    
    try:
        spk_global.enable()
        wf = wave.open(state.audio_file_path, 'rb')
        
        CHUNK = int(wf.get_framerate()/25)

        p = PyAudio()
        p.initialize(CHUNK)
        MediaManager.init()

        stream = p.open(format=p.get_format_from_width(wf.get_sampwidth()),
                    channels=wf.get_channels(),
                    rate=wf.get_framerate(),
                    output=True,
                    frames_per_buffer=CHUNK)

        stream.volume(vol=75)

        data = wf.read_frames(CHUNK)

        while data:
            stream.write(data)
            data = wf.read_frames(CHUNK)
                
    except BaseException as e:
        print(f"异常 Exception: {e}")
        return False, f"播放失败: {e}"
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()
        spk_global.disable()

        MediaManager.deinit()
        
    print("音频播放完成")
    return True, "播放完成"

def main():
    global state
    
    Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    MediaManager.init()
    
    img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.ARGB8888)
    
    print("=== 亚博智能K230语音合成系统 ===")
    print(f"合成文本: {TEXT}")
    
    animation_frame = 0
    
    try:
        state.program_state = "connecting"
        state.status_message = "正在连接网络..."
        draw_main_interface(img, animation_frame)
        Display.show_image(img)
        
        print("步骤1: 连接WiFi...")
        if not connect_wifi():
            state.program_state = "error"
            state.status_message = "网络连接失败，程序结束"
            draw_main_interface(img, animation_frame)
            Display.show_image(img)
            print("网络连接失败，程序结束")
            time.sleep(5)
            return
        
        state.program_state = "connecting"
        state.status_message = "网络连接成功！"
        draw_main_interface(img, animation_frame)
        Display.show_image(img)
        time.sleep(0.5)
        
        state.program_state = "synthesizing"
        state.status_message = "开始语音合成..."
        state.loading_frame = 0
        
        draw_main_interface(img, animation_frame)
        Display.show_image(img)
        
        print("步骤2: 语音合成...")
        for i in range(20):
            uos.exitpoint()
            animation_frame = (animation_frame + 1) % 100
            draw_main_interface(img, animation_frame)
            Display.show_image(img)
            time.sleep(0.1)
        TEXT
        success, message = synthesize_speech(TEXT, DEFAULT_VOICE)
        
        if not success:
            state.program_state = "error"
            state.status_message = f"语音合成失败: {message}"
            draw_main_interface(img, animation_frame)
            Display.show_image(img)
            print(f"语音合成失败: {message}")
            time.sleep(5)
            return
        
        state.program_state = "synthesizing"
        state.status_message = "语音合成完成，准备播放..."
        draw_main_interface(img, animation_frame)
        Display.show_image(img)
        time.sleep(0.5)
        
        state.program_state = "playing"
        state.status_message = "正在通过扬声器播放"
        
        draw_main_interface(img, animation_frame)
        Display.show_image(img)
        
        print("步骤3: 播放音频...")
        MediaManager.deinit()
        
        success, message = play_audio()
        
        if not success:
            MediaManager.init()
            state.program_state = "error"
            state.status_message = f"音频播放失败: {message}"
            draw_main_interface(img, animation_frame)
            Display.show_image(img)
            print(f"音频播放失败: {message}")
            time.sleep(5)
            return
        
        MediaManager.init()
        state.program_state = "completed"
        
        print("所有步骤完成！程序将在10秒后结束...")
        
        for i in range(100):
            uos.exitpoint()
            animation_frame = (animation_frame + 1) % 100
            draw_main_interface(img, animation_frame)
            Display.show_image(img)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("程序被用户中断")
    except Exception as e:
        state.program_state = "error"
        state.status_message = f"程序异常: {str(e)}"
        try:
            MediaManager.init()
            draw_simple_interface(img)
            Display.show_image(img)
        except:
            pass
        time.sleep(5)
    finally:
        print("程序结束")
        try:
            MediaManager.deinit()
        except:
            pass

if __name__ == "__main__":
    main()