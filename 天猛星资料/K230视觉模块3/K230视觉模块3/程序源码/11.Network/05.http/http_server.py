# 导入必要的模块 Import required modules
import socket  # 用于网络通信 For network communication
import network  # 用于WiFi连接 For WiFi connection
import time, os  # 用于时间操作和系统功能 For time operations and system functions

# HTTP响应内容,包含HTML页面 HTTP response content containing HTML page
CONTENT = b"""\
HTTP/1.0 200 OK\r\n\
Content-Type: text/html; charset=utf-8\r\n\
\r\n\
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <title>亚博智能K230</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f0f0f0;
            }
            h1 {
                color: #333;
                text-align: center;
            }
            h2 {
                color: #222;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>欢迎使用亚博智能 K230</h1>
        <h2>Welcome to yahboom K230</h2>
    </body>
</html>
"""

# 连接WiFi的函数 Function to connect to WiFi
def Connect_WIFI(SSID,KEY):
    # 创建WLAN对象 Create WLAN object
    sta = network.WLAN(0)
    # 连接到指定的WiFi Connect to specified WiFi
    sta.connect(SSID,KEY)
    print(sta.status())
    # 等待直到获取到IP地址 Wait until IP address is obtained
    while sta.ifconfig()[0] == '0.0.0.0':
        os.exitpoint()
    # 打印网络配置信息 Print network configuration
    print(sta.ifconfig())
    # 返回IP地址 Return IP address
    ip = sta.ifconfig()[0]
    return ip

# 主函数 Main function
def main(micropython_optimize=True):
    # 连接WiFi并获取IP Connect to WiFi and get IP
    ip = Connect_WIFI("WIFI SSID", "WIFI PASSWORD")
    
    # 创建socket对象 Create socket object
    s = socket.socket()
    # 获取地址信息 Get address information
    ai = socket.getaddrinfo("0.0.0.0", 8081)
    addr = ai[0][-1]
    # 设置socket选项 Set socket options
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 绑定地址 Bind address
    s.bind(addr)
    # 开始监听 Start listening
    s.listen(5)
    s.setblocking(False)
    print("Listening, connect your browser to http://%s:8081/" % (ip))

    counter = 0
    # 主循环处理客户端连接 Main loop to handle client connections
    while True:
        # 接受客户端连接 Accept client connection
        try:
            res = s.accept()
        except OSError as e:
            if e.args[0] == 11:
                time.sleep(0.1)
                continue
            raise e
        client_sock = res[0]
        client_addr = res[1]
        print("Client address:", client_addr)
        # 设置非阻塞模式 Set non-blocking mode
        client_sock.setblocking(False)
        # 获取客户端流 Get client stream
        client_stream = client_sock if micropython_optimize else client_sock.makefile("rwb")

        # 读取HTTP请求头 Read HTTP request headers
        while True:
            h = client_stream.read()
            if h is None or h==b'':
                continue
            print(h)
            if h.endswith(b'\r\n\r\n'):
                break
            os.exitpoint()

        # 发送响应内容 Send response content
        client_stream.write(CONTENT)
        # 关闭客户端连接 Close client connection
        client_stream.close()

# 运行主函数 Run main function
main()