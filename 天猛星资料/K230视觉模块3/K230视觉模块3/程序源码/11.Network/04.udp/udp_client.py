import socket
import os
import time
import network

def connect_wifi(ssid="[WIFI SSID]", password="[WIFI PASSWORD]"):
    """
    连接WiFi并返回IP地址
    Connect to WiFi and return IP address
    
    参数 / Parameters:
    ssid: WiFi名称 / WiFi name
    password: WiFi密码 / WiFi password
    
    返回 / Returns:
    str: IP地址 / IP address
    """
    wifi_station = network.WLAN(0)  # 创建WiFi站点对象 / Create WiFi station object
    wifi_station.connect(ssid, password)  # 连接到指定WiFi / Connect to specified WiFi
    
    # 等待直到获取到IP地址 / Wait until IP address is obtained
    while wifi_station.ifconfig()[0] == '0.0.0.0':
        os.exitpoint()
    return wifi_station.ifconfig()[0]  # 返回IP地址 / Return IP address

def start_udp_client():
    """
    启动UDP客户端，发送测试消息
    Start UDP client and send test messages
    """
    # 连接WiFi网络 / Connect to WiFi network
    connect_wifi()
    
    # 设置服务器参数 / Set server parameters
    server_ip = '192.168.2.89'
    server_port = 8080
    
    # 获取服务器地址信息 / Get server address information
    address_info = socket.getaddrinfo(server_ip, server_port)
    print("地址信息 / Address info:", address_info)
    
    server_address = address_info[0][-1]
    print("连接地址 / Connect address:", server_address)
    
    # 创建UDP套接字 / Create UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # 发送测试消息 / Send test messages
    try:
        for msg_count in range(10):
            # 构建消息 / Build message
            message = f"K230 UDP client send test {msg_count}\r\n"
            print("发送消息 / Sending:", message)
            
            # 发送消息并获取发送字节数 / Send message and get bytes sent
            bytes_sent = udp_socket.sendto(message.encode(), server_address)
            print("发送字节数 / Bytes sent:", bytes_sent)
            
            # 等待200ms / Wait 200ms
            time.sleep(0.2)
            
    finally:
        # 关闭套接字 / Close socket
        udp_socket.close()
        print("客户端已结束 / Client ended.")

# 启动客户端 / Start client
if __name__ == '__main__':
    start_udp_client()