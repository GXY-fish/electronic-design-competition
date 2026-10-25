from machine import UART, Pin

FUNC_ID = 7


uart1 = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9), bits=8, parity=None, stop=0)

print("hello yahboom")


def parse_data(data):
    if data[0] == ord('$') and data[len(data)-1] == ord('#'):
        data_list = data[1:len(data)-1].decode('utf-8').split(',')
        data_len = int(data_list[0])
        data_id = int(data_list[1])
        if data_len == len(data) and data_id == FUNC_ID:
            # print(data_list)
            x0 = int(data_list[2])
            y0 = int(data_list[3])
            x1 = int(data_list[4])
            y1 = int(data_list[5])
            return x0, y0, x1, y1
        elif (data_len != len(data)):
            print("data len error:", data_len, len(data))
        elif(data_id != FUNC_ID):
            print("func id error:", data_id, FUNC_ID)
    return -1, -1, -1, -1

last_data = bytearray()
while True:
    if uart1.any() > 0:
        cur_data = uart1.readline()
        # print("rx:", cur_data)
        if ord('\n') in cur_data:
            # data = bytearray(last_data + cur_data.decode('utf-8'), 'utf-8')
            data = last_data + cur_data
            last_data = bytearray()
            x0, y0, x1, y1 = parse_data(data.rstrip(b'\n'))
            print("eye:x0:%d, y0:%d, x1:%d, y1:%d" % (x0, y0, x1, y1))
        else:
            last_data = last_data + cur_data

