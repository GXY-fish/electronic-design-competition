import os
from media.media import *
from media.display import *
from media.pyaudio import *
import media.wave as wave
import time
from ybUtils.YbKey import YbKey
import ujson as json

try:
    import urequests as requests
except ImportError:
    import requests

import libs.upload_image as upload_image

DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

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
    'recording': (255, 45, 85),
}


class AudioRecorderWithUpload:
    def __init__(self, api_key, model_name="paraformer-v2", wifi_ssid="Yahboom", wifi_key="yahboom890729", enable_ui=True):
        self.FORMAT = paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = self.RATE // 25
        self.frames = []
        self.is_recording = False

        self.api_key = api_key
        self.model_name = model_name
        
        self.wifi_ssid = wifi_ssid
        self.wifi_key = wifi_key
        self.network_connected = False

        self.enable_ui = enable_ui
        self.img = None
        self.loading_frame = 0
        self.ui_state = "idle"
        self.status_message = "准备开始录音"
        self.recognition_result = ""

        if self.enable_ui:
            try:
                Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
                self.img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.ARGB8888)
                print("UI显示初始化成功")
            except Exception as e:
                print(f"UI显示初始化失败: {e}")
                self.enable_ui = False

        self.p = PyAudio()
        self.p.initialize(self.CHUNK)
        MediaManager.init()

        if self.enable_ui:
            self.update_ui()

    def draw_rounded_rect(self, img, x, y, width, height, color, corner_radius=12, fill=True):
        if fill:
            img.draw_rectangle(x + corner_radius, y, width - 2 * corner_radius, height, color, fill=True)
            img.draw_rectangle(x, y + corner_radius, width, height - 2 * corner_radius, color, fill=True)
            
            img.draw_circle(x + corner_radius, y + corner_radius, corner_radius, color, fill=True)
            img.draw_circle(x + width - corner_radius, y + corner_radius, corner_radius, color, fill=True)
            img.draw_circle(x + corner_radius, y + height - corner_radius, corner_radius, color, fill=True)
            img.draw_circle(x + width - corner_radius, y + height - corner_radius, corner_radius, color, fill=True)

    def draw_loading_spinner(self, img, x, y, frame):
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

    def draw_recording_indicator(self, img, x, y, frame):
        import math
        
        pulse = int(abs(math.sin(frame * 0.3)) * 10) + 5
        
        img.draw_circle(x + 20, y + 20, 20 + pulse, UI_COLORS['recording'], fill=False, thickness=3)
        img.draw_circle(x + 20, y + 20, 12, UI_COLORS['recording'], fill=True)

    def draw_text_with_wrapping(self, img, x, y, width, height, text, font_size=16, color=(28, 28, 30)):
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

    def update_ui(self):
        if not self.enable_ui or not self.img:
            return
        
        self.img.draw_rectangle(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, UI_COLORS['background'], fill=True)
        
        status_bar_height = 44
        self.img.draw_rectangle(0, 0, DISPLAY_WIDTH, status_bar_height, UI_COLORS['card_bg'], fill=True)
        
        self.img.draw_string_advanced(20, 14, 20, "YAHBOOM | 语音识别", color=UI_COLORS['text_primary'])
        
        status_color = UI_COLORS['success'] if self.network_connected else UI_COLORS['error']
        self.img.draw_circle(DISPLAY_WIDTH - 30, 22, 6, status_color, fill=True)
        
        network_status = "已连接" if self.network_connected else "未连接"
        self.img.draw_string_advanced(DISPLAY_WIDTH - 80, 14, 12, network_status, color=status_color)
        
        record_area_y = status_bar_height + 10
        record_area_height = 120
        
        self.draw_rounded_rect(self.img, 20, record_area_y, DISPLAY_WIDTH - 40, record_area_height, 
                             UI_COLORS['card_bg'], corner_radius=12, fill=True)
        
        if self.ui_state == "recording":
            self.img.draw_string_advanced(40, record_area_y + 15, 16, "正在录音...", color=UI_COLORS['recording'])
            self.draw_recording_indicator(self.img, 40, record_area_y + 40, self.loading_frame)
            self.img.draw_string_advanced(100, record_area_y + 55, 14, "松开按键停止录音", color=UI_COLORS['text_secondary'])
        elif self.ui_state == "uploading":
            self.img.draw_string_advanced(40, record_area_y + 15, 16, "正在上传...", color=UI_COLORS['warning'])
            self.draw_loading_spinner(self.img, 40, record_area_y + 40, self.loading_frame)
        elif self.ui_state == "processing":
            self.img.draw_string_advanced(40, record_area_y + 15, 16, "正在处理...", color=UI_COLORS['primary'])
            self.draw_loading_spinner(self.img, 40, record_area_y + 40, self.loading_frame)
        elif self.ui_state == "completed":
            self.img.draw_string_advanced(40, record_area_y + 15, 16, "处理完成", color=UI_COLORS['success'])
            self.img.draw_circle(60, record_area_y + 55, 15, UI_COLORS['success'], fill=True)
            self.img.draw_string_advanced(40, record_area_y + 80, 14, "✓", color=UI_COLORS['card_bg'])
        elif self.ui_state == "error":
            self.img.draw_string_advanced(40, record_area_y + 15, 16, "处理失败", color=UI_COLORS['error'])
            self.img.draw_circle(60, record_area_y + 55, 15, UI_COLORS['error'], fill=True)
            self.img.draw_string_advanced(40, record_area_y + 80, 14, "✗", color=UI_COLORS['card_bg'])
        else:
            self.img.draw_string_advanced(40, record_area_y + 15, 16, "准备就绪", color=UI_COLORS['text_primary'])
            self.img.draw_string_advanced(40, record_area_y + 40, 14, "按下按键开始录音", color=UI_COLORS['text_secondary'])
        
        result_area_y = record_area_y + record_area_height + 10
        result_area_height = 200
        
        self.draw_rounded_rect(self.img, 20, result_area_y, DISPLAY_WIDTH - 40, result_area_height, 
                             UI_COLORS['card_bg'], corner_radius=16, fill=True)
        
        self.img.draw_string_advanced(40, result_area_y + 15, 14, "识别结果:", color=UI_COLORS['text_secondary'])
        
        content_start_y = result_area_y + 45
        if self.recognition_result:
            available_height = result_area_height - (content_start_y - result_area_y) - 15
            self.draw_text_with_wrapping(self.img, 40, content_start_y, DISPLAY_WIDTH - 80, 
                                      available_height, self.recognition_result, 
                                      font_size=14, color=UI_COLORS['text_primary'])
        else:
            self.img.draw_string_advanced(40, content_start_y, 14, "暂无识别结果", 
                                       color=UI_COLORS['text_secondary'])
        
        status_y = DISPLAY_HEIGHT - 60
        
        if self.ui_state == "error":
            status_color = UI_COLORS['error']
        elif self.ui_state == "completed":
            status_color = UI_COLORS['success']
        elif self.ui_state in ["recording", "uploading", "processing"]:
            status_color = UI_COLORS['warning']
        else:
            status_color = UI_COLORS['separator']
        
        self.draw_rounded_rect(self.img, 20, status_y, DISPLAY_WIDTH - 40, 40, 
                             status_color, corner_radius=8, fill=True)
        
        if self.ui_state in ["error", "completed", "recording", "uploading", "processing"]:
            text_color = UI_COLORS['card_bg']
        else:
            text_color = UI_COLORS['text_secondary']
        
        self.img.draw_string_advanced(40, status_y + 12, 14, self.status_message, color=text_color)
        
        Display.show_image(self.img)

    def exit_check(self):
        try:
            os.exitpoint()
        except KeyboardInterrupt as e:
            print("user stop: ", e)
            return True
        return False

    def connect_wifi(self):
        print("正在连接WiFi...")
        
        if self.enable_ui:
            self.ui_state = "processing"
            self.status_message = "正在连接WiFi..."
            self.update_ui()
        
        try:
            import network
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            
            if not wlan.isconnected():
                print(f"连接到WiFi: {self.wifi_ssid}")
                wlan.connect(self.wifi_ssid, self.wifi_key)
                
                timeout = 15
                while not wlan.isconnected() and timeout > 0:
                    time.sleep(0.5)
                    timeout -= 0.5
                    print(f"连接中... 剩余时间: {timeout:.1f}s")
                    
                    if self.enable_ui:
                        self.loading_frame = (self.loading_frame + 1) % 100
                        self.status_message = f"连接WiFi中... {timeout:.1f}s"
                        self.update_ui()
                
                if wlan.isconnected():
                    ip = wlan.ifconfig()[0]
                    print(f"WiFi连接成功! IP: {ip}")
                    self.network_connected = True
                    
                    if self.enable_ui:
                        self.ui_state = "completed"
                        self.status_message = f"WiFi连接成功! IP: {ip}"
                        self.update_ui()
                        time.sleep(1)
                        self.ui_state = "idle"
                        self.status_message = "准备开始录音"
                        self.update_ui()
                    
                    return True
                else:
                    print("WiFi连接超时")
                    self.network_connected = False
                    
                    if self.enable_ui:
                        self.ui_state = "error"
                        self.status_message = "WiFi连接超时"
                        self.update_ui()
                    
                    return False
            else:
                ip = wlan.ifconfig()[0]
                print(f"WiFi已连接! IP: {ip}")
                self.network_connected = True
                
                if self.enable_ui:
                    self.ui_state = "idle"
                    self.status_message = f"WiFi已连接! IP: {ip}"
                    self.update_ui()
                
                return True
                
        except Exception as e:
            print(f"WiFi连接失败: {e}")
            self.network_connected = False
            
            if self.enable_ui:
                self.ui_state = "error"
                self.status_message = f"WiFi连接失败: {str(e)}"
                self.update_ui()
            
            return False

    def basename(self, path):
        if hasattr(os, 'path') and hasattr(os.path, 'basename'):
            return os.path.basename(path)
        else:
            if '/' in path:
                return path.split('/')[-1]
            elif '\\' in path:
                return path.split('\\')[-1]
            else:
                return path

    def file_exists(self, path):
        try:
            if hasattr(os, 'path') and hasattr(os.path, 'exists'):
                return os.path.exists(path)
            else:
                try:
                    with open(path, 'rb') as f:
                        pass
                    return True
                except OSError:
                    return False
        except Exception:
            return False

    def get_upload_policy(self, max_retries=10):
        url = f"https://dashscope.aliyuncs.com/api/v1/uploads?action=getPolicy&model={self.model_name}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(max_retries):
            try:
                print(f"获取上传凭证... (尝试 {attempt + 1}/{max_retries})")
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    json_data = response.json()
                    print("上传凭证获取成功")
                    return json_data['data']
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"获取上传凭证失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                
                if attempt < max_retries - 1:
                    wait_time = 3 + (attempt * 2)
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"获取上传凭证失败，已重试 {max_retries} 次: {error_msg}")

    def upload_file_to_oss(self, policy_data, file_path, max_retries=1):
        original_file_name = self.basename(file_path)
        
        timestamp = str(int(time.time() * 1000))
        name_parts = original_file_name.rsplit('.', 1)
        if len(name_parts) == 2:
            file_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            file_name = f"{original_file_name}_{timestamp}"
        
        key = f"{policy_data['upload_dir']}/{file_name}"
        
        with open(file_path, 'rb') as file_content:
            file_data = file_content.read()
        
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        
        form_data = []
        
        fields = {
            'OSSAccessKeyId': policy_data['oss_access_key_id'],
            'Signature': policy_data['signature'],
            'policy': policy_data['policy'],
            'x-oss-object-acl': policy_data['x_oss_object_acl'],
            'x-oss-forbid-overwrite': policy_data['x_oss_forbid_overwrite'],
            'key': key,
            'success_action_status': '200'
        }
        
        for field_name, field_value in fields.items():
            form_data.append(f'--{boundary}')
            form_data.append(f'Content-Disposition: form-data; name="{field_name}"')
            form_data.append('')
            form_data.append(str(field_value))
        
        form_data.append(f'--{boundary}')
        form_data.append(f'Content-Disposition: form-data; name="file"; filename="{file_name}"')
        form_data.append('Content-Type: application/octet-stream')
        form_data.append('')
        
        text_part = '\r\n'.join(form_data) + '\r\n'
        text_bytes = text_part.encode('utf-8')
        
        end_boundary = f'\r\n--{boundary}--\r\n'.encode('utf-8')
        body = text_bytes + file_data + end_boundary
        
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
        
        for attempt in range(max_retries):
            try:
                print(f"上传文件到OSS... (尝试 {attempt + 1}/{max_retries})")
                response = requests.post(policy_data['upload_host'], data=body, headers=headers)
                
                if response.status_code == 200:
                    print("文件上传成功")
                    return f"oss://{key}"
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"文件上传失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                
                if attempt < max_retries - 1:
                    wait_time = 3 + (attempt * 2)
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"文件上传失败，已重试 {max_retries} 次: {error_msg}")

    def upload_audio_to_oss(self, audio_path, max_retries=5):
        if not self.network_connected:
            print("网络未连接，尝试连接WiFi...")
            if not self.connect_wifi():
                raise Exception("WiFi连接失败，无法上传文件")
        
        print("开始上传音频到OSS...")
        
        with open(audio_path, 'rb') as f:
            pass
        
        for attempt in range(max_retries):
            try:
                print(f"上传音频到OSS... (尝试 {attempt + 1}/{max_retries})")
                
                oss_url = upload_image.upload_image_to_dashscope(self.api_key, audio_path, self.model_name)
                
                print(f"音频上传成功! OSS地址: {oss_url}")
                return oss_url
                
            except Exception as e:
                error_msg = str(e)
                print(f"音频上传失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                
                if attempt < max_retries - 1:
                    wait_time = 3 + (attempt * 2)
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"音频上传失败，已重试 {max_retries} 次: {error_msg}")

    def record_with_button_and_upload(self, filename, key, left_volume=85, right_volume=85, ans=False, auto_upload=True):
        oss_url = None
        try:
            if self.enable_ui:
                self.ui_state = "idle"
                self.status_message = "准备录音..."
                self.update_ui()
            
            if auto_upload:
                print("准备上传功能，检查网络连接...")
                if not self.connect_wifi():
                    print("WiFi连接失败，将只保存本地文件")
                    auto_upload = False
            
            self.input_stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )

            self.input_stream.volume(LEFT, left_volume)
            self.input_stream.volume(RIGHT, right_volume)

            if(ans):
                self.input_stream.enable_audio3a(AUDIO_3A_ENABLE_ANS)

            print("等待按键开始录制...")
            if self.enable_ui:
                self.ui_state = "idle"
                self.status_message = "按下按键开始录音..."
                self.update_ui()
            
            while not key.is_pressed():
                if self.exit_check():
                    return None
                time.sleep(0.01)

            print("开始录制...按键松开时停止")
            self.frames = []
            self.is_recording = True
            
            if self.enable_ui:
                self.ui_state = "recording"
                self.status_message = "录音中...松开按键停止"
                self.update_ui()

            recording_frame = 0
            while key.is_pressed() and self.is_recording:
                if self.exit_check():
                    break
                data = self.input_stream.read()
                self.frames.append(data)
                
                if self.enable_ui:
                    recording_frame += 1
                    if recording_frame % 10 == 0:
                        self.update_ui()

            print("停止录制...")
            
            if self.enable_ui:
                self.ui_state = "processing"
                self.status_message = "保存音频文件..."
                self.update_ui()

            self._save_to_wav(filename)
            
            if auto_upload and self.frames and self.network_connected:
                if self.enable_ui:
                    self.status_message = "上传到OSS..."
                    self.update_ui()
                oss_url = self.upload_audio_to_oss(filename)
                
                if self.enable_ui:
                    if oss_url:
                        self.ui_state = "completed"
                        self.status_message = "录音和上传完成！"
                    else:
                        self.ui_state = "error"
                        self.status_message = "上传失败"
                    self.update_ui()
            else:
                if self.enable_ui:
                    self.ui_state = "completed"
                    self.status_message = "录音完成！"
                    self.update_ui()

        except BaseException as e:
            print(f"Exception {e}")
            if self.enable_ui:
                self.ui_state = "error"
                self.status_message = f"录音失败: {str(e)}"
                self.update_ui()
        finally:
            self.stop()
            
        return oss_url

    def record_and_upload(self, filename, duration, left_volume=85, right_volume=85, ans=False, auto_upload=True):
        oss_url = None
        try:
            self.input_stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )

            self.input_stream.volume(LEFT, left_volume)
            self.input_stream.volume(RIGHT, right_volume)

            if(ans):
                self.input_stream.enable_audio3a(AUDIO_3A_ENABLE_ANS)

            print("start record...")
            self.frames = []
            self.is_recording = True

            for i in range(0, int(self.RATE / self.CHUNK * duration)):
                if not self.is_recording or self.exit_check():
                    break
                data = self.input_stream.read()
                self.frames.append(data)

            print("stop record...")

            self._save_to_wav(filename)
            
            if auto_upload and self.frames:
                oss_url = self.upload_audio_to_oss(filename)

        except BaseException as e:
            print(f"Exception {e}")
        finally:
            self.stop()
            
        return oss_url

    def record_with_button_and_speech_to_text(self, filename, key, left_volume=85, right_volume=85, ans=False):
        """
        按键控制录制音频并转换为文字
        Record audio with button control and convert to text
        
        参数 / Parameters:
            filename: 音频保存路径 / Path to save audio file
            key: 按键对象 / Button object
            left_volume: 左声道音量 / Left channel volume
            right_volume: 右声道音量 / Right channel volume
            ans: 是否启用音频3A功能：自动噪声抑制(ANS) / Open Ans or not
            
        返回:
            tuple: (success, result) - success为布尔值，result为转换结果或错误信息
        """
        try:
            # 初始化UI状态
            if self.enable_ui:
                self.ui_state = "idle"
                self.status_message = "准备语音识别..."
                self.recognition_result = ""
                self.update_ui()
            
            # 录制音频并上传
            oss_url = self.record_with_button_and_upload(filename, key, left_volume, right_volume, ans, auto_upload=True)
            
            if not oss_url:
                if self.enable_ui:
                    self.ui_state = "error"
                    self.status_message = "录音或上传失败"
                    self.update_ui()
                return False, "录音或上传失败"
            
            # 更新UI状态为语音识别中
            if self.enable_ui:
                self.ui_state = "processing"
                self.status_message = "正在进行语音识别..."
                self.update_ui()
            
            # 进行语音转文字，传递OSS URL而不是本地文件路径
            success, result = self.speech_to_text_from_oss(oss_url)
            
            # 更新UI显示识别结果
            if self.enable_ui:
                if success:
                    self.ui_state = "completed"
                    self.status_message = "语音识别完成！"
                    self.recognition_result = result
                else:
                    self.ui_state = "error"
                    self.status_message = "语音识别失败"
                    self.recognition_result = result
                self.update_ui()
            
            return success, result
            
        except Exception as e:
            if self.enable_ui:
                self.ui_state = "error"
                self.status_message = f"语音识别异常: {str(e)}"
                self.update_ui()
            return False, f"录音转文字异常: {str(e)}"

    def record_and_speech_to_text(self, filename, duration, left_volume=85, right_volume=85, ans=False):
        try:
            oss_url = self.record_and_upload(filename, duration, left_volume, right_volume, ans, auto_upload=True)
            
            if not oss_url:
                return False, "录音或上传失败"
            
            success, result = self.speech_to_text_from_oss(oss_url)
            
            return success, result
            
        except Exception as e:
            return False, f"录音转文字异常: {str(e)}"

    def speech_to_text(self, audio_file_path):
        try:
            print(f"开始语音转文字处理: {audio_file_path}")
            
            task_id = self.submit_voice_task(audio_file_path)
            if not task_id:
                return False, "提交语音识别任务失败"
            
            print(f"任务ID: {task_id}")
            
            max_attempts = 30
            for attempt in range(max_attempts):
                print(f"检查任务状态 ({attempt + 1}/{max_attempts})...")
                
                status, result = self.check_task_status(task_id)
                
                if status == "SUCCEEDED":
                    print("语音识别成功!")
                    return True, result
                elif status == "FAILED":
                    print("语音识别失败")
                    return False, result
                elif status in ["PENDING", "RUNNING"]:
                    print(f"任务状态: {status}，等待中...")
                    time.sleep(2)
                else:
                    print(f"未知任务状态: {status}")
                    time.sleep(2)
            
            return False, "语音识别超时"
            
        except Exception as e:
            print(f"语音转文字过程中出现错误: {e}")
            return False, str(e)

    def record_with_button_and_speech_to_text(self, save_path, key):
        try:
            if not self.network_connected:
                print("尝试连接WiFi...")
                if not self.connect_wifi():
                    return False, "WiFi连接失败，无法进行语音识别"
            
            print("按下按键开始录音，松开按键停止录音...")
            oss_url = self.record_with_button_and_upload(save_path, key, auto_upload=True)
            
            if oss_url is None:
                return False, "录音或上传失败"
            
            print(f"录音完成，文件保存至: {save_path}")
            print(f"开始语音转文字处理，OSS URL: {oss_url}")
            
            return self.speech_to_text_from_oss(oss_url)
            
        except Exception as e:
            print(f"按键录音转文字过程中出现错误: {e}")
            return False, str(e)

    def record_and_speech_to_text(self, save_path, duration=5):
        try:
            if not self.network_connected:
                print("尝试连接WiFi...")
                if not self.connect_wifi():
                    return False, "WiFi连接失败，无法进行语音识别"
            
            print(f"开始录音 {duration} 秒...")
            oss_url = self.record_and_upload(save_path, duration, auto_upload=True)
            
            if oss_url is None:
                return False, "录音或上传失败"
            
            print(f"录音完成，文件保存至: {save_path}")
            print(f"开始语音转文字处理，OSS URL: {oss_url}")
            
            return self.speech_to_text_from_oss(oss_url)
            
        except Exception as e:
            print(f"固定时长录音转文字过程中出现错误: {e}")
            return False, str(e)

    def stop(self):
        self.is_recording = False
        if hasattr(self, 'input_stream') and self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
                delattr(self, 'input_stream')
            except Exception as e:
                print(f"关闭音频流时出错: {e}")

    def _save_to_wav(self, filename):
        if not self.frames:
            print("没有录制到任何音频，不保存文件")
            return

        wf = wave.open(filename, 'wb')
        wf.set_channels(self.CHANNELS)
        wf.set_sampwidth(self.p.get_sample_size(self.FORMAT))
        wf.set_framerate(self.RATE)
        wf.write_frames(b''.join(self.frames))
        wf.close()
        print(f"录音已保存到: {filename}")

    def submit_voice_task(self, oss_url, max_retries=5):
        url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
            "X-DashScope-OssResourceResolve": "enable"
        }
        
        if isinstance(oss_url, list):
            oss_url = oss_url[0] if len(oss_url) > 0 else ""
        elif not isinstance(oss_url, str):
            oss_url = str(oss_url)
            
        print(f"准备提交语音识别任务，OSS URL: {oss_url}")
        
        data = {
            "model": "paraformer-v2",
            "input": {
                "file_urls": [oss_url]
            },
            "parameters": {
                "format": "wav",
                "sample_rate": 16000,
                "language_hints": ["zh", "en"]
            }
        }
        
        for attempt in range(max_retries):
            try:
                print(f"提交语音识别任务... (尝试 {attempt + 1}/{max_retries})")
                response = requests.post(url, headers=headers, data=json.dumps(data))
                
                if response.status_code == 200:
                    json_data = response.json()
                    if json_data.get('output') and json_data['output'].get('task_id'):
                        print(f"任务提交成功，任务ID: {json_data['output']['task_id']}")
                        return json_data['output']['task_id']
                    else:
                        raise Exception(f"任务提交失败: {json_data}")
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"提交任务失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                
                if attempt < max_retries - 1:
                    wait_time = 3 + (attempt * 2)
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"提交任务失败，已重试 {max_retries} 次: {error_msg}")

    def download_transcription_result(self, transcription_url):
        try:
            print(f"下载转录结果: {transcription_url}")
            response = requests.get(transcription_url)
            
            if response.status_code == 200:
                content = response.text
                print(f"原始响应内容: {content}")
                
                try:
                    json_data = json.loads(content)
                    print(f"解析成功: {json_data}")
                    return json_data
                except:
                    print("直接JSON解析失败，尝试手动处理...")
                    
                    start_idx = content.find('{')
                    end_idx = content.rfind('}')
                    
                    if start_idx != -1 and end_idx != -1:
                        json_content = content[start_idx:end_idx+1]
                        print(f"提取的JSON内容: {json_content}")
                        
                        try:
                            json_data = json.loads(json_content)
                            print(f"手动解析成功: {json_data}")
                            return json_data
                        except Exception as parse_error:
                            print(f"手动解析也失败: {parse_error}")
                            
                            lines = content.strip().split('\n')
                            for line in lines:
                                line = line.strip()
                                if line.startswith('{') and line.endswith('}'):
                                    try:
                                        json_data = json.loads(line)
                                        print(f"逐行解析成功: {json_data}")
                                        return json_data
                                    except:
                                        continue
                    
                    print("所有JSON解析方法都失败，返回原始内容")
                    return {"raw_content": content}
                    
            else:
                raise Exception(f"下载失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"下载转录结果失败: {e}")
            raise

    def check_task_status(self, task_id):
        url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            print(f"检查任务状态: {task_id}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                content = response.text
                print(f"状态查询响应: {content}")
                
                try:
                    json_data = json.loads(content)
                except:
                    start_idx = content.find('{')
                    end_idx = content.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        json_content = content[start_idx:end_idx+1]
                        try:
                            json_data = json.loads(json_content)
                        except:
                            lines = content.strip().split('\n')
                            json_data = None
                            for line in lines:
                                line = line.strip()
                                if line.startswith('{') and line.endswith('}'):
                                    try:
                                        json_data = json.loads(line)
                                        break
                                    except:
                                        continue
                            if json_data is None:
                                raise Exception("无法解析响应JSON")
                
                task_status = json_data.get('output', {}).get('task_status', 'UNKNOWN')
                print(f"任务状态: {task_status}")
                
                if task_status == 'SUCCEEDED':
                    results = json_data.get('output', {}).get('results', [])
                    if results and len(results) > 0:
                        transcription_url = results[0].get('transcription_url')
                        if transcription_url:
                            print(f"获取到转录结果URL: {transcription_url}")
                            transcription_data = self.download_transcription_result(transcription_url)
                            return 'SUCCEEDED', transcription_data
                        else:
                            return 'SUCCEEDED', {"error": "未找到转录结果URL"}
                    else:
                        return 'SUCCEEDED', {"error": "未找到转录结果"}
                        
                elif task_status == 'FAILED':
                    error_msg = json_data.get('output', {}).get('message', '任务失败')
                    return 'FAILED', {"error": error_msg}
                    
                elif task_status in ['PENDING', 'RUNNING']:
                    return task_status, None
                    
                else:
                    return 'UNKNOWN', {"error": f"未知任务状态: {task_status}"}
                    
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"检查任务状态失败: {e}")
            return 'ERROR', {"error": str(e)}

    def speech_to_text_from_oss(self, oss_url, max_wait_time=60):
        try:
            print(f"开始语音转文字，使用OSS URL: {oss_url}")
            
            task_id = self.submit_voice_task(oss_url)
            print(f"语音识别任务已提交: {task_id}")
            
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                status, result = self.check_task_status(task_id)
                
                if status == 'SUCCEEDED':
                    print("语音转文字成功!")
                    
                    if isinstance(result, dict):
                        text_result = ""
                        
                        if 'transcripts' in result:
                            transcripts = result['transcripts']
                            if isinstance(transcripts, list) and len(transcripts) > 0:
                                text_result = transcripts[0].get('text', '')
                        
                        elif 'sentences' in result:
                            sentences = result['sentences']
                            if isinstance(sentences, list):
                                text_parts = []
                                for sentence in sentences:
                                    if isinstance(sentence, dict) and 'text' in sentence:
                                        text_parts.append(sentence['text'])
                                text_result = ''.join(text_parts)
                        
                        elif 'text' in result:
                            text_result = result['text']
                        
                        elif 'raw_content' in result:
                            text_result = f"原始内容: {result['raw_content']}"
                        
                        if text_result:
                            print(f"识别结果: {text_result}")
                            return True, text_result
                        else:
                            print(f"未能从结果中提取文本: {result}")
                            return False, f"未能提取文本内容: {result}"
                    else:
                        return False, f"结果格式异常: {result}"
                        
                elif status == 'FAILED':
                    error_msg = result.get('error', '任务失败') if result else '任务失败'
                    print(f"语音转文字失败: {error_msg}")
                    return False, error_msg
                    
                elif status == 'ERROR':
                    error_msg = result.get('error', '检查状态出错') if result else '检查状态出错'
                    print(f"检查状态出错: {error_msg}")
                    return False, error_msg
                    
                else:
                    print(f"任务状态: {status}，继续等待...")
                    time.sleep(2)
            
            return False, "语音转文字超时"
            
        except Exception as e:
            print(f"语音转文字过程中出现错误: {e}")
            return False, str(e)

def ensure_dir(directory):
    try:
        try:
            os.listdir(directory)
            print(f"目录已存在: {directory}")
        except OSError:
            print(f"创建目录: {directory}")
            parts = directory.strip('/').split('/')
            current_path = ''
            for part in parts:
                if part:
                    current_path += '/' + part
                    try:
                        os.mkdir(current_path)
                        print(f"创建子目录: {current_path}")
                    except OSError:
                        pass
    except Exception as e:
        print(f"创建目录失败: {e}")


if __name__ == "__main__":
    os.exitpoint(os.EXITPOINT_ENABLE)
    
    api_key = ""
    model_name = "paraformer-v2"
    save_path = "/data/audio/"
    wifi_ssid = ""
    wifi_key = ""
    
    ensure_dir(save_path)
    
    recorder = AudioRecorderWithUpload(api_key, model_name, wifi_ssid, wifi_key, enable_ui=True)
    key = YbKey()

    print("按下按键开始录音，松开按键停止录音，录音完成后自动转换为文字")
    
    if recorder.enable_ui:
        recorder.ui_state = "idle"
        recorder.status_message = "按下按键开始语音识别..."
        recorder.recognition_result = ""
        recorder.update_ui()
    
    try:
        while True:
            success, result = recorder.record_with_button_and_speech_to_text(
                save_path + 'button_audio.wav', 
                key
            )
            
            if success:
                print(f"✓ 语音识别成功!")
                print(f"识别结果: {result}")
                
                if recorder.enable_ui:
                    recorder.ui_state = "completed"
                    recorder.status_message = "语音识别完成！"
                    recorder.recognition_result = result
                    recorder.update_ui()
            else:
                print(f"✗ 语音识别失败: {result}")
                
                if recorder.enable_ui:
                    recorder.ui_state = "error"
                    recorder.status_message = "语音识别失败"
                    recorder.recognition_result = result
                    recorder.update_ui()
                
            if recorder.enable_ui:
                time.sleep(5)
                recorder.ui_state = "idle"
                recorder.status_message = "按下按键开始下一次语音识别..."
                recorder.update_ui()
            
    except Exception as e:
        print(f"操作失败: {e}")

    print("程序结束")