from machine import PWM
import time


# 实例化PWM通道0，频率为1000Hz，占空比为50%，默认使能输出
# Instantiate PWM channel 0 with a frequency of 1000Hz, a duty cycle of 50%, and enable the output by default
pwm0 = PWM(42,freq=1000,duty=50)


# 实例化PWM通道1，频率为1000Hz，占空比为50%，默认使能输出
# Instantiate PWM channel 1 with a frequency of 1000Hz, a duty cycle of 50%, and enable the output by default
pwm1 = PWM(43,freq=1000,duty=50)
pwm1.duty(0)

# 调整通道1频率为1000Hz
# Adjust the frequency of Channel 1 to 1000Hz
pwm1.freq(1000)
# 调整通道1占空比为80%
# Adjust the duty cycle of Channel 1 to 80%
pwm1.duty(80)

# 阻止程序退出
# Prevent the program from exiting
while True:
    time.sleep(1)
