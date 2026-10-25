import network                          # 导入网络模块，用于处理WiFi连接 / Import network module for handling WiFi connections
import os                              # 导入操作系统模块，提供系统相关功能 / Import os module for system-related functions
import time                            # 导入时间模块，用于延时操作 / Import time module for delay operations

WIFI_SSID = "WIFI SSID"              # WiFi网络名称（SSID） / WiFi network name (SSID)
WIFI_PASSWD = "WIFI PASSWORD"        # WiFi网络密码 / WiFi network password

print("[INFO] 连接网络中 ... Connecting ...")          # 打印信息，表示正在连接网络 / Print info indicating network connection in progress
wifi = network.WLAN(network.STA_IF)    # 创建WLAN对象，设置为STA模式（客户端模式） / Create WLAN object, set to STA mode (client mode)

# STA模式连接到指定的WiFi接入点（AP） / Connect to the specified WiFi access point (AP) in STA mode
wifi.connect(WIFI_SSID, WIFI_PASSWD)   # 使用SSID和密码连接WiFi / Connect to WiFi using SSID and password

# 查看STA模式的WiFi连接状态 / Check the WiFi connection status in STA mode
print("WIFI status:", wifi.status())   # 打印WiFi状态码 / Print WiFi status code

# 等待直到获取到有效的IP地址 / Wait until a valid IP address is obtained
while wifi.ifconfig()[0] == '0.0.0.0': # 检查IP地址是否为'0.0.0.0'（未分配IP） / Check if IP address is '0.0.0.0' (unassigned IP)
    os.exitpoint()                     # 检查是否有退出信号，允许外部中断 / Check for exit signal, allowing external interruption

# 查看并打印IP配置信息 / View and print IP configuration information
print("My IP:", wifi.ifconfig()[0])    # 打印当前设备的IP地址 / Print the current device's IP address
# 查看WiFi是否已连接 / Check if WiFi is connected
print("WIFI isconnected:", wifi.isconnected())  # 打印WiFi连接状态（True表示已连接） / Print WiFi connection status (True means connected)

time.sleep(5)                          # 延时5秒，等待网络稳定或观察状态 / Delay for 5 seconds to stabilize the network or observe status

# 断开WiFi连接 / Disconnect from WiFi
wifi.disconnect()                      # 断开当前WiFi连接 / Disconnect the current WiFi connection
# 查看断开后的STA状态 / Check STA status after disconnection
print("WIFI status:", wifi.status())   # 打印断开后的WiFi状态码 / Print WiFi status code after disconnection
print("WIFI isconnected:", wifi.isconnected())  # 打印断开后的连接状态 / Print connection status after disconnection