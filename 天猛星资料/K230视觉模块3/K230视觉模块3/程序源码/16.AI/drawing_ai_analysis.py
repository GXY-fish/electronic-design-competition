# Drawing + Multimodal Analysis Integrated Script (Multi-OSD Layer Version)
import uos
import time
import ssl
from media.display import *
from media.media import *
import ybUtils.YbKey as YbKey
from machine import TOUCH

import libs.upload_image as upload_image
import YbRequests as requests

save_path = "/sdcard/drawings/"
prefix = time.ticks_us() % 10000
drawing_count = 1

API_KEY = ""
WIFI_SSID = ""
WIFI_KEY = ""

network_connected = False

DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

tp = TOUCH(0)

drawing_canvas = None
ui_overlay = None

UI_COLORS = {
    'primary': (0, 150, 255),
    'success': (0, 200, 100),
    'warning': (255, 180, 0),
    'error': (255, 80, 80),
    'info': (150, 150, 255),
    'text': (255, 255, 255),
    'text_dim': (200, 200, 200),
    'background': (20, 20, 30),
    'progress_bg': (60, 60, 80),
    'progress_fill': (0, 180, 255),
    'canvas_bg': (255, 255, 255),
    'brush_color': (0, 0, 0),
    'ui_overlay': (240, 240, 240)
}

def draw_rounded_rect(img, x, y, width, height, color, corner_radius=5):
    img.draw_rectangle(x + corner_radius, y, width - 2 * corner_radius, height, color, fill=True)
    img.draw_rectangle(x, y + corner_radius, width, height - 2 * corner_radius, color, fill=True)
    
    for i in range(corner_radius):
        for j in range(corner_radius):
            if i * i + j * j <= corner_radius * corner_radius:
                img.draw_rectangle(x + corner_radius - i, y + corner_radius - j, 1, 1, color, fill=True)
                img.draw_rectangle(x + width - corner_radius + i - 1, y + corner_radius - j, 1, 1, color, fill=True)
                img.draw_rectangle(x + corner_radius - i, y + height - corner_radius + j - 1, 1, 1, color, fill=True)
                img.draw_rectangle(x + width - corner_radius + i - 1, y + height - corner_radius + j - 1, 1, 1, color, fill=True)

def draw_progress_bar(img, x, y, width, height, progress, bg_color=None, fill_color=None, show_text=True):
    if bg_color is None:
        bg_color = UI_COLORS['progress_bg']
    if fill_color is None:
        fill_color = UI_COLORS['progress_fill']
    
    progress = max(0.0, min(1.0, progress))
    
    draw_rounded_rect(img, x, y, width, height, bg_color, corner_radius=height//2)
    
    if progress > 0:
        fill_width = int(width * progress)
        if fill_width > 0:
            draw_rounded_rect(img, x, y, fill_width, height, fill_color, corner_radius=height//2)
    
    if show_text:
        percentage = int(progress * 100)
        text = f"{percentage}%"
        text_x = x + width // 2 - len(text) * 4
        text_y = y + height // 2 - 8
        img.draw_string_advanced(text_x, text_y, 16, text, color=UI_COLORS['text'])

def draw_status_card(img, x, y, width, height, title, content, status_type='info'):
    color_map = {
        'info': UI_COLORS['info'],
        'success': UI_COLORS['success'],
        'warning': UI_COLORS['warning'],
        'error': UI_COLORS['error']
    }
    
    card_color = color_map.get(status_type, UI_COLORS['info'])
    
    bg_color = (40, 40, 50)
    draw_rounded_rect(img, x, y, width, height, bg_color, corner_radius=8)
    
    img.draw_rectangle(x, y + 5, 4, height - 10, card_color, fill=True)
    
    img.draw_string_advanced(x + 15, y + 12, 20, title, color=card_color)
    
    content_lines = content.split('\n')
    y_offset = y + 40
    line_spacing = 24
    for line in content_lines:
        if y_offset < y + height - 25:
            img.draw_string_advanced(x + 15, y_offset, 16, line, color=UI_COLORS['text'])
            y_offset += line_spacing

def show_loading_animation(img, x, y, frame, text="处理中..."):
    spinner_chars = ['|', '/', '-', '\\']
    spinner = spinner_chars[frame % 4]
    
    animated_text = f"{spinner} {text} {spinner}"
    img.draw_string_advanced(x, y, 18, animated_text, color=UI_COLORS['primary'])

def show_progress_with_animation(img, title, steps, current_step, progress=0.0):
    img_temp = image.Image(640, 480, image.ARGB8888)
    img_temp.clear()
    img_temp.draw_rectangle(0, 0, 640, 480, (30, 30, 40), fill=True)
    
    draw_status_card(img_temp, 50, 150, 540, 180, title, 
                    f"步骤 {current_step}/{len(steps)}: {steps[current_step-1] if current_step > 0 else '准备中...'}", 
                    'info')
    
    draw_progress_bar(img_temp, 80, 280, 480, 30, progress)
    
    show_loading_animation(img_temp, 250, 350, int(time.ticks_ms() / 200))
    
    Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)

def create_drawing_canvas():
    canvas = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB565)
    canvas.clear()
    
    canvas.draw_rectangle(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, 
                         color=UI_COLORS['canvas_bg'], fill=True)
    
    return canvas

def create_ui_overlay():
    overlay = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.ARGB8888)
    overlay.clear()
    
    overlay.draw_rectangle(0, 0, DISPLAY_WIDTH, 60, 
                         color=UI_COLORS['ui_overlay'], fill=True)
    
    overlay.draw_rectangle(0, DISPLAY_HEIGHT - 60, DISPLAY_WIDTH, 60, 
                         color=UI_COLORS['ui_overlay'], fill=True)
    
    overlay.draw_string_advanced(20, 20, 24, f"绘画模式 - 作品 {drawing_count}", 
                               color=UI_COLORS['primary'])
    
    overlay.draw_string_advanced(20, DISPLAY_HEIGHT - 40, 18, 
                               "在白色区域画画，按物理按键保存并分析", 
                               color=UI_COLORS['text_dim'])
    
    return overlay

def draw_on_canvas(canvas, x, y, last_x, last_y, brush_size=5):
    if last_x is not None and last_y is not None:
        canvas.draw_line(last_x, last_y, x, y, 
                       color=UI_COLORS['brush_color'], thickness=brush_size)
    else:
        canvas.draw_circle(x, y, brush_size//2, 
                         color=UI_COLORS['brush_color'], fill=True)

def enhanced_network_connection(ssid, key, background_img):
    steps = ["初始化网络", "搜索WiFi", "建立连接", "获取IP地址", "连接完成"]
    
    import network
    
    show_progress_with_animation(background_img, "网络连接", steps, 1, 0.1)
    time.sleep_ms(500)
    
    sta = network.WLAN(0)
    sta.active(True)
    
    if sta.isconnected():
        show_progress_with_animation(background_img, "网络连接", steps, 5, 1.0)
        time.sleep_ms(1000)
        return sta.ifconfig()[0]
    
    show_progress_with_animation(background_img, "网络连接", steps, 2, 0.3)
    time.sleep_ms(500)
    
    show_progress_with_animation(background_img, "网络连接", steps, 3, 0.5)
    sta.connect(ssid, key)
    
    timeout = 30
    while not sta.isconnected() and timeout > 0:
        progress = 0.5 + (30 - timeout) / 30 * 0.4
        show_progress_with_animation(background_img, "网络连接", steps, 4, progress)
        time.sleep(1)
        timeout -= 1
    
    if sta.isconnected():
        show_progress_with_animation(background_img, "网络连接", steps, 5, 1.0)
        time.sleep_ms(1500)
        return sta.ifconfig()[0]
    else:
        raise Exception("WiFi连接超时")
            
#    except Exception as e:
#        # 显示错误状态
#        img_temp = image.Image(640, 480, image.RGB565)
#        img_temp.clear()
#        img_temp.copy_from(background_img)
#        draw_status_card(img_temp, 50, 200, 540, 100, "连接失败", str(e), 'error')
#        Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
#        time.sleep_ms(3000)
#        return None

def enhanced_ai_analysis(api_key, image_path, prompt, background_img):
    steps = ["准备上传", "上传画作", "发送分析请求", "等待AI响应", "处理结果"]
    max_retries = 6
    
    for attempt in range(max_retries):
        try:
            if attempt == 0:
                show_progress_with_animation(background_img, "AI分析画作", steps, 1, 0.1)
                time.sleep_ms(500)
                
                show_progress_with_animation(background_img, "AI分析画作", steps, 2, 0.3)
                temp_url = upload_image.upload_image_to_dashscope(api_key, image_path, "qwen-vl-max")
                
                show_progress_with_animation(background_img, "AI分析画作", steps, 3, 0.6)
                time.sleep_ms(500)
                
                show_progress_with_animation(background_img, "AI分析画作", steps, 4, 0.8)
                analysis_result = analyze_image_with_dashscope(api_key, temp_url, prompt)
                
                show_progress_with_animation(background_img, "AI分析画作", steps, 5, 1.0)
                time.sleep_ms(1000)
                
                return analysis_result
            else:
                temp_url = upload_image.upload_image_to_dashscope(api_key, image_path, "qwen-vl-max")
                analysis_result = analyze_image_with_dashscope(api_key, temp_url, prompt)
                
                img_temp = image.Image(640, 480, image.RGB565)
                img_temp.clear()
                img_temp.copy_from(background_img)
                draw_status_card(img_temp, 50, 200, 540, 100, 
                               "✅ 分析成功", "网络恢复正常，画作分析完成！", 'success')
                Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
                time.sleep_ms(1500)
                
                return analysis_result
                
        except Exception as e:
            error_str = str(e).lower()
            
            # 判断错误类型
            network_error_keywords = ['badstatusline', 'connection', 'timeout', 'network', 'socket', 'ssl', 'tls']
            is_network_error = any(keyword in error_str for keyword in network_error_keywords)
            
            config_error_keywords = ['invalidapikey', 'invalid api-key', 'unauthorized', 'forbidden', 'authentication', 'permission']
            is_config_error = any(keyword in error_str for keyword in config_error_keywords)
            
            if is_config_error:
                # 配置错误，不重试
                img_temp = image.Image(640, 480, image.ARGB8888)
                img_temp.clear()
                img_temp.copy_from(background_img)
                
                if 'InvalidApiKey' in str(e) or 'Invalid API-key' in str(e):
                    error_message = "API密钥无效\n请检查配置文件中的API_KEY"
                elif 'unauthorized' in error_str or 'forbidden' in error_str:
                    error_message = "访问权限不足\n请检查API密钥权限"
                else:
                    error_message = f"配置错误\n{str(e)[:60]}..."
                
                draw_status_card(img_temp, 50, 200, 540, 120, 
                               "⚠️ 配置错误", error_message, 'error')
                Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
                time.sleep_ms(5000)
                raise
            
            elif is_network_error and attempt < max_retries - 1:
                # 网络错误，显示友好重试信息
                img_temp = image.Image(640, 480, image.ARGB8888)
                img_temp.clear()
                img_temp.copy_from(background_img)
                
                friendly_message = f"网络波动较大，正在努力为您分析画作_(:з」∠)_\n重试中... ({attempt + 1}/{max_retries})"
                
                draw_status_card(img_temp, 50, 200, 540, 120, 
                               "处理中", friendly_message, 'warning')
                Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
                time.sleep_ms(2000)
                
                # 更新重试状态
                if attempt < max_retries - 2:
                    img_temp2 = image.Image(640, 480, image.ARGB8888)
                    img_temp2.clear()
                    img_temp2.copy_from(background_img)
                    
                    retry_message = f"网络波动较大，正在努力为您分析画作_(:з」∠)_\n [{attempt + 2} / 6] "
                    draw_status_card(img_temp2, 50, 200, 540, 120, 
                                   "Trying...", retry_message, 'info')
                    Display.show_image(img_temp2, 0, 0, Display.LAYER_OSD2)
                    time.sleep_ms(1000)
            
            elif is_network_error and attempt >= max_retries - 1:
                # 网络错误达到最大重试次数
                img_temp = image.Image(640, 480, image.ARGB8888)
                img_temp.clear()
                img_temp.copy_from(background_img)
                draw_status_card(img_temp, 50, 200, 540, 120, 
                               "网络超时", f"已尝试 {max_retries} 次，请检查网络连接\n或稍后再试", 'error')
                Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
                time.sleep_ms(3000)
                raise
            
            else:
                # 其他未知错误
                img_temp = image.Image(640, 480, image.ARGB8888)
                img_temp.clear()
                img_temp.copy_from(background_img)
                
                error_display = str(e)[:80] + "..." if len(str(e)) > 80 else str(e)
                
                draw_status_card(img_temp, 50, 200, 540, 120, 
                               "❌ 处理失败", f"发生错误:\n{error_display}", 'error')
                Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
                time.sleep_ms(4000)
                raise

def analyze_image_with_dashscope(api_key, image_url, prompt="请分析一下这幅画的内容，并给我的画技打个分"):
    """使用DashScope兼容模式API分析画作"""
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-OssResourceResolve": "enable"
    }
    
    data = {
        "model": "qwen-vl-max",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        print(f"正在分析画作: {image_url}")
        print(f"分析提示: {prompt}")
        
        response = requests.post(url, headers=headers, json_data=data, timeout=60)
        print(f"分析响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"分析失败，响应内容: {response.text}")
            raise Exception(f"画作分析失败: {response.text}")
        
        result = response.json
        print("画作分析成功!")
        return result
        
    except Exception as e:
        print(f"画作分析错误: {e}")
        raise

def enhanced_display_analysis_result(background_img, result_text, duration=10000):
    """增强的分析结果显示"""
    try:
        # 智能文本处理
        processed_text = smart_text_processing(result_text)
        pages = split_text_to_pages(processed_text, max_lines_per_page=12, max_chars_per_line=32)
        
        for page_num, page_text in enumerate(pages):
            img_temp = image.Image(640, 480, image.ARGB8888)
            img_temp.clear()
            # 设置不透明的背景色
            img_temp.draw_rectangle(0, 0, 640, 480, (30, 30, 40), fill=True)
            
            # 绘制结果卡片
            card_height = min(400, len(page_text.split('\n')) * 25 + 80)
            draw_status_card(img_temp, 20, 50, 600, card_height, 
                           f"大师点评 ({page_num + 1}/{len(pages)})", 
                           page_text, 'success')
            
            # 添加页面指示器
            if len(pages) > 1:
                indicator_y = card_height + 70
                for i in range(len(pages)):
                    dot_x = 300 + (i - len(pages)//2) * 20
                    dot_color = UI_COLORS['primary'] if i == page_num else UI_COLORS['text_dim']
                    img_temp.draw_circle(dot_x, indicator_y, 4, dot_color, fill=True)
                
                if page_num < len(pages) - 1:
                    img_temp.draw_string_advanced(250, indicator_y + 20, 16, 
                                                "自动翻页中...", color=UI_COLORS['warning'])
                else:
                    img_temp.draw_string_advanced(270, indicator_y + 20, 16, 
                                                "评析完成", color=UI_COLORS['success'])
            
            Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
            
            page_duration = duration // len(pages) if len(pages) > 1 else duration
            page_duration = max(page_duration, 4000)  # 最少4秒
            time.sleep_ms(page_duration)
            
    except Exception as e:
        print(f"显示分析结果时出错: {e}")
        img_temp = image.Image(640, 480, image.ARGB8888)
        img_temp.clear()
        # 设置不透明的背景色
        img_temp.draw_rectangle(0, 0, 640, 480, (30, 30, 40), fill=True)
        draw_status_card(img_temp, 50, 200, 540, 100, "显示完成", "详细结果请查看控制台", 'info')
        Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
        time.sleep_ms(duration)

def smart_text_processing(text):
    """智能文本处理，提取关键信息"""
    if len(text) <= 500:
        return text
    
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 保留重要信息行
        if any(keyword in line for keyword in ['画', '作品', '技法', '色彩', '构图', '评分', '建议', '优点', '不足', '总体']):
            if len(line) > 40:
                if '，' in line:
                    parts = line.split('，')
                    simplified = parts[0] + '，' + parts[1] if len(parts) > 1 else parts[0]
                    if len(simplified) <= 40:
                        processed_lines.append(simplified)
                    else:
                        processed_lines.append(line[:37] + '...')
                else:
                    processed_lines.append(line[:37] + '...')
            else:
                processed_lines.append(line)
    
    if len(processed_lines) > 20:
        processed_lines = processed_lines[:20]
        processed_lines.append("...")
    
    return '\n'.join(processed_lines)

def split_text_to_pages(text, max_lines_per_page=15, max_chars_per_line=35):
    """将文本分割成多页显示"""
    lines = text.split('\n')
    pages = []
    current_page = []
    current_line_count = 0
    
    for line in lines:
        if len(line) > max_chars_per_line:
            while len(line) > max_chars_per_line:
                current_page.append(line[:max_chars_per_line])
                line = line[max_chars_per_line:]
                current_line_count += 1
                
                if current_line_count >= max_lines_per_page:
                    pages.append('\n'.join(current_page))
                    current_page = []
                    current_line_count = 0
            
            if line:
                current_page.append(line)
                current_line_count += 1
        else:
            current_page.append(line)
            current_line_count += 1
        
        if current_line_count >= max_lines_per_page:
            pages.append('\n'.join(current_page))
            current_page = []
            current_line_count = 0
    
    if current_page:
        pages.append('\n'.join(current_page))
    
    return pages if pages else ["无内容显示"]

def ensure_dir(directory):
    """递归创建目录"""
    if not directory or directory == '/':
        return

    directory = directory.rstrip('/')

    try:
        uos.stat(directory)
        print(f'目录已存在: {directory}')
        return
    except OSError:
        if '/' in directory:
            parent = directory[:directory.rindex('/')]
            if parent and parent != directory:
                ensure_dir(parent)

        try:
            uos.mkdir(directory)
            print(f'已创建目录: {directory}')
        except OSError as e:
            try:
                uos.stat(directory)
                print(f'目录已被其他进程创建: {directory}')
            except:
                print(f'创建目录时出错: {e}')
    except Exception as e:
        print(f'处理目录时出错: {e}')

if __name__ == "__main__":
    # 初始化按键
    key = YbKey.YbKey()
    
    # 初始化显示器
    Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    MediaManager.init()
    
    # 创建多图层系统
    drawing_canvas = create_drawing_canvas()  # 纯绘画层
    ui_overlay = create_ui_overlay()          # UI覆盖层
    
    # 触摸状态变量
    last_x = None
    last_y = None
    last_key_status = False
    
    print("=== 触摸绘画+多模态识别系统启动 (多OSD图层版本) ===")
    print("在屏幕上画画，按下按键保存并分析画作")
    print("首次分析时会自动连接WiFi")
    
    while True:
        uos.exitpoint()
        
        # 处理触摸输入
        point = tp.read(1)
        
        if len(point):
            pt = point[0]
            # 处理触摸事件（按下或移动）
            if pt.event == 0 or pt.event == TOUCH.EVENT_DOWN or pt.event == TOUCH.EVENT_MOVE:
                if pt.event != 2:  # 不是抬起事件
                    draw_on_canvas(drawing_canvas, pt.x, pt.y, last_x, last_y)
                last_x = pt.x
                last_y = pt.y
            else:
                # 触摸抬起，重置坐标
                last_x = None
                last_y = None
        
        # 显示多图层：先显示绘画层，再显示UI覆盖层
        Display.show_image(drawing_canvas, 0, 0, Display.LAYER_OSD1)  # 绘画层
        Display.show_image(ui_overlay, 0, 0, Display.LAYER_OSD2)      # UI层
        
        # 检测按键
        if key.is_pressed() == 1:
            if not last_key_status:
                last_key_status = True
                
                print(f"\n=== 开始处理第 {drawing_count} 幅画作 ===")
                
                # 确保目录存在
                ensure_dir(save_path + str(prefix) + "/")
                
                # 保存纯绘画内容（无UI元素）
                drawing_path = save_path + str(prefix) + "/" + f"drawing_{drawing_count}.jpg"
                print(f"保存画作到: {drawing_path}")
                
                # 直接保存纯绘画画布（已经没有UI元素）
                drawing_canvas.save(drawing_path)
                print("画作保存成功!")
                
                # 显示保存成功状态
                success_overlay = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.ARGB8888)
                success_overlay.clear()
                success_overlay.copy_from(ui_overlay)
                draw_status_card(success_overlay, 50, 200, 540, 100, 
                               "🎨 保存成功", f"画作已保存: drawing_{drawing_count}.jpg", 'success')
                Display.show_image(success_overlay, 0, 0, Display.LAYER_OSD2)
                time.sleep_ms(1500)
                
                # 如果还没连接网络，先连接
                if not network_connected:
                    print("首次使用，正在连接WiFi...")
                    ip = enhanced_network_connection(WIFI_SSID, WIFI_KEY, drawing_canvas)
                    if ip:
                        network_connected = True
                        print("网络连接成功!")
                    else:
                        print("网络连接失败，跳过AI分析")
                        drawing_count += 1
                        # 重新创建画布和UI
                        drawing_canvas = create_drawing_canvas()
                        ui_overlay = create_ui_overlay()
                        time.sleep_ms(1000)
                        continue
                
                # 进行AI画作分析
                if network_connected:
                    print("开始分析...")
                    result = enhanced_ai_analysis(API_KEY, drawing_path, 
                                                "请分析一下这幅画的内容，包括画面描述、绘画技法、色彩运用、构图特点等，并给我的画技打个分（1-10分），同时提供一些改进建议。请用简洁友好的语言回复，控制在300字以内。", 
                                                drawing_canvas)
                    
                    # 提取分析结果
                    if 'choices' in result and len(result['choices']) > 0:
                        analysis_text = result['choices'][0]['message']['content']
                        print(f"\n=== 评析结果 ===")
                        print(analysis_text)
                        
                        # 显示分析结果
                        enhanced_display_analysis_result(drawing_canvas, analysis_text, 10000)
                        
                    else:
                        print("AI分析结果格式异常")
                        print(f"完整响应: {result}")
                
                drawing_count += 1
                print(f"=== 第 {drawing_count-1} 幅画作处理完成 ===\n")
                
                # 重新创建画布和UI
                drawing_canvas = create_drawing_canvas()
                ui_overlay = create_ui_overlay()
                time.sleep_ms(100)
        else:
            last_key_status = False
        
        time.sleep(0.05)