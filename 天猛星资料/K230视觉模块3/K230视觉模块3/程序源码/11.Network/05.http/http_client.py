import network
import socket
import os, time

HOST = "www.baidu.com"

def Connect_WIFI(ssid, key):
    """
    使用 WLAN 连接网络。
    Connect to a WLAN network.

    :param ssid: WLAN 网络的 SSID
    :param key: WLAN 网络的密钥
    :return: 网络接口的 IP 地址
    """
    sta = network.WLAN(0)
    sta.connect(ssid, key)
    while not sta.isconnected():
        time.sleep(1)
    return sta.ifconfig()[0]

def main(use_stream=True):
    """
    主要函数，完成以下步骤:
    1. 连接 WLAN 网络
    2. 创建 socket
    3. 获取主机地址和端口号
    4. 连接到主机
    5. 发送 HTTP GET 请求并打印响应

    The main function that does the following:
    1. Connect to a WLAN network
    2. Create a socket
    3. Get the host address and port number
    4. Connect to the host
    5. Send an HTTP GET request and print the response

    :param use_stream: 是否使用流式 socket 进行读取
    """
    global HOST
    Connect_WIFI("WIFI SSID", "WIFI PASSWORD")

    s = socket.socket()

    ai = []
    for attempt in range(0, 3):
        try:
            ai = socket.getaddrinfo(HOST, 80)
            break
        except Exception as e:
            print("getaddrinfo again", e)

    if ai == []:
        print("连接错误 Connect error")
        s.close()
        return

    addr = ai[0][-1]
    print("连接地址 address:", addr)

    s.connect(addr)

    if use_stream:
        s = s.makefile("rwb", 0)
        s.write(b"GET /index.html HTTP/1.0\r\n\r\n")
        print(s.read())
    else:
        s.send(b"GET /index.html HTTP/1.0\r\n\r\n")
        print(s.recv(4096))

    s.close()

main()