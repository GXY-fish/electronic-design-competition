# 导入FPIOA类 (Import FPIOA class from machine module)
from machine import FPIOA

# 实例化FPIOA (Initialize FPIOA object)
fpioa = FPIOA()

# 打印所有引脚配置 (Print all pin configurations)
fpioa.help()

# 打印指定引脚详细配置 (Print detailed configuration for a specific pin)
fpioa.help(0)

# 打印指定功能所有可用的配置引脚 (Print all available pins for a specific function)
fpioa.help(FPIOA.IIC0_SDA, func=True)

# 获取指定功能当前所在的引脚 (Get the current pin number for a specific function)
fpioa.get_pin_num(FPIOA.UART0_TXD)

# 获取指定引脚当前功能 (Get the current function of a specific pin)
fpioa.get_pin_func(0)
