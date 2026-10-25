# 拍照+多模态识别整合脚本
import uos
import time
import ssl
from media.sensor import *
from media.display import *
from media.media import *
import ybUtils.YbKey as YbKey

# 导入多模态分析相关模块
import libs.upload_image as upload_image
import YbRequests as requests


save_path = "/sdcard/snapshots/"
prefix = time.ticks_us() % 10000
i = 1

API_KEY = ""
WIFI_SSID = ""
WIFI_KEY = ""

network_connected = False

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
    'progress_fill': (0, 180, 255)
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
    """绘制美观的进度条
    Args:
        img: 图像对象
        x, y: 进度条位置
        width, height: 进度条尺寸
        progress: 进度值 (0.0 - 1.0)
        bg_color: 背景颜色
        fill_color: 填充颜色
        show_text: 是否显示百分比文字
    """
    if bg_color is None:
        bg_color = UI_COLORS['progress_bg']
    if fill_color is None:
        fill_color = UI_COLORS['progress_fill']
    
    # 限制进度值范围
    progress = max(0.0, min(1.0, progress))
    
    # 绘制背景
    draw_rounded_rect(img, x, y, width, height, bg_color, corner_radius=height//2)
    
    # 绘制进度填充
    if progress > 0:
        fill_width = int(width * progress)
        if fill_width > 0:
            draw_rounded_rect(img, x, y, fill_width, height, fill_color, corner_radius=height//2)
    
    # 绘制百分比文字
    if show_text:
        percentage = int(progress * 100)
        text = f"{percentage}%"
        text_x = x + width // 2 - len(text) * 4  # 粗略居中
        text_y = y + height // 2 - 8
        img.draw_string_advanced(text_x, text_y, 16, text, color=UI_COLORS['text'])

def show_progress_with_animation(img, title, steps, current_step, progress=0.0):
    """显示带动画的进度界面"""
    # 创建显示图像
    img_temp = image.Image(640, 480, image.RGB565)
    img_temp.clear()
    img_temp.copy_from(img)
    
    # 绘制状态卡片
    draw_status_card(img_temp, 50, 150, 540, 180, title, 
                    f"步骤 {current_step}/{len(steps)}: {steps[current_step-1] if current_step > 0 else '准备中...'}", 
                    'info')
    
    # 绘制进度条
    draw_progress_bar(img_temp, 80, 280, 480, 30, progress)
    
    # 显示加载动画
    show_loading_animation(img_temp, 250, 350, int(time.ticks_ms() / 200))
    
    Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
    
    # 短暂延迟以显示动画效果
    time.sleep_ms(50)

def draw_status_card(img, x, y, width, height, title, content, status_type='info'):
    """绘制状态卡片
    Args:
        status_type: 'info', 'success', 'warning', 'error'
    """
    # 选择颜色
    color_map = {
        'info': UI_COLORS['info'],
        'success': UI_COLORS['success'],
        'warning': UI_COLORS['warning'],
        'error': UI_COLORS['error']
    }
    
    card_color = color_map.get(status_type, UI_COLORS['info'])
    
    # 绘制卡片背景（更加半透明的效果）
    bg_color = (card_color[0]//6, card_color[1]//6, card_color[2]//6)  # 更透明
    draw_rounded_rect(img, x, y, width, height, bg_color, corner_radius=8)
    
    # 绘制左侧彩色边框
    img.draw_rectangle(x, y + 5, 4, height - 10, card_color, fill=True)
    
    # 绘制标题
    img.draw_string_advanced(x + 15, y + 12, 20, title, color=card_color)
    
    # 绘制内容（增加行间距）
    content_lines = content.split('\n')
    y_offset = y + 40  # 增加标题和内容之间的间距
    line_spacing = 24  # 增加行间距从20到24
    for line in content_lines:
        if y_offset < y + height - 25:  # 调整底部边距
            img.draw_string_advanced(x + 15, y_offset, 16, line, color=UI_COLORS['text'])
            y_offset += line_spacing

def show_loading_animation(img, x, y, frame, text="处理中..."):
    """显示加载动画"""
    # 简单的旋转动画字符
    spinner_chars = ['|', '/', '-', '\\']
    spinner = spinner_chars[frame % 4]
    
    # 绘制动画文字
    animated_text = f"{spinner} {text} {spinner}"
    img.draw_string_advanced(x, y, 18, animated_text, color=UI_COLORS['primary'])

def show_progress_with_animation(img, title, steps, current_step, progress=0.0):
    """显示带动画的进度界面"""
    # 创建显示图像
    img_temp = image.Image(640, 480, image.RGB565)
    img_temp.clear()
    img_temp.copy_from(img)
    
    # 绘制状态卡片
    draw_status_card(img_temp, 50, 150, 540, 180, title, 
                    f"步骤 {current_step}/{len(steps)}: {steps[current_step-1] if current_step > 0 else '准备中...'}", 
                    'info')
    
    # 绘制进度条
    draw_progress_bar(img_temp, 80, 280, 480, 30, progress)
    
    # 显示加载动画
    show_loading_animation(img_temp, 250, 350, int(time.ticks_ms() / 200))
    
    Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)

def enhanced_network_connection(ssid, key, img):
    """增强的网络连接，带进度显示"""
    steps = ["初始化网络", "搜索WiFi", "建立连接", "获取IP地址", "连接完成"]
    
    try:
        import network
        
        # 步骤1: 初始化网络
        show_progress_with_animation(img, "网络连接", steps, 1, 0.1)
        time.sleep_ms(500)
        
        sta = network.WLAN(0)
        sta.active(True)
        
        if sta.isconnected():
            show_progress_with_animation(img, "网络连接", steps, 5, 1.0)
            time.sleep_ms(1000)
            return sta.ifconfig()[0]
        
        # 步骤2: 搜索WiFi
        show_progress_with_animation(img, "网络连接", steps, 2, 0.3)
        time.sleep_ms(500)
        
        # 步骤3: 建立连接
        show_progress_with_animation(img, "网络连接", steps, 3, 0.5)
        sta.connect(ssid, key)
        
        # 步骤4: 等待连接
        timeout = 30
        while not sta.isconnected() and timeout > 0:
            progress = 0.5 + (30 - timeout) / 30 * 0.4  # 从50%到90%
            show_progress_with_animation(img, "网络连接", steps, 4, progress)
            time.sleep(1)
            timeout -= 1
        
        if sta.isconnected():
            # 步骤5: 连接完成
            show_progress_with_animation(img, "网络连接", steps, 5, 1.0)
            time.sleep_ms(1500)
            return sta.ifconfig()[0]
        else:
            raise Exception("WiFi连接超时")
            
    except Exception as e:
        # 显示错误状态
        img_temp = image.Image(640, 480, image.RGB565)
        img_temp.clear()
        img_temp.copy_from(img)
        draw_status_card(img_temp, 50, 200, 540, 100, "连接失败", str(e), 'error')
        Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
        time.sleep_ms(3000)
        return None

def enhanced_ai_analysis(api_key, image_path, prompt, img):
    """增强的AI分析，带进度显示"""
    steps = ["准备上传", "上传图片", "发送分析请求", "等待AI响应", "处理结果"]
    max_retries = 4  # 修改为4次重试
    
    # 第一次尝试显示正常进度
    for attempt in range(max_retries):
        try:
            if attempt == 0:
                # 第一次尝试显示正常进度条
                # 步骤1: 准备上传
                show_progress_with_animation(img, f"AI分析", steps, 1, 0.1)
                time.sleep_ms(500)
                
                # 步骤2: 上传图片
                show_progress_with_animation(img, f"AI分析", steps, 2, 0.3)
                temp_url = upload_image.upload_image_to_dashscope(api_key, image_path, "qwen-vl-max")
                
                # 步骤3: 发送分析请求
                show_progress_with_animation(img, f"AI分析", steps, 3, 0.6)
                time.sleep_ms(500)
                
                # 步骤4: 等待AI响应
                show_progress_with_animation(img, f"AI分析", steps, 4, 0.8)
                analysis_result = analyze_image_with_dashscope(api_key, temp_url, prompt)
                
                # 步骤5: 处理结果
                show_progress_with_animation(img, f"AI分析", steps, 5, 1.0)
                time.sleep_ms(1000)
                
                return analysis_result
            else:
                # 重试时直接执行，不显示进度条
                temp_url = upload_image.upload_image_to_dashscope(api_key, image_path, "qwen-vl-max")
                analysis_result = analyze_image_with_dashscope(api_key, temp_url, prompt)
                
                # 重试成功，显示成功界面
                img_temp = image.Image(640, 480, image.RGB565)
                img_temp.clear()
                img_temp.copy_from(img)
                draw_status_card(img_temp, 50, 200, 540, 100, 
                               "✅ 识别成功", "网络恢复正常，分析完成！", 'success')
                Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
                time.sleep_ms(1500)
                
                return analysis_result
                
        except Exception as e:
            error_str = str(e).lower()
            
            # 判断是否为需要重试的网络错误
            network_error_keywords = ['badstatusline', 'connection', 'timeout', 'network', 'socket', 'ssl', 'tls']
            is_network_error = any(keyword in error_str for keyword in network_error_keywords)
            
            # 判断是否为不应重试的配置错误
            config_error_keywords = ['invalidapikey', 'invalid api-key', 'unauthorized', 'forbidden', 'authentication', 'permission']
            is_config_error = any(keyword in error_str for keyword in config_error_keywords)
            
            if is_config_error:
                # 配置错误，直接显示错误信息，不重试
                img_temp = image.Image(640, 480, image.RGB565)
                img_temp.clear()
                img_temp.copy_from(img)
                
                # 提取关键错误信息
                if 'InvalidApiKey' in str(e) or 'Invalid API-key' in str(e):
                    error_message = "API密钥无效\n请检查配置文件中的API_KEY"
                elif 'unauthorized' in error_str or 'forbidden' in error_str:
                    error_message = "访问权限不足\n请检查API密钥权限"
                else:
                    error_message = f"配置错误\n{str(e)[:60]}..."
                
                draw_status_card(img_temp, 50, 200, 540, 120, 
                               "⚠️ 配置错误", error_message, 'error')
                Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
                time.sleep_ms(5000)  # 显示更长时间让用户看清错误
                raise
            
            elif is_network_error and attempt < max_retries - 1:
                # 网络错误且还有重试机会，显示友好的重试信息
                img_temp = image.Image(640, 480, image.RGB565)
                img_temp.clear()
                img_temp.copy_from(img)
                
                friendly_message = f"网络波动较大，正在努力为您识别_(:з」∠)_\n重试中... ({attempt + 1}/{max_retries})"
                
                draw_status_card(img_temp, 50, 200, 540, 120, 
                               "处理中", friendly_message, 'warning')
                Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
                
                # 在友好界面上等待一段时间，然后继续重试
                time.sleep_ms(2000)
                
                # 更新重试状态显示
                if attempt < max_retries - 2:  # 不是最后一次重试
                    img_temp2 = image.Image(640, 480, image.RGB565)
                    img_temp2.clear()
                    img_temp2.copy_from(img)
                    
                    retry_message = f"网络波动较大，正在努力为您识别_(:з」∠)_\n [{attempt + 2} / 4] "
                    draw_status_card(img_temp2, 50, 200, 540, 120, 
                                   "Trying...", retry_message, 'info')
                    Display.show_image(img_temp2, 0, 0, Display.LAYER_OSD2)
                    time.sleep_ms(1000)
            
            elif is_network_error and attempt >= max_retries - 1:
                # 网络错误但已达到最大重试次数
                img_temp = image.Image(640, 480, image.RGB565)
                img_temp.clear()
                img_temp.copy_from(img)
                draw_status_card(img_temp, 50, 200, 540, 120, 
                               "网络超时", f"已尝试 {max_retries} 次，请检查网络连接\n或稍后再试", 'error')
                Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
                time.sleep_ms(3000)
                raise
            
            else:
                # 其他未知错误，直接显示错误信息，不重试
                img_temp = image.Image(640, 480, image.RGB565)
                img_temp.clear()
                img_temp.copy_from(img)
                
                # 简化错误信息显示
                error_display = str(e)[:80] + "..." if len(str(e)) > 80 else str(e)
                
                draw_status_card(img_temp, 50, 200, 540, 120, 
                               "❌ 处理失败", f"发生错误:\n{error_display}", 'error')
                Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
                time.sleep_ms(4000)
                raise

def enhanced_display_analysis_result(img, result_text, duration=8000):
    """增强的分析结果显示，带美观UI"""
    try:
        # 智能文本处理
        processed_text = smart_text_processing(result_text)
        pages = split_text_to_pages(processed_text, max_lines_per_page=12, max_chars_per_line=32)
        
        for page_num, page_text in enumerate(pages):
            # 创建显示图像
            img_temp = image.Image(640, 480, image.RGB565)
            img_temp.clear()
            img_temp.copy_from(img)
            
            # 绘制结果卡片
            card_height = min(400, len(page_text.split('\n')) * 25 + 80)
            draw_status_card(img_temp, 20, 50, 600, card_height, 
                           f"AI分析结果 ({page_num + 1}/{len(pages)})", 
                           page_text, 'success')
            
            # 添加页面指示器
            if len(pages) > 1:
                indicator_y = card_height + 70
                # 绘制页面指示点
                for i in range(len(pages)):
                    dot_x = 300 + (i - len(pages)//2) * 20
                    dot_color = UI_COLORS['primary'] if i == page_num else UI_COLORS['text_dim']
                    img_temp.draw_circle(dot_x, indicator_y, 4, dot_color, fill=True)
                
                # 显示翻页提示
                if page_num < len(pages) - 1:
                    img_temp.draw_string_advanced(250, indicator_y + 20, 16, 
                                                "自动翻页中...", color=UI_COLORS['warning'])
                else:
                    img_temp.draw_string_advanced(270, indicator_y + 20, 16, 
                                                "显示完成", color=UI_COLORS['success'])
            
            Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
            
            # 每页显示时间
            page_duration = duration // len(pages) if len(pages) > 1 else duration
            page_duration = max(page_duration, 3000)  # 最少3秒
            time.sleep_ms(page_duration)
            
    except Exception as e:
        print(f"显示分析结果时出错: {e}")
        # 回退显示
        img_temp = image.Image(640, 480, image.RGB565)
        img_temp.clear()
        img_temp.copy_from(img)
        draw_status_card(img_temp, 50, 200, 540, 100, "显示完成", "详细结果请查看控制台", 'info')
        Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
        time.sleep_ms(duration)

def smart_text_processing(text):
    """智能文本处理，提取关键信息"""
    if len(text) <= 500:
        return text
    
    # 提取关键段落
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 保留重要信息行
        if any(keyword in line for keyword in ['描述', '场景', '主要', '重点', '总结', '包括', '显示', '可以看到']):
            # 简化长句
            if len(line) > 40:
                # 尝试在合适位置截断
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
    
    # 如果处理后还是太长，进一步简化
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
        # 处理超长行
        if len(line) > max_chars_per_line:
            # 按字符数分割长行
            while len(line) > max_chars_per_line:
                current_page.append(line[:max_chars_per_line])
                line = line[max_chars_per_line:]
                current_line_count += 1
                
                if current_line_count >= max_lines_per_page:
                    pages.append('\n'.join(current_page))
                    current_page = []
                    current_line_count = 0
            
            if line:  # 剩余部分
                current_page.append(line)
                current_line_count += 1
        else:
            current_page.append(line)
            current_line_count += 1
        
        # 检查是否需要新页
        if current_line_count >= max_lines_per_page:
            pages.append('\n'.join(current_page))
            current_page = []
            current_line_count = 0
    
    # 添加最后一页
    if current_page:
        pages.append('\n'.join(current_page))
    
    return pages if pages else ["无内容显示"]

def analyze_image_with_dashscope(api_key, image_url, prompt="图中描绘的是什么景象?"):
    """使用DashScope兼容模式API分析图片"""
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
        print(f"正在分析图片: {image_url}")
        print(f"分析提示: {prompt}")
        
        # 使用YbRequest库发送请求
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MicroPython-urequests",
            "X-DashScope-OssResourceResolve": "enable"
        }
        
        response = requests.post(url, headers=headers, json_data=data, timeout=60)
        print(f"分析响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"分析失败，响应内容: {response.text}")
            raise Exception(f"图片分析失败: {response.text}")
        
        result = response.json
        print("图片分析成功!")
        return result
        
    except Exception as e:
        print(f"图片分析错误: {e}")
        raise

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
    try:
        # 初始化按键
        key = YbKey.YbKey()

        # 构造传感器对象
        sensor = Sensor()
        sensor.reset()

        # 设置通道1的输出格式
        sensor.set_framesize(width=640, height=480, chn=CAM_CHN_ID_1)
        sensor.set_pixformat(Sensor.RGB565, chn=CAM_CHN_ID_1)

        Display.init(Display.ST7701, width=640, height=480, to_ide=True)

        # 初始化媒体管理器
        MediaManager.init()
        sensor.run()

        last_status = False
        
        print("=== 拍照+多模态识别系统启动 ===")
        print("按下按键进行拍照和AI分析")
        print("首次拍照时会自动连接WiFi")

        while True:
            # 捕获图像
            img = sensor.snapshot(chn=CAM_CHN_ID_1)
            
            # 创建显示用的图像缓冲
            img2 = image.Image(640, 480, image.RGB565)
            img2.clear()
            img2.copy_from(img)
            
            # 绘制美观的状态界面
            status_text = "🌐 已连接" if network_connected else "📶 未连接"
            connection_color = UI_COLORS['success'] if network_connected else UI_COLORS['warning']
            
            # 主状态卡片
            draw_status_card(img2, 20, 20, 600, 80, 
                           f"K230 & 场景分析 - 照片 {i}", 
                           f"网络状态: {status_text}\n按键进行拍照和AI分析", 'info')
            
            # 操作提示
            img2.draw_string_advanced(50, 420, 20, "按下按键开始拍照", color=UI_COLORS['primary'])
            img2.draw_string_advanced(50, 450, 16, "首次使用将自动连接WiFi", color=UI_COLORS['text_dim'])
            
            Display.show_image(img2, 0, 0, Display.LAYER_OSD2)

            # 按键检测和处理逻辑
            if key.is_pressed() == 1:
                if last_status == False:
                    last_status = True
                    
                    print(f"\n=== 开始处理第 {i} 张照片 ===")
                    
                    # 确保目录存在
                    ensure_dir(save_path + str(prefix) + "/")
                    
                    # 保存图片
                    image_path = save_path + str(prefix) + "/" + str(i) + ".jpg"
                    print(f"保存图片到: {image_path}")
                    img.save(image_path)
                    print("图片保存成功!")
                    
                    # 显示保存成功
                    img_temp = image.Image(640, 480, image.RGB565)
                    img_temp.clear()
                    img_temp.copy_from(img)
                    draw_status_card(img_temp, 50, 200, 540, 100, 
                                   "拍照成功", f"图片已保存: {i}.jpg", 'success')
                    Display.show_image(img_temp, 0, 0, Display.LAYER_OSD2)
                    time.sleep_ms(1500)
                    
                    # 如果还没连接网络，先连接
                    if not network_connected:
                        print("首次使用，正在连接WiFi...")
                        ip = enhanced_network_connection(WIFI_SSID, WIFI_KEY, img)
                        if ip:
                            network_connected = True
                            print("网络连接成功!")
                        else:
                            print("网络连接失败，跳过AI分析")
                            i += 1
                            time.sleep_ms(1000)
                            continue
                    
                    # 进行多模态分析
                    if network_connected:
                        try:
                            print("开始AI分析...")
                            result = enhanced_ai_analysis(API_KEY, image_path, 
                                                        "请用简洁的语言描述这张图片中的主要内容，控制在200字以内", img)
                            
                            # 提取分析结果
                            if 'choices' in result and len(result['choices']) > 0:
                                analysis_text = result['choices'][0]['message']['content']
                                print(f"\n=== AI分析结果 ===")
                                print(analysis_text)
                                
                                # 显示分析结果
                                enhanced_display_analysis_result(img, analysis_text, 8000)
                                
                            else:
                                print("AI分析结果格式异常")
                                print(f"完整响应: {result}")
                                
                        except Exception as e:
                            print(f"AI分析失败: {e}")
                    
                    i += 1
                    print(f"=== 第 {i-1} 张照片处理完成 ===\n")
                    time.sleep_ms(100)
            else:
                last_status = False
                
    except KeyboardInterrupt as e:
        print(f"用户停止程序")
    except BaseException as e:
        print(f"发生异常: '{e}'")
    finally:
        # 清理资源
        if isinstance(sensor, Sensor):
            sensor.stop()
        Display.deinit()
        uos.exitpoint(uos.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()