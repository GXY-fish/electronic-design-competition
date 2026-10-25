# 导入必要的模块 / Import required modules
from ybUtils.mqtt import MQTTClient  # 导入MQTT客户端模块 / Import MQTT client module
import network  # 导入网络模块，用于WiFi连接 / Import network module for WiFi connection
import os      # 导入操作系统模块 / Import operating system module
import machine # 导入硬件控制模块 / Import hardware control module
import time    # 导入时间模块，用于延时操作 / Import time module for delays

# WiFi配置参数 / WiFi configuration parameters
WIFI_SSID = "WIFI SSID"          # WiFi名称 / WiFi name
WIFI_PASSWORD = "WIFI PASSWORD" # WiFi密码 / WiFi password

# MQTT服务器配置参数 / MQTT server configuration parameters
MQTT_BROKER = "broker.emqx.io"  # MQTT服务器地址 / MQTT broker address
MQTT_PORT = 1883                # MQTT服务器端口 / MQTT broker port
MQTT_TOPIC = "yahboom/topic"    # MQTT主题 / MQTT topic

def connect_wifi(ssid, password):
    """
    连接WiFi并返回IP地址
    Connect to WiFi and return IP address

    参数 / Parameters:
    ssid: WiFi名称 / WiFi name
    password: WiFi密码 / WiFi password

    返回 / Returns:
    str: IP地址 / IP address
    """
    print(f"连接WIFI: {ssid}.. Connecting..")
    # 创建WiFi站点对象 / Create WiFi station object
    wifi_station = network.WLAN(0)
    # 连接到指定WiFi / Connect to specified WiFi
    wifi_station.connect(ssid, password)

    # 等待直到获取到IP地址 / Wait until IP address is obtained
    while wifi_station.ifconfig()[0] == '0.0.0.0':
        os.exitpoint()
    print("WIFI连接成功 WIFI Connected!")
    # 返回IP地址 / Return IP address
    return wifi_station.ifconfig()[0]

# 主程序入口 / Main program entry
if __name__ == "__main__":

    # 连接WiFi网络 / Connect to WiFi network
    connect_wifi(WIFI_SSID, WIFI_PASSWORD)

    # 创建MQTT客户端实例 / Create MQTT client instance
    # 参数包括客户端ID、服务器地址和端口 / Parameters include client ID, broker address and port
    client = MQTTClient("YAHBOOM-K230", MQTT_BROKER, port=MQTT_PORT)

    # 连接到MQTT服务器 / Connect to MQTT broker
    client.connect()

    # 循环发送100条消息 / Send 100 messages in a loop
    for i in range(100):
        # 发布消息到指定主题 / Publish message to specified topic
        client.publish(MQTT_TOPIC, "Hello Yahboom! " + str(i))
        # 延时500毫秒 / Delay 500 milliseconds
        time.sleep_ms(500)

    # 断开与MQTT服务器的连接 / Disconnect from MQTT broker
    client.disconnect()
