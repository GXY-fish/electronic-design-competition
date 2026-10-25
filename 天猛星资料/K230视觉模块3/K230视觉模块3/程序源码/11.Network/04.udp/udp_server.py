#配置 tcp/udp socket调试工具
import socket
import time,os
import network

WIFI_SSID="SSID"
WIFI_PASSWD="WIFI PASSWORD"

IP_ADDR_HOST="192.168.2.68"
IP_PORT=8081

def network_use_wlan():
    wifi=network.WLAN(network.STA_IF)
    wifi.connect(WIFI_SSID, WIFI_PASSWD)
    while wifi.ifconfig()[0] == '0.0.0.0':
        os.exitpoint()
    ip = wifi.ifconfig()[0]
    print("IP Address:", ip)
    return ip

def udpserver():
    #获取lan接口
    IP_ADDR=network_use_wlan()
    IP_PORT=8081
    
    network_use_wlan()

    #获取地址及端口号对应地址
    ai = socket.getaddrinfo(IP_ADDR, IP_PORT)
    print("Address infos:", ai)
    IP_ADDR = ai[0][-1]

    print("udp server %s port:%d\n" % ((IP_ADDR), IP_PORT))
    #建立socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #设置属性
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #绑定
    s.bind(("0.0.0.0", IP_PORT))
    #延时
    time.sleep(1)

    counter=0
    while True:
        os.exitpoint()
        data, addr = s.recvfrom(10)
        if data == b"":
            continue
        print("recv %d" % counter,data,addr)
        #回复内容
        s.sendto(b"%s have recv count=%d " % (data,counter), (IP_ADDR_HOST, IP_PORT))
        counter = counter+1
        if counter > 10 :
            break
    #关闭
    s.close()
    print("udp server exit!!")


udpserver()
