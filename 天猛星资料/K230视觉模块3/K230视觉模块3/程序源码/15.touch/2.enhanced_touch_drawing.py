# Enhanced Touch Drawing Application - Fixed Version
# 增强版触摸绘画应用程序 - 修复版本
# 功能：多颜色绘画、画笔粗细调节、清屏等

import time, os, sys
from media.display import *
from media.media import *
from machine import TOUCH

# Initialize touch sensor
tp = TOUCH(0)

# Display constants
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480
CANVAS_WIDTH = 480  # 绘画区域宽度
CANVAS_HEIGHT = 480  # 绘画区域高度
TOOLBAR_WIDTH = 160  # 工具栏宽度

class DrawingApp:
    def __init__(self):
        """初始化绘画应用程序"""
        # 绘画状态
        self.current_color = (0, 0, 0)  # 当前颜色（黑色）
        self.current_brush_size = 5     # 当前画笔大小
        self.is_drawing = False         # 是否正在绘画
        self.last_x = None             # 上一个触摸点X坐标
        self.last_y = None             # 上一个触摸点Y坐标
        
        # 颜色调色板
        self.colors = [
            (0, 0, 0),       # 黑色
            (255, 0, 0),     # 红色
            (0, 255, 0),     # 绿色
            (0, 0, 255),     # 蓝色
            (255, 255, 0),   # 黄色
            (255, 0, 255),   # 紫色
            (0, 255, 255),   # 青色
            (255, 128, 0),   # 橙色
            (128, 0, 128),   # 深紫色
            (255, 255, 255), # 白色（橡皮擦）
        ]
        
        # 画笔大小选项
        self.brush_sizes = [2, 5, 8, 12, 16, 20]
        self.current_brush_index = 1  # 默认选择5像素
        
        # UI区域定义
        self.color_palette_y = 50
        self.color_size = 25
        self.color_spacing = 30
        
        self.brush_palette_y = 200
        self.brush_button_height = 25
        self.brush_spacing = 30
        
        self.control_buttons_y = 380
        self.button_width = 120
        self.button_height = 35
        
        # 创建单一显示图像，避免复杂的像素操作
        self.display_image = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB888)
        
        # 初始化显示
        self.clear_canvas()
        self.draw_ui()
        self.update_display()
    
    def clear_canvas(self):
        """清空画布"""
        # 清空整个显示图像
        self.display_image.clear()
        # 绘制白色画布背景
        self.display_image.draw_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, 
                                        color=(255, 255, 255), fill=True)
        # 绘制工具栏背景
        self.display_image.draw_rectangle(CANVAS_WIDTH, 0, TOOLBAR_WIDTH, CANVAS_HEIGHT, 
                                        color=(240, 240, 240), fill=True)
        # 绘制分隔线
        self.display_image.draw_line(CANVAS_WIDTH, 0, CANVAS_WIDTH, CANVAS_HEIGHT, 
                                   color=(200, 200, 200), thickness=2)
    
    def draw_ui(self):
        """绘制用户界面"""
        # 绘制工具栏背景
        self.display_image.draw_rectangle(CANVAS_WIDTH, 0, TOOLBAR_WIDTH, CANVAS_HEIGHT, 
                                        color=(240, 240, 240), fill=True)
        
        # 绘制分隔线
        self.display_image.draw_line(CANVAS_WIDTH, 0, CANVAS_WIDTH, CANVAS_HEIGHT, 
                                   color=(200, 200, 200), thickness=2)
        
        # 绘制标题
        self.display_image.draw_string_advanced(CANVAS_WIDTH + 10, 10, 20, 
                                               "绘画工具", color=(50, 50, 50))
        
        # 绘制颜色调色板
        self.draw_color_palette()
        
        # 绘制画笔大小选择
        self.draw_brush_size_palette()
        
        # 绘制控制按钮
        self.draw_control_buttons()
        
        # 绘制当前状态信息
        self.draw_status_info()
    
    def draw_color_palette(self):
        """绘制颜色调色板"""
        self.display_image.draw_string_advanced(CANVAS_WIDTH + 10, self.color_palette_y - 20, 16, 
                                               "颜色:", color=(80, 80, 80))
        
        # 绘制颜色方块（2行5列）
        for i, color in enumerate(self.colors):
            row = i // 5
            col = i % 5
            x = CANVAS_WIDTH + 15 + col * self.color_spacing
            y = self.color_palette_y + row * self.color_spacing
            
            # 绘制颜色方块
            self.display_image.draw_rectangle(x, y, self.color_size, self.color_size, 
                                            color=color, fill=True)
            
            # 如果是当前选中的颜色，绘制边框
            if color == self.current_color:
                self.display_image.draw_rectangle(x-2, y-2, self.color_size+4, self.color_size+4, 
                                                color=(0, 0, 0), fill=False, thickness=2)
    
    def draw_brush_size_palette(self):
        """绘制画笔大小选择"""
        self.display_image.draw_string_advanced(CANVAS_WIDTH + 10, self.brush_palette_y - 20, 16, 
                                               "画笔:", color=(80, 80, 80))
        
        # 绘制画笔大小按钮
        for i, size in enumerate(self.brush_sizes):
            y = self.brush_palette_y + i * self.brush_spacing
            
            # 按钮背景
            bg_color = (200, 200, 255) if i == self.current_brush_index else (220, 220, 220)
            self.display_image.draw_rectangle(CANVAS_WIDTH + 15, y, 100, self.brush_button_height, 
                                            color=bg_color, fill=True)
            
            # 按钮边框
            self.display_image.draw_rectangle(CANVAS_WIDTH + 15, y, 100, self.brush_button_height, 
                                            color=(150, 150, 150), fill=False)
            
            # 画笔大小文字
            self.display_image.draw_string_advanced(CANVAS_WIDTH + 20, y + 5, 14, 
                                                   f"{size}px", color=(50, 50, 50))
            
            # 画笔预览圆点
            preview_x = CANVAS_WIDTH + 80
            preview_y = y + self.brush_button_height // 2
            self.display_image.draw_circle(preview_x, preview_y, size//2, 
                                         color=(100, 100, 100), fill=True)
    
    def draw_control_buttons(self):
        """绘制控制按钮"""
        
        buttons = ["Clear", "Cancel"]
        button_colors = [(255, 200, 200), (200, 255, 200)]
        
        for i, (text, color) in enumerate(zip(buttons, button_colors)):
            y = self.control_buttons_y + i * (self.button_height + 10)
            
            # 按钮背景
            self.display_image.draw_rectangle(CANVAS_WIDTH + 20, y, self.button_width, self.button_height, 
                                            color=color, fill=True)
            
            # 按钮边框
            self.display_image.draw_rectangle(CANVAS_WIDTH + 20, y, self.button_width, self.button_height, 
                                            color=(100, 100, 100), fill=False)
            
            # 按钮文字
            # 英文备选
            en_text = "Clear" if i == 0 else "Undo"
            self.display_image.draw_string_advanced(CANVAS_WIDTH + 30, y + 8, 16, 
                                                   en_text, color=(50, 50, 50))
    
    def draw_status_info(self):
        """绘制当前状态信息 - 移动到画布左上角"""
        status_x = 10  # 左上角X坐标
        status_y = 10  # 左上角Y坐标
        
        # 绘制半透明背景
        self.display_image.draw_rectangle(status_x - 5, status_y - 5, 120, 35, 
                                        color=(255, 255, 255), fill=True)
        self.display_image.draw_rectangle(status_x - 5, status_y - 5, 120, 35, 
                                        color=(150, 150, 150), fill=False)
        
        # 当前颜色显示
        self.display_image.draw_rectangle(status_x, status_y, 20, 20, 
                                        color=self.current_color, fill=True)
        self.display_image.draw_rectangle(status_x, status_y, 20, 20, 
                                        color=(0, 0, 0), fill=False)
        
        # 当前画笔大小显示
        self.display_image.draw_string_advanced(status_x + 25, status_y + 3, 14, 
                                               f"{self.current_brush_size}px", color=(50, 50, 50))
    
    def handle_touch(self, x, y, event):
        """处理触摸事件"""
        if x < CANVAS_WIDTH:
            # 在画布区域绘画
            self.handle_drawing(x, y, event)
        else:
            # 在工具栏区域处理UI交互
            self.handle_ui_interaction(x, y, event)
    
    def handle_drawing(self, x, y, event):
        """处理绘画操作"""
        if event == TOUCH.EVENT_DOWN:
            self.is_drawing = True
            self.last_x = x
            self.last_y = y
            # 绘制起始点
            self.display_image.draw_circle(x, y, self.current_brush_size//2, 
                                         color=self.current_color, fill=True)
        
        elif event == TOUCH.EVENT_MOVE and self.is_drawing:
            if self.last_x is not None and self.last_y is not None:
                # 绘制连续线条
                self.display_image.draw_line(self.last_x, self.last_y, x, y, 
                                           color=self.current_color, 
                                           thickness=self.current_brush_size)
            self.last_x = x
            self.last_y = y
        
        elif event == TOUCH.EVENT_UP:
            self.is_drawing = False
            self.last_x = None
            self.last_y = None
    
    def handle_ui_interaction(self, x, y, event):
        """处理UI交互"""
        if event != TOUCH.EVENT_DOWN:
            return
        
        # 检查颜色选择
        if self.color_palette_y <= y <= self.color_palette_y + 60:
            self.handle_color_selection(x, y)
        
        # 检查画笔大小选择
        elif self.brush_palette_y <= y <= self.brush_palette_y + len(self.brush_sizes) * self.brush_spacing:
            self.handle_brush_size_selection(x, y)
        
        # 检查控制按钮
        elif self.control_buttons_y <= y <= self.control_buttons_y + 80:
            self.handle_control_buttons(x, y)
    
    def handle_color_selection(self, x, y):
        """处理颜色选择"""
        rel_x = x - (CANVAS_WIDTH + 15)
        rel_y = y - self.color_palette_y
        
        if rel_x >= 0 and rel_y >= 0:
            col = rel_x // self.color_spacing
            row = rel_y // self.color_spacing
            color_index = row * 5 + col
            
            if 0 <= color_index < len(self.colors):
                self.current_color = self.colors[color_index]
                print(f"选择颜色: {self.current_color}")
                # 重新绘制UI以更新选中状态
                self.draw_ui()
    
    def handle_brush_size_selection(self, x, y):
        """处理画笔大小选择"""
        if CANVAS_WIDTH + 15 <= x <= CANVAS_WIDTH + 115:
            rel_y = y - self.brush_palette_y
            brush_index = rel_y // self.brush_spacing
            
            if 0 <= brush_index < len(self.brush_sizes):
                self.current_brush_index = brush_index
                self.current_brush_size = self.brush_sizes[brush_index]
                print(f"选择画笔大小: {self.current_brush_size}px")
                # 重新绘制UI以更新选中状态
                self.draw_ui()
    
    def handle_control_buttons(self, x, y):
        """处理控制按钮"""
        if CANVAS_WIDTH + 20 <= x <= CANVAS_WIDTH + 20 + self.button_width:
            rel_y = y - self.control_buttons_y
            button_index = rel_y // (self.button_height + 10)
            
            if button_index == 0:  # 清屏按钮
                self.clear_canvas()
                self.draw_ui()
                print("清空画布")
            elif button_index == 1:  # 撤销按钮
                print("撤销功能（待实现）")
    
    def update_display(self):
        """更新显示 - 简化版本，避免像素级操作"""
        Display.show_image(self.display_image)

def main():
    """主程序"""
    print("启动增强版触摸绘画程序...")
    print("Enhanced Touch Drawing App Starting...")
    
    # 初始化显示
    Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    MediaManager.init()
    
    # 创建绘画应用
    app = DrawingApp()
    
    try:
        print("程序已启动，开始绘画吧！")
        print("App started, start drawing!")
        
        while True:
            os.exitpoint()
            
            # 读取触摸点
            points = tp.read(1)
            
            if len(points) > 0:
                pt = points[0]
                app.handle_touch(pt.x, pt.y, pt.event)
                # 只在有触摸事件时更新显示
                app.update_display()
            
            time.sleep(0.02)  # 50 FPS
            
    except KeyboardInterrupt:
        print("用户停止程序")
        print("User stopped the program")
    except Exception as e:
        print(f"程序异常: {e}")
        print(f"Program exception: {e}")
    finally:
        # 清理资源
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        MediaManager.deinit()
        print("程序已退出")
        print("Program exited")

if __name__ == "__main__":
    os.exitpoint(os.EXITPOINT_ENABLE)
    main()