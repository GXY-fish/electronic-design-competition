import serial

com="/dev/ttyUSB0"
ser = serial.Serial(com, 115200)

FUNC_ID = 7


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

while True:
    if ser.in_waiting:
        data = ser.readline()
        # print("rx:", data)
        x0, y0, x1, y1 = parse_data(data.rstrip(b'\n'))
        print("eye:x0:%d, y0:%d, x1:%d, y1:%d" % (x0, y0, x1, y1))

