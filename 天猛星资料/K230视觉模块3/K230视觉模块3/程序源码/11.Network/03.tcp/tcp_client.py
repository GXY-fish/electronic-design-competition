# MicroPython TCP Client Implementation
# MicroPython TCP客户端实现

import network  # For WiFi functionality / 用于WiFi功能
import socket  # For TCP/IP communications / 用于TCP/IP通信
import os      # For system functions / 用于系统功能
import time    # For adding delays / 用于添加延时

def connect_wifi(ssid, password):
    """
    Connect to WiFi network with given SSID and password
    连接到指定SSID和密码的WiFi网络
    
    Args:
        ssid: WiFi network name / WiFi网络名称
        password: WiFi password / WiFi密码
    
    Returns:
        str: IP address if connected successfully / 连接成功时返回IP地址
    """
    # Initialize WiFi in station mode / 初始化WiFi站点模式
    wifi = network.WLAN(network.STA_IF)
    
    # Connect to WiFi network / 连接WiFi网络
    wifi.connect(ssid, password)
    
    # Wait for connection with timeout / 等待连接,带超时
    retry_count = 0
    while not wifi.isconnected() and retry_count < 10:
        print("Connecting to WiFi... / 正在连接WiFi...")
        time.sleep(1)
        retry_count += 1
    
    if wifi.isconnected():
        ip = wifi.ifconfig()[0]
        print(f"Connected! IP: {ip} / 已连接! IP地址: {ip}")
        return ip
    else:
        print("Failed to connect / 连接失败")
        return None

def run_tcp_client():
    """
    Run TCP client to send test messages
    运行TCP客户端发送测试消息
    """
    # Connect to WiFi first / 首先连接WiFi
    if not connect_wifi("[Your SSID]", "[Your PASSWORD]"):
        return
    
    # Create TCP socket / 创建TCP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Server details / 服务器详情
    server_ip = "[改成NetAssist里的本地主机地址]"
    server_port = 8080
    
    try:
        # Connect to server / 连接到服务器
        print(f"Connecting to {server_ip}:{server_port} / 正在连接到 {server_ip}:{server_port}")
        sock.connect((server_ip, server_port))
        
        # Send test messages / 发送测试消息
        for i in range(10):
            message = f"K230 TCP client test message {i}\r\n"
            print(f"Sending message {i} / 正在发送消息 {i}")
            sock.send(message.encode())
            time.sleep(0.2)  # Small delay between messages / 消息间的小延时
            
    except Exception as e:
        print(f"Error occurred: {e} / 发生错误: {e}")
        
    finally:
        # Always close the socket / 始终关闭套接字
        sock.close()
        print("Connection closed / 连接已关闭")

# Start the client / 启动客户端
if __name__ == "__main__":
    run_tcp_client()