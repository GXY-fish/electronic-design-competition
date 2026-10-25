import socket      # 导入socket模块，用于网络通信 / Import socket module for network communication
import network    # 导入network模块，用于WiFi连接 / Import network module for WiFi connection
import os         # 导入os模块，用于系统操作 / Import os module for system operations
import time       # 导入time模块，用于时间相关操作 / Import time module for time-related operations

def connect_wifi():
    """
    连接WiFi并返回IP地址
    Connect to WiFi and return IP address
    """
    sta = network.WLAN(0)  # 创建WiFi站点对象 / Create WiFi station object
    sta.connect("WIFI SSID", "WIFI PASSWORD")  # 连接到指定WiFi / Connect to specified WiFi
    # 等待直到获取到IP地址 / Wait until IP address is obtained
    while sta.ifconfig()[0] == '0.0.0.0':
        os.exitpoint()
    return sta.ifconfig()[0]  # 返回IP地址 / Return IP address

def close_client(client):
    """
    关闭客户端连接
    Close client connection
    """
    client.close()  # 关闭连接 / Close connection
    print("等待连接 ... Waiting for connect")

def run_server():
    """
    运行TCP服务器的主函数
    Main function to run TCP server
    """
    # 连接WiFi并获取IP地址 / Connect to WiFi and get IP address
    ip = connect_wifi()

    # 创建TCP服务器 / Create TCP server
    server = socket.socket()
    server.setblocking(False) # 设置非阻塞模式 / Set non-blocking mode
    # 设置端口复用 / Set port reuse
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 绑定IP和端口 / Bind IP and port
    server.bind((ip, 8080))
    # 开始监听，最大连接数为5 / Start listening, maximum 5 connections
    server.listen(5)
    print(f"TCP server running on {ip}:8080")

    while True:
        # 等待客户端连接 / Wait for client connection
        try:
            client, addr = server.accept()
        except OSError as e:
            if e.args[0] == 11: # EAGAIN
                time.sleep(0.1)
                continue
            raise e
        print(f"Client connected: {addr}")
        # 设置非阻塞模式 / Set non-blocking mode
        client.setblocking(False)

        # 发送欢迎消息 / Send welcome message
        client.write(f"Hello!\n".encode())

        while True:
            # 处理接收数据 / Handle received data
            try:
                data = client.read()
                if data:
                    print(data)
                    # 发送确认消息 / Send acknowledgment
                    client.write(b"recv: " + data)
                # 如果收到结束命令，关闭连接 / If end command received, close connection
                if b"end" in data:
                    close_client(client)
                    break
            except:
                pass

    # 关闭服务器 / Close server
    server.close()
    print("Server stopped")

# 启动服务器 / Start server
run_server()