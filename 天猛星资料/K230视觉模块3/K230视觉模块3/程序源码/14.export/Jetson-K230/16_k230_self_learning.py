import serial

com="/dev/ttyUSB0"
ser = serial.Serial(com, 115200)

FUNC_ID = 16

def parse_data(data):
    if data[0] == ord('$') and data[len(data)-1] == ord('#'):
        data_list = data[1:len(data)-1].decode('utf-8').split(',')
        data_len = int(data_list[0])
        data_id = int(data_list[1])
        if data_len == len(data) and data_id == FUNC_ID:
            # print(data_list)
            category = data_list[2]
            score = int(data_list[3])/100.0

            return category, score
        elif (data_len != len(data)):
            print("data len error:", data_len, len(data))
        elif(data_id != FUNC_ID):
            print("func id error:", data_id, FUNC_ID)
    else:
        print("pto error", data)
    return "", -1

while True:
    if ser.in_waiting:
        data = ser.readline()
        # print("rx:", data)
        category, score = parse_data(data.rstrip(b'\n'))
        print("category:%s, score:%.2f" % (category, score))

