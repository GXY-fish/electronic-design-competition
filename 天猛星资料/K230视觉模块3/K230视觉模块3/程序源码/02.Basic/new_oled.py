import framebuf


# register definitions
SET_CONTRAST        = const(0x81)
SET_ENTIRE_ON       = const(0xa4)
SET_NORM_INV        = const(0xa6)
SET_DISP            = const(0xae)
SET_MEM_ADDR        = const(0x20)
SET_COL_ADDR        = const(0x21)
SET_PAGE_ADDR       = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP       = const(0xa0)
SET_MUX_RATIO       = const(0xa8)
SET_COM_OUT_DIR     = const(0xc0)
SET_DISP_OFFSET     = const(0xd3)
SET_COM_PIN_CFG     = const(0xda)
SET_DISP_CLK_DIV    = const(0xd5)
SET_PRECHARGE       = const(0xd9)
SET_VCOM_DESEL      = const(0xdb)
SET_CHARGE_PUMP     = const(0x8d)


class SSD1306:
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        # Note the subclass must initialize self.framebuf to a framebuffer.
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00, # off
            # address setting
            SET_MEM_ADDR, 0x00, # horizontal
            # resolution and layout
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01, # column addr 127 mapped to SEG0
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08, # scan from COM[N] to COM0
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x02 if self.height == 32 else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0x22 if self.external_vcc else 0xf1,
            SET_VCOM_DESEL, 0x30, # 0.83*Vcc
            # display
            SET_CONTRAST, 0xff, # maximum
            SET_ENTIRE_ON, # output follows RAM contents
            SET_NORM_INV, # not inverted
            # charge pump
            SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01): # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_framebuf()

    def fill(self, col):
        self.framebuf.fill(col)

    def pixel(self, x, y, c=None):
        if c is None:
            return self.framebuf.pixel(x, y)
        else:
            self.framebuf.pixel(x, y, c)

    def scroll(self, dx, dy):
        self.framebuf.scroll(dx, dy)

    def text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, col)

    def text_line(self, string, line=1):
        line = int(line)
        if line >= 1 and line <= 4:
            self.framebuf.text(string, 0, 8*(line-1), 1)
        else:
            self.framebuf.text(string, 0, 0, 1)


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3c):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        # Add an extra byte to the data buffer to hold an I2C data/command byte
        # to use hardware-compatible I2C transactions.  A memoryview of the
        # buffer is used to mask this byte from the framebuffer operations
        # (without a major memory hit as memoryview doesn't copy to a separate
        # buffer).
        self.buffer = bytearray(((height // 8) * width) + 1)
        self.buffer[0] = 0x40  # Set first byte of data buffer to Co=0, D/C=1
        self.framebuf = framebuf.FrameBuffer(memoryview(self.buffer)[1:], width, height, framebuf.MONO_VLSB)
        time.sleep(0.2)
        super().__init__(width, height, False)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        for retry in range(5):  # 增加重试次数到5次
            try:
                self.i2c.writeto(self.addr, self.temp)
                return
            except OSError as e:
                print(f"retry:{retry}")
                if retry == 4:  # 最后一次重试失败
                    print(f"写入命令 0x{cmd:02x} 失败，重试 {retry+1} 次后仍然失败")
                    raise e
                time.sleep(0.01)  # 等待10ms后重试

    def write_framebuf(self):
        # 分块发送数据，避免一次发送太多数据
        chunk_size = 32  # 每次发送32字节
        for i in range(0, len(self.buffer), chunk_size):
            chunk = self.buffer[i:i+chunk_size]
            for retry in range(3):
                try:
                    if i == 0:
                        # 第一块包含命令字节
                        self.i2c.writeto(self.addr, chunk)
                    else:
                        # 后续块需要添加数据命令字节
                        data_chunk = bytearray([0x40]) + chunk
                        self.i2c.writeto(self.addr, data_chunk)
                    break
                except OSError as e:
                    print(f"write_framebuf retry {write_framebuf}")
                    if retry == 2:
                        print(f"写入帧缓冲区块 {i} 失败")
                        raise e
                    time.sleep(0.01)

if __name__ == "__main__":
    from machine import I2C,FPIOA
    import time
    fpioa = FPIOA()
    fpioa.set_function(9, FPIOA.IIC1_SCL, oe=1, ie=1, pu=1, st=1, ds=15)
    fpioa.set_function(10, FPIOA.IIC1_SDA, oe=1, ie=1, pu=1, st=1, ds=15)
    i2c = I2C(1, scl=9, sda=10, freq=40000)

    print("扫描I2C设备...")
    devices = i2c.scan()
    print("发现的设备地址:", [hex(device) for device in devices])

    if not devices:
        print("错误: 未发现任何I2C设备")
        raise
#        exit()

    # 检查OLED地址
    oled_addr = 0x3c
    if oled_addr not in devices:
        print(f"未找到OLED")
        # 尝试常见的OLED地址
        if 0x3d in devices:
            oled_addr = 0x3d
            print(f"找到OLED，使用地址: {hex(oled_addr)}")
        elif devices:
            oled_addr = devices[0]
            print(f"尝试使用第一个发现的设备地址: {hex(oled_addr)}")
    else:
        print(f"找到OLED，地址: {hex(oled_addr)}")

    try:
        # 创建 SSD1306 OLED 显示器实例
        oled = SSD1306_I2C(128, 32, i2c, addr=oled_addr)
        print("OLED初始化成功")

        # 清除 OLED 显示器的内容
        oled.fill(0)

        # 在 OLED 显示器上显示文字
        oled.text('Hello Yahboom', 0, 10)

        # 遍历 OLED 显示器的所有像素
        for x in range(128):
            for y in range(32):
                a = oled.pixel(x, y)
                if a == 1:
                    print(x, y)

        # 更新 OLED 显示器的内容
        oled.show()
        print("显示更新完成")

    except Exception as e:
        print(f"OLED操作失败: {e}")
