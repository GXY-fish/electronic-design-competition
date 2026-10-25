# 简化版AI文本聊天程序 - 单次对话多页显示
import uos
import time
import gc
import ujson as json
from media.display import *
from media.media import *
import ybUtils.YbKey as YbKey

# 导入网络请求模块
import YbRequests as requests

USER_QUESTION = "给我讲个笑话吧"

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
    'shadow': (0, 0, 0, 20),
    'separator': (229, 229, 234),
}

chat_history = [
    {"role": "system", "content": "回复内容控制在一百字以内"},
    {"role": "system", "content": "你是一个有用的助手"}
]

ai_response_text = "程序启动中..."
response_pages = []
current_page = 0
total_pages = 0
program_state = "connecting"

max_retries = 3
current_retry = 0
retry_delay = 2

def connect_wifi():
    """连接WiFi网络"""
    global network_connected
    
    print("正在连接WiFi...")
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        if not wlan.isconnected():
            wlan.connect(WIFI_SSID, WIFI_KEY)
            
            # 等待连接
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

def split_text_to_pages(text, max_chars_per_page=400):
    if not text or len(text) <= max_chars_per_page:
        return [text] if text else [""]
    
    pages = []
    sentences = text.split('。')
    current_page = ""
    
    for sentence in sentences:
        if len(current_page + sentence + '。') <= max_chars_per_page:
            current_page += sentence + '。'
        else:
            if current_page.strip():
                pages.append(current_page.strip())
            
            if len(sentence) > max_chars_per_page:
                for i in range(0, len(sentence), max_chars_per_page - 10):
                    chunk = sentence[i:i + max_chars_per_page - 10]
                    if i + max_chars_per_page - 10 < len(sentence):
                        chunk += "..."
                    pages.append(chunk)
                current_page = ""
            else:
                current_page = sentence + '。'
    
    if current_page.strip():
        pages.append(current_page.strip())
    
    return pages if pages else [""]

def draw_text_with_proper_spacing(img, x, y, width, height, text, font_size=16, color=(28, 28, 30)):
    if not text:
        return
    
    line_height = font_size + 6
    max_lines = (height - 20) // line_height
    
    char_width = font_size * 1.1
    available_width = width - 40
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

def draw_main_interface(img, loading_frame=None):
    """绘制主界面 - 简化的iOS风格"""
    # 清空背景
    img.draw_rectangle(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, UI_COLORS['background'], fill=True)
    
    # 顶部状态栏
    status_bar_height = 44
    img.draw_rectangle(0, 0, DISPLAY_WIDTH, status_bar_height, UI_COLORS['card_bg'], fill=True)
    
    # 标题
    img.draw_string_advanced(20, 14, 20, "AI助手演示", color=UI_COLORS['text_primary'])
    
    status_color = UI_COLORS['success'] if network_connected else UI_COLORS['error']
    img.draw_circle(DISPLAY_WIDTH - 30, 22, 6, status_color, fill=True)
    
    question_area_y = status_bar_height + 10
    question_area_height = 60
    
    img.draw_string_advanced(20, question_area_y + 10, 14, "问题: " + USER_QUESTION[:50] + "...", 
                           color=UI_COLORS['text_secondary'])
    
    response_area_y = question_area_y + question_area_height + 10
    response_area_height = 300
    
    draw_rounded_rect(img, 20, response_area_y, DISPLAY_WIDTH - 40, response_area_height, 
                     UI_COLORS['card_bg'], corner_radius=16, fill=True)
    
    shadow_color = (220, 220, 220)
    img.draw_rectangle(22, response_area_y + 2, DISPLAY_WIDTH - 44, 1, shadow_color, fill=True)
    
    if total_pages > 1:
        page_info = f"AI回复 (第{current_page + 1}页/共{total_pages}页):"
    else:
        page_info = "AI回复:"
    
    img.draw_string_advanced(40, response_area_y + 15, 14, page_info, color=UI_COLORS['text_secondary'])
    
    content_start_y = response_area_y + 45
    if current_retry > 0:
        retry_text = f"正在重试... (第{current_retry}次/共{max_retries}次)"
        img.draw_string_advanced(40, content_start_y, 14, retry_text, color=(255, 149, 0))
        
        progress_width = DISPLAY_WIDTH - 100
        progress_x = 40
        progress_y = content_start_y + 25
        
        img.draw_rectangle(progress_x, progress_y, progress_width, 4, 
                         UI_COLORS['separator'], fill=True)
        
        current_progress = (current_retry / max_retries) * progress_width
        img.draw_rectangle(progress_x, progress_y, int(current_progress), 4, 
                         (255, 149, 0), fill=True)
        
        content_start_y += 40
    
    if loading_frame is not None:
        img.draw_string_advanced(40, content_start_y, 16, "AI正在思考...", color=UI_COLORS['text_secondary'])
        draw_loading_spinner(img, 40, content_start_y + 30, loading_frame)
    else:
        if response_pages and current_page < len(response_pages):
            current_text = response_pages[current_page]
            available_height = response_area_height - (content_start_y - response_area_y) - 15
            draw_text_with_proper_spacing(img, 40, content_start_y, DISPLAY_WIDTH - 80, 
                                        available_height, current_text, 
                                        font_size=16, color=UI_COLORS['text_primary'])
    
    status_y = DISPLAY_HEIGHT - 60
    
    draw_rounded_rect(img, 20, status_y, DISPLAY_WIDTH - 40, 40, 
                     UI_COLORS['separator'], corner_radius=8, fill=True)
    
    status_messages = {
        "connecting": "正在连接网络...",
        "asking": f"重试发送中... ({current_retry}/{max_retries})" if current_retry > 0 else "准备发送问题...",
        "responding": "等待AI回复...",
        "displaying": f"显示中 (3秒后自动翻页)" if total_pages > 1 and current_page < total_pages - 1 else "显示完成",
        "completed": "对话完成"
    }
    
    status_text = status_messages.get(program_state, "运行中...")
    img.draw_string_advanced(40, status_y + 12, 14, status_text, color=UI_COLORS['text_secondary'])

def send_message_to_ai(message):
    global chat_history, ai_response_text, response_pages, total_pages, current_retry
    
    if not network_connected:
        ai_response_text = "网络未连接，无法获取AI回复"
        response_pages = [ai_response_text]
        total_pages = 1
        return False, "网络未连接"
    
    # 重试逻辑
    for attempt in range(max_retries):
        current_retry = attempt + 1
        
        try:
            print(f"尝试发送请求 (第{current_retry}次/共{max_retries}次)")
            
            # 添加用户消息到历史记录（只在第一次尝试时添加）
            if attempt == 0:
                chat_history.append({"role": "user", "content": message})
            
            # 准备API请求
            url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "qwen-plus",
                "messages": chat_history,
                "max_tokens": 200,  # 减少token数量以配合字数限制
                "temperature": 0.7
            }
            
            print(f"发送消息给AI: {message}")
            
            # 发送请求，增加超时时间
            response = requests.post(url, headers=headers, json_data=data, timeout=45)
            
            if response.status_code == 200:
                result = response.json
                if result and 'choices' in result and len(result['choices']) > 0:
                    ai_response = result['choices'][0]['message']['content']
                    
                    # 添加AI回复到历史记录（只在第一次成功时添加）
                    if attempt == 0 or len(chat_history) == 1 or chat_history[-1]['role'] != 'assistant':
                        chat_history.append({"role": "assistant", "content": ai_response})
                    
                    # 更新显示的回复文本并分页
                    ai_response_text = ai_response
                    response_pages = split_text_to_pages(ai_response, max_chars_per_page=400)
                    total_pages = len(response_pages)
                    
                    print(f"AI回复成功: {ai_response}")
                    print(f"分页数量: {total_pages}")
                    current_retry = 0  # 重置重试计数
                    return True, ai_response
                else:
                    error_msg = "AI响应格式错误"
                    print(f"响应格式错误: {result}")
                    if attempt == max_retries - 1:  # 最后一次尝试
                        ai_response_text = error_msg
                        response_pages = [error_msg]
                        total_pages = 1
                        current_retry = 0
                        return False, error_msg
            else:
                error_msg = f"API请求失败，状态码: {response.status_code}"
                print(f"HTTP错误: {error_msg}")
                if attempt == max_retries - 1:  # 最后一次尝试
                    ai_response_text = error_msg
                    response_pages = [error_msg]
                    total_pages = 1
                    current_retry = 0
                    return False, error_msg
                    
        except Exception as e:
            error_str = str(e)
            print(f"请求异常 (第{current_retry}次尝试): {error_str}")
            
            retryable_errors = [
                "SSL - The connection indicated an EOF",
                "timeout",
                "Connection reset",
                "Connection refused",
                "Network is unreachable",
                "Name or service not known"
            ]
            
            is_retryable = any(err in error_str for err in retryable_errors)
            
            if attempt == max_retries - 1 or not is_retryable:
                if "SSL" in error_str:
                    error_msg = f"SSL连接失败，已重试{current_retry}次: {error_str}"
                elif "timeout" in error_str:
                    error_msg = f"网络超时，已重试{current_retry}次: {error_str}"
                else:
                    error_msg = f"网络错误，已重试{current_retry}次: {error_str}"
                
                ai_response_text = error_msg
                response_pages = [error_msg]
                total_pages = 1
                current_retry = 0
                return False, error_msg
            else:
                print(f"等待{retry_delay}秒后重试...")
                time.sleep(retry_delay)
                continue
    
    current_retry = 0
    return False, "未知错误"

def main():
    global current_page, program_state
    
    key = YbKey.YbKey()
    
    Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    MediaManager.init()
    
    img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.ARGB8888)
    
    loading_frame = None
    loading_start_time = 0
    state_start_time = time.ticks_ms()
    last_key_status = False
    key_press_start_time = 0
    message_sent = False
    
    print("=== 简化版AI文本聊天演示程序启动 ===")
    print("程序将发送一次问题并以多页形式显示AI回复")
    print("长按按键可重新连接网络")
    
    try:
        while True:
            uos.exitpoint()
            current_time = time.ticks_ms()
            
            key_pressed = key.is_pressed() == 1
            
            if key_pressed and not last_key_status:
                key_press_start_time = current_time
                last_key_status = True
            elif not key_pressed and last_key_status:
                press_duration = current_time - key_press_start_time
                
                if press_duration > 2000:
                    print("长按检测到，重新连接WiFi...")
                    program_state = "connecting"
                    ai_response_text = "正在重新连接WiFi..."
                    message_sent = False
                    current_page = 0
                    state_start_time = current_time
                    
                    if connect_wifi():
                        ai_response_text = "WiFi重连成功！"
                        program_state = "asking"
                    else:
                        ai_response_text = "WiFi重连失败，请检查网络设置"
                        program_state = "connecting"
                    
                    state_start_time = current_time
                
                last_key_status = False
            
            time_elapsed = current_time - state_start_time
            
            if program_state == "connecting":
                if time_elapsed > 2000:
                    if connect_wifi():
                        program_state = "asking"
                        ai_response_text = "网络连接成功，准备发送问题..."
                    else:
                        ai_response_text = "网络连接失败，请检查网络设置"
                    state_start_time = current_time
            
            elif program_state == "asking" and not message_sent:
                if time_elapsed > 2000:
                    program_state = "responding"
                    loading_frame = 0
                    loading_start_time = current_time
                    ai_response_text = "AI正在思考..."
                    
                    success, response = send_message_to_ai(USER_QUESTION)
                    message_sent = True
                    
                    loading_frame = None
                    program_state = "displaying"
                    current_page = 0
                    state_start_time = current_time
                    
                    if not success:
                        print(f"发送失败: {response}")
            
            elif program_state == "displaying":
                if total_pages > 1 and current_page < total_pages - 1:
                    if time_elapsed > 4000:
                        current_page += 1
                        state_start_time = current_time
                        print(f"自动翻页到第 {current_page + 1} 页")
                elif time_elapsed > 4000:
                    program_state = "completed"
                    state_start_time = current_time
            
            if loading_frame is not None:
                if current_time - loading_start_time > 100:
                    loading_frame += 1
                    loading_start_time = current_time
            
            draw_main_interface(img, loading_frame)
            Display.show_image(img)
            
            if current_time % 5000 < 50:
                gc.collect()
            
            time.sleep_ms(50)
            
    except KeyboardInterrupt:
        print("用户停止程序")
    except Exception as e:
        print(f"程序异常: {e}")
    finally:
        Display.deinit()
        uos.exitpoint(uos.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()
        print("程序已退出")

if __name__ == "__main__":
    main()