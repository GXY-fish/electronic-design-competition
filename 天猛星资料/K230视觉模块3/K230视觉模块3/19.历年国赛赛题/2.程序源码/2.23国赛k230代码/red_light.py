import time
from media.sensor import *
from media.display import *
from media.media import *
from ybUtils.YbKey import YbKey
from ybUtils.YbUart import YbUart

key = YbKey()
uart = YbUart(baudrate=115200)

WIDTH = 640
HEIGHT = 480
sensor = Sensor(width = WIDTH, height = HEIGHT, fps=30)
sensor.reset()
time.sleep_ms(100)
sensor.set_framesize(width = WIDTH, height = HEIGHT)
sensor.set_pixformat(sensor.RGB565)

#red_light = (67, 100, -3, 40, -6, 11)
light = (85, 100, 25, -16, -16, 51)
red_light = (0, 100, 22, 80, -27, 94)
light_roi =(100,40,600,420)#根据自己的硬件结构修改！！！



Display.init(Display.ST7701, width = WIDTH, height = HEIGHT, to_ide = True)
MediaManager.init()

sensor.run()
clock = time.clock()

last_cx = 300 #初始点x坐标
last_cy = 220 #初始点y坐标

#last_cx = 0
#last_cy = 400





def find_max_blob(blobs): #寻找最大色块面积函数
    blobs.sort(key=lambda x:x.perimeter(),reverse=True);
    max_value={}
    max_value=blobs[0];
    return max_value;


def send_target_data(x,y):
    n = 0
    for i in range(4):
        x_h = (x>>8)&0xFF
        x_l = x&0xFF
        y_h = (y>>8)&0xFF
        y_l = y&0xFF
        uart.write(bytearray([0x55, 0xaa, 0xff, int(x_h)&0xFF, int(x_l)&0xFF, 0xfa]))

        time.sleep_ms(3)
        n+=1

        uart.write(bytearray([0x55, 0xaa, 0x00, int(y_h)&0xFF, int(y_l)&0xFF, 0xfa]))

        time.sleep_ms(3)
        n+=1


def conversion_postion(x,y):
    if x > 510:
       x_h = 255
       x_l = 255
       x_z = x-255-255
    elif 510>=x>=255:
       x_h = 255
       x_l = x-255
       x_z = 0
    else:
       x_h = x
       x_l = 0
       x_z = 0
    if y > 510:
       y_h = 255
       y_l = 255
       y_z = y-255-255
    elif 510>=y>=255:
       y_h = 255
       y_l = y-255
       y_z = 0
    else:
       y_h = y
       y_l = 0
       y_z = 0
    return x_h,x_l,x_z,y_h,y_l,y_z


def color_blob(img,hano,color):#寻找指定颜色最大色块
    blobs = img.find_blobs([hano],roi=light_roi,merge = True)
    if blobs:
        #print(blobs)
        #print('light')
        global last_cx
        global last_cy
        for blob in blobs:
            roi = (blob.x()-5,blob.y()-5,blob.w()+10,blob.h()+10)#得到亮斑外接圆范围
            #img.draw_rectangle(blob[0:4],color=(0,0,255)) # 画矩形
            #if img.find_blobs([color],roi=roi,merge = True):#找到了指定颜色
            if img.find_blobs([color],roi=roi,x_stride=1, y_stride=1,
                             area_threshold=0, pixels_threshold=0,merge=False,margin=1):#找到了指定颜色
               #print('red')
               cx = blob[5]
               cy = blob[6]
               img.draw_rectangle(blob[0:4],color=(0,0,255)) # 画矩形
               img.draw_cross(blob[5], blob[6],color=(0,0,255)) # 画十字
               last_cx = cx#更新坐标
               last_cy = cy#更新坐标
               #print(cx,cy)
               return cx, cy, 1
        return last_cx, last_cy, 0
    return last_cx, last_cy, 0


while True:
    clock.tick()
    os.exitpoint()
    img = sensor.snapshot()
    img = img.gaussian(1)
    img = sensor.snapshot().lens_corr(strength = 1.7 , zoom = 1.0)
    cx,cy,ok= color_blob(img,light,red_light)
    cx_h,cx_l,cx_z,cy_h,cy_l,cy_z = conversion_postion(cx,cy)

    img.draw_rectangle(light_roi,color=(0,0,255)) # rect
    uart.write(bytearray([0x55,0xaa,0x00,int(cx_h),int(cx_l),int(cx_z),0xfa]))
    uart.write(bytearray([0x55,0xaa,0xff,int(cy_h),int(cy_l),int(cy_z),0xfa]))

    Display.show_image(img)



