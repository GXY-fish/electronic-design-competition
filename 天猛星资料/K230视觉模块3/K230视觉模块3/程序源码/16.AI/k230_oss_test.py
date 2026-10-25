"""
K230版本OSS上传测试程序
适配MicroPython环境，测试OSS上传功能的稳定性
"""

import uos
import time
import network
import libs.upload_image as upload_image

# 配置信息
API_KEY = ""  # DashScope API密钥
MODEL_NAME = "qwen-audio-turbo"  # 模型名称

# WiFi配置 填写正确的WiFi SSID和密钥
WIFI_SSID = ""
WIFI_KEY = ""

# 测试音频文件路径（K230上的路径）
TEST_AUDIO_FILE = "/data/recorded_audio_263794.wav"

def print_with_time(message):
    """带时间戳的打印函数"""
    current_time = time.ticks_ms()
    print(f"[{current_time}ms] {message}")

def connect_wifi():
    """连接WiFi网络"""
    print_with_time("开始连接WiFi...")
    
    # 创建WLAN对象
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # 检查是否已连接
    if wlan.isconnected():
        print_with_time(f"WiFi已连接: {wlan.ifconfig()}")
        return True
    
    # 连接WiFi
    print_with_time(f"正在连接WiFi: {WIFI_SSID}")
    wlan.connect(WIFI_SSID, WIFI_KEY)
    
    # 等待连接
    max_wait = 20  # 最大等待20秒
    wait_count = 0
    
    while not wlan.isconnected() and wait_count < max_wait:
        print_with_time(f"等待WiFi连接... ({wait_count + 1}/{max_wait})")
        time.sleep(1)
        wait_count += 1
    
    if wlan.isconnected():
        print_with_time(f"WiFi连接成功! IP地址: {wlan.ifconfig()[0]}")
        return True
    else:
        print_with_time("WiFi连接失败!")
        return False

def check_file_exists(file_path):
    """检查文件是否存在"""
    try:
        with open(file_path, 'rb') as f:
            file_size = 0
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                file_size += len(chunk)
        print_with_time(f"测试文件存在: {file_path}, 大小: {file_size} 字节")
        return True, file_size
    except Exception as e:
        print_with_time(f"测试文件不存在或无法读取: {file_path}, 错误: {e}")
        return False, 0

def upload_audio_test(file_path, test_number):
    """单次音频上传测试"""
    print_with_time(f"=== 开始第 {test_number} 次上传测试 ===")
    
    start_time = time.ticks_ms()
    
    try:
        # 调用上传函数
        oss_url = upload_image.upload_image_to_dashscope(API_KEY, file_path, MODEL_NAME)
        
        end_time = time.ticks_ms()
        upload_time = time.ticks_diff(end_time, start_time) / 1000.0  # 转换为秒
        
        print_with_time(f"第 {test_number} 次上传成功!")
        print_with_time(f"上传时间: {upload_time:.2f}秒")
        print_with_time(f"OSS地址: {oss_url}")
        
        return True, upload_time, None
        
    except Exception as e:
        end_time = time.ticks_ms()
        upload_time = time.ticks_diff(end_time, start_time) / 1000.0
        
        error_msg = str(e)
        print_with_time(f"第 {test_number} 次上传失败!")
        print_with_time(f"失败时间: {upload_time:.2f}秒")
        print_with_time(f"错误信息: {error_msg}")
        
        return False, upload_time, error_msg

def run_multiple_upload_tests(file_path, test_count=10):
    """运行多次上传测试"""
    print_with_time(f"=== 开始 {test_count} 次OSS上传测试 ===")
    
    # 统计变量
    success_count = 0
    fail_count = 0
    total_time = 0
    upload_times = []
    error_messages = []
    
    # 执行测试
    for i in range(1, test_count + 1):
        success, upload_time, error_msg = upload_audio_test(file_path, i)
        
        total_time += upload_time
        upload_times.append(upload_time)
        
        if success:
            success_count += 1
        else:
            fail_count += 1
            if error_msg:
                error_messages.append(f"测试{i}: {error_msg}")
        
        # 测试间隔
        if i < test_count:
            print_with_time("等待1秒后进行下一次测试...")
            time.sleep(1)
    
    # 计算统计信息
    success_rate = (success_count / test_count) * 100
    avg_time = total_time / test_count
    min_time = min(upload_times) if upload_times else 0
    max_time = max(upload_times) if upload_times else 0
    
    # 输出统计结果
    print_with_time("")
    print_with_time("=== 测试结果统计 ===")
    print_with_time(f"总测试次数: {test_count}")
    print_with_time(f"成功次数: {success_count}")
    print_with_time(f"失败次数: {fail_count}")
    print_with_time(f"成功率: {success_rate:.1f}%")
    print_with_time(f"平均上传时间: {avg_time:.2f}秒")
    print_with_time(f"最快上传时间: {min_time:.2f}秒")
    print_with_time(f"最慢上传时间: {max_time:.2f}秒")
    print_with_time(f"总耗时: {total_time:.2f}秒")
    
    # 输出错误信息
    if error_messages:
        print_with_time("")
        print_with_time("=== 错误详情 ===")
        for error in error_messages:
            print_with_time(error)
    
    return success_count, fail_count, success_rate

def main():
    """主函数"""
    print_with_time("=== K230 OSS上传测试程序启动 ===")
    
    # 1. 连接WiFi
    if not connect_wifi():
        print_with_time("WiFi连接失败，程序退出")
        return
    
    # 2. 检查测试文件
    file_exists, file_size = check_file_exists(TEST_AUDIO_FILE)
    if not file_exists:
        print_with_time("测试文件不存在，程序退出")
        return
    
    # 3. 运行上传测试
    try:
        success_count, fail_count, success_rate = run_multiple_upload_tests(TEST_AUDIO_FILE, 10)
        
        print_with_time("")
        print_with_time("=== 测试完成 ===")
        if success_rate >= 80:
            print_with_time("✅ 测试结果良好，OSS上传功能正常")
        elif success_rate >= 50:
            print_with_time("⚠️  测试结果一般，OSS上传可能存在网络问题")
        else:
            print_with_time("❌ 测试结果较差，OSS上传存在严重问题")
            
    except Exception as e:
        print_with_time(f"测试程序异常: {e}")
    
    print_with_time("=== K230 OSS上传测试程序结束 ===")

if __name__ == "__main__":
    main()