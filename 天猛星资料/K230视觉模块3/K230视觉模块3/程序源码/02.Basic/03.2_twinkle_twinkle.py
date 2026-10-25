# 导入蜂鸣器库 (Import buzzer library)
from ybUtils.YbBuzzer import YbBuzzer
# 导入时间库 (Import time library)
import time

# 创建蜂鸣器实例 (Create buzzer instance)
buzzer = YbBuzzer()

# 定义音符频率（Hz）(Define note frequencies in Hz)
C5 = 523  # 1 - 中央C (Middle C)
D5 = 587  # 2 - 中央D (Middle D)
E5 = 659  # 3 - 中央E (Middle E)
F5 = 698  # 4 - 中央F (Middle F)
G5 = 784  # 5 - 中央G (Middle G)
A5 = 880  # 6 - 中央A (Middle A)
B5 = 988  # 7 - 中央B (Middle B)

# 定义音符持续时间 (Define note duration)
BEAT = 0.3  # 一拍的时间（单位：秒）(Duration of one beat in seconds)

# 演奏旋律 (Play melody)
def play_twinkle():
    """
    演奏《一闪一闪亮晶晶》(小星星)的旋律
    (Play the melody of "Twinkle Twinkle Little Star")
    """
    # 一闪一闪亮晶晶的音符序列 (Note sequence for "Twinkle Twinkle Little Star")
    notes = [
        (C5, BEAT), (C5, BEAT), (G5, BEAT), (G5, BEAT),  # 1 1 5 5 (音乐简谱：小星星)
        (A5, BEAT), (A5, BEAT), (G5, BEAT*2),            # 6 6 5- (亮晶晶)
        (F5, BEAT), (F5, BEAT), (E5, BEAT), (E5, BEAT),  # 4 4 3 3 (满天都是)
        (D5, BEAT), (D5, BEAT), (C5, BEAT*2),            # 2 2 1- (小星星)
    ]

    # 遍历音符列表并演奏 (Iterate through the notes list and play)
    for freq, duration in notes:
        # 播放当前音符 (Play current note)
        # 参数：频率、音量50%、持续时间 (Parameters: frequency, volume 50%, duration)
        buzzer.on(freq, 50, duration)
        # 音符之间的短暂停顿，增加清晰度 (Brief pause between notes for clarity)
        time.sleep(0.1)

    # 结束后关闭蜂鸣器 (Turn off the buzzer after playing)
    buzzer.off()

# 程序入口点 (Program entry point)
if __name__ == "__main__":
    # 调用函数演奏旋律 (Call function to play the melody)
    play_twinkle()
