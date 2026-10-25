#include "yb_protocol.h"

#include "stdio.h"
#include "stdlib.h"
#include "string.h"

#define DEBUG 0
#if DEBUG
    #define DEBUG_PRINT(fmt, ...) printf(fmt, ##__VA_ARGS__)
#else
    #define DEBUG_PRINT(fmt, ...) // 定义为空，编译器会优化掉   Define it as empty, the compiler will optimize it away
#endif

uint8_t RxBuffer[PTO_BUF_LEN_MAX];
/* 接收数据下标 *//* Receive data index */
uint8_t RxIndex = 0;
/* 接收状态机 *//* Receive state machine */
uint8_t RxFlag = 0;
/* 新命令接收标志 *//* New command receiving flag */
uint8_t New_CMD_flag;
/* 新命令数据长度 *//* New command data length */
uint8_t New_CMD_length;
// 全局变量，用于通信丢失检测   Global variable for communication loss detection
volatile int lost_count = 50;
volatile int Lost_Flag = 0;

extern int Car_Auto_Drive;

int x,y,w,h,id,degrees,x0,y0,x1,y1= 0;
float score = 0;


///////////////////////***************定义所有协议字段描述****************/////////////////////////
//////////////////**********Define all protocol field descriptions*************//////////////////


// 颜色识别协议：字段2-5为数字 // Color detection protocol: fields 2-5 are integers
static const FieldMeta color_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}
};

// 条码识别协议：字段2-5是数字，字段6是字符串 // Barcode protocol: fields 2-5 are integers, field 6 is a string
static const FieldMeta barcode_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_STRING}
};

// 二维码识别协议：字段2-5是数字，字段6是字符串 // QRCode protocol: fields 2-5 are integers, field 6 is a string
static const FieldMeta qrcode_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_STRING}
};

// AprilTag识别协议：字段2-7为数字 // AprilTag protocol: fields 2-7 are integers
static const FieldMeta apriltag_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_INT}, {7, FIELD_INT}
};

// DataMatrix码协议：字段2-5是数字，字段6是字符串，字段7是角度 // DataMatrix code protocol: fields 2-5 are integers, field 6 is a string, field 7 is an angle
static const FieldMeta dmcode_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_STRING}, {7, FIELD_INT}
};

// 人脸检测协议：字段2-5为数字 // Face detection protocol: fields 2-5 are integers
static const FieldMeta facedetect_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}
};

// 注视方向协议：字段2-5为数字（x0,y0,x1,y1） // Gaze direction protocol: fields 2-5 are coordinates (x0,y0,x1,y1)
static const FieldMeta eyegaze_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}
};

// 人脸识别协议：字段2-5为数字，字段6是字符串（姓名），字段7是分数 // Face recognition protocol: fields 2-5 are integers, field 6 is name string, field 7 is score
static const FieldMeta facerecog_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_STRING}, {7, FIELD_INT}
};

// 人体检测协议：字段2-5为数字 // Person detection protocol: fields 2-5 are integers
static const FieldMeta persondetect_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}
};

// 跌倒检测协议：字段2-5为数字，字段6是状态字符串，字段7是分数 // Fall detection protocol: fields 2-5 are integers, field 6 is state string, field 7 is score
static const FieldMeta falldown_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_STRING}, {7, FIELD_INT}
};

// 手部检测协议：字段2-5为数字 // Hand detection protocol: fields 2-5 are integers
static const FieldMeta handdetect_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}
};

// 手势识别协议：字段2是字符串 // Hand gesture protocol: field 2 is a string
static const FieldMeta handgesture_fields[] = {
    {2, FIELD_STRING}
};

// OCR识别协议：字段2是字符串 // OCR recognition protocol: field 2 is a string
static const FieldMeta ocrrec_fields[] = {
    {2, FIELD_STRING}
};

// 目标检测协议：字段2-5为数字，字段6是类别字符串 // Object detection protocol: fields 2-5 are integers, field 6 is class name
static const FieldMeta objectdetect_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_STRING}
};

// 跟踪器协议：字段2-5为数字 // Nano tracker protocol: fields 2-5 are integers
static const FieldMeta nanotracker_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}
};

// 自学习分类协议：字段2是类别字符串，字段3是分数 // Self-learning classification protocol: field 2 is category name, field 3 is score
static const FieldMeta selflearning_fields[] = {
    {2, FIELD_STRING}, {3, FIELD_INT}
};

// 车牌识别协议：字段2是字符串 // License plate recognition protocol: field 2 is a string
static const FieldMeta licencerec_fields[] = {
    {2, FIELD_STRING}
};

// 车牌检测协议：字段2-9为数字 // License plate detection protocol: fields 2-9 are numbers
static const FieldMeta licencedetect_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_INT}, {7, FIELD_INT}, {8, FIELD_INT}, {9, FIELD_INT}
};

// 垃圾检测协议： 字段2-5为数字, 字段7为字符串 // Spam detection protocol: Fields 2-5 are numbers, field 7 is a string
static const FieldMeta garbagedetect_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_STRING}
};

// 路标识别协议：字段2-5为数字, 字段7为字符串 // Road sign recognition protocol: Fields 2-5 are numbers, field 7 is a string
static const FieldMeta guidedetect_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_STRING}
};

// 障碍检测协议：字段2-5为数字, 字段7为字符串 // Obstacle detection protocol: Fields 2-5 are numbers, field 7 is a string
static const FieldMeta obstacledetect_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_STRING}
};

// 多颜色识别协议：字段2-5为数字, 字段7为字符串 // Multi-color identification protocol: Fields 2-5 are numbers, field 7 is a string
static const FieldMeta multicolorrec_fields[] = {
    {2, FIELD_INT}, {3, FIELD_INT}, {4, FIELD_INT}, {5, FIELD_INT}, {6, FIELD_STRING}
};


// 全局功能表定义，每个协议条目独立展开 // Global function table definition, each protocol entry is explicitly listed
const FuncDesc func_table[] = {
    
    // 颜色识别协议：4个字段（x/y/w/h） // Color detection protocol: 4 fields (x/y/w/h)
    {ID_COLOR, color_fields, 4, HandleColor},

    // 条形码识别协议：5个字段（x/y/w/h/msg） // Barcode recognition protocol: 5 fields (x/y/w/h/msg)
    {ID_BARCODE, barcode_fields, 5, HandleBarcode},

    // 二维码识别协议：5个字段（x/y/w/h/msg） // QRCode detection protocol: 5 fields (x/y/w/h/msg)
    {ID_QRCODE, qrcode_fields, 5, HandleQRCode},

    // AprilTag识别协议：6个字段（x/y/w/h/id/degrees） // AprilTag detection protocol: 6 fields (x/y/w/h/id/degrees)
    {ID_APRILTAG, apriltag_fields, 6, HandleAprilTag},

    // DataMatrix码协议：6个字段（x/y/w/h/msg/degrees） // DataMatrix code protocol: 6 fields (x/y/w/h/msg/degrees)
    {ID_DMCODE, dmcode_fields, 6, HandleDMCode},

    // 人脸检测协议：4个字段（x/y/w/h） // Face detection protocol: 4 fields (x/y/w/h)
    {ID_FACE_DETECT, facedetect_fields, 4, HandleFaceDetect},

    // 注视方向协议：4个字段（x0/y0/x1/y1） // Gaze Direction Protocol: 4 fields (x0/y0/x1/y1)
    {ID_EYE_GAZE, eyegaze_fields, 4, HandleEyeGaze},

    // 人脸识别协议：6个字段（x/y/w/h/name/score） // Face recognition protocol: 6 fields (x/y/w/h/name/score)
    {ID_FACE_RECOGNITION, facerecog_fields, 6, HandleFaceRecognition},

    // 人体检测协议：4个字段（x/y/w/h） // Person detection protocol: 4 fields (x/y/w/h)
    {ID_PERSON_DETECT, persondetect_fields, 4, HandlePersonDetect},

    // 跌倒检测协议：6个字段（x/y/w/h/state/score） // Fall detection protocol: 6 fields (x/y/w/h/state/score)
    {ID_FALLDOWN_DETECT, falldown_fields, 6, HandleFallDown},

    // 手掌检测协议：4个字段（x/y/w/h） // Palm detection protocol: 4 fields (x/y/w/h)
    {ID_HAND_DETECT, handdetect_fields, 4, HandleHandDetect},

    // 手势识别协议：1个字段（gesture） // Hand gesture protocol: 1 field (gesture)
    {ID_HAND_GESTURE, handgesture_fields, 1, HandleHandGesture},

    // OCR字符识别协议：1个字段（text） // OCR character recognition protocol: 1 field (text)
    {ID_OCR_REC, ocrrec_fields, 1, HandleOCRRec},

    // 物体检测协议：5个字段（x/y/w/h/class） // Object detection protocol: 5 fields (x/y/w/h/class)
    {ID_OBJECT_DETECT, objectdetect_fields, 5, HandleObjectDetect},

    // 目标跟踪协议：4个字段（x/y/w/h） // Target Tracking Protocol: 4 fields (x/y/w/h)
    {ID_NANO_TRACKER, nanotracker_fields, 4, HandleNanoTracker},

    // 自学习物体识别协议：2个字段（category/score） // Self-learning object recognition protocol: 2 fields (category/score)
    {ID_SELF_LEARNING, selflearning_fields, 2, HandleSelfLearning},

    // 车牌识别协议：1个字段 // License plate recognition protocol: 1 field 
    {ID_LICENCE_REC, licencerec_fields, 1, HandleLicenceRec},
    
    // 车牌检测协议：8个字段 // License plate detection protocol: 8 fields 
    {ID_LICENCE_DETECT, licencedetect_fields, 8, HandleLicenceDetect},
    
    // 垃圾检测协议：4个字段 // Spam detection protocol: 4 fields 
    {ID_GARBAGE_DETECT, garbagedetect_fields, 5, HandleGarbageDetect},
    
    // 路标检测协议：5个字段 // Signpost Detection Protocol: 5 fields 
    {ID_GUIDE_DETECT, guidedetect_fields, 5, HandleGuideDetect},
    
    // 障碍检测协议：5个字段 // Obstacle Detection Protocol: 5 fields 
    {ID_OBSTACLE_DETECT, obstacledetect_fields, 5, HandleObstacleDetect},
    
    // 多颜色识别协议：5个字段 // Multi-color recognition protocol: 5 fields 
    {ID_MULTI_COLOR, multicolorrec_fields, 5, HandleMultiColorRec},
};



// 清除命令数据和相关标志  Clear command data and related flags
void Pto_Clear_CMD_Flag(void)
{
	for (uint8_t i = 0; i < PTO_BUF_LEN_MAX; i++)
	{
		RxBuffer[i] = 0;
	}
	New_CMD_length = 0;
	New_CMD_flag = 0;
}


// 接收数据进入协议缓存   Receive data into the protocol buffer
void Pto_Data_Receive(uint8_t Rx_Temp)
{
	switch (RxFlag)
	{
	case 0:
		if (Rx_Temp == PTO_HEAD)
		{
			RxBuffer[0] = PTO_HEAD;
			RxFlag = 1;
            RxIndex = 1;
		}
		break;

	case 1:
		RxBuffer[RxIndex] = Rx_Temp;
		RxIndex++;
		if (Rx_Temp == PTO_TAIL)
		{
			New_CMD_flag = 1;
            New_CMD_length = RxIndex;
			RxFlag = 0;
			RxIndex = 0;
            //printf("Received: %s\r\n", RxBuffer);
		}
        else if (RxIndex >= PTO_BUF_LEN_MAX)
        {
            New_CMD_flag = 0;
            New_CMD_length = 0;
			RxFlag = 0;
			RxIndex = 0;
            Pto_Clear_CMD_Flag();
        }
		break;

	default:
		break;
	}
}

void Get_LOST_Flag(void)
{
    if (lost_count > 0)
    {
        Lost_Flag = 0;
        lost_count--;
    }
    if (lost_count == 0)
    {
        Lost_Flag = 1;
        lost_count = 50;
    }
}

// 将字符串数字转成数字。示例："12"->12   Convert a string number to a number. Example: "12"->12
int Pto_Char_To_Int(char* data)
{
    return atoi(data);
}

/**
 * @Brief: 数据分析 Data analysis
 * @Note: 
 * @Parm: 传入接受到的一个数据帧和长度    Pass in a received data frame and length
 * @Retval: 
 */
void Pto_Data_Parse(uint8_t *data_buf, uint8_t num)
{
    uint8_t pto_head = data_buf[0];
	uint8_t pto_tail = data_buf[num-1];
    
    //校验头尾  Check head and tail
    if (!(pto_head == PTO_HEAD && pto_tail == PTO_TAIL))
    {
	    //DEBUG_PRINT("pto error:pto_head=0x%02x , pto_tail=0x%02x\n", pto_head, pto_tail);
        return;
    }
    
    uint8_t data_index = 1;
    uint8_t field_index[PTO_BUF_LEN_MAX] = {0};
    int i = 0;
    int values[PTO_BUF_LEN_MAX] = {0};
    char msgs[][PTO_BUF_LEN_MAX] = {0};
    
    //分割字段  Split Field
    for (i = 1; i < num-1; i++)
    {
        if (data_buf[i] == ',')
        {
            data_buf[i] = 0;
            field_index[data_index] = i;
            data_index++;
        }
    }
    
    //解析长度与功能ID  Parsing length and function ID
    for (i = 0; i < 2; i++)
    {
        values[i] = Pto_Char_To_Int((char*)data_buf+field_index[i]+1);
    }
    
    uint8_t pto_len = values[0];
    uint8_t pto_id = values[1];
    
    ParseCommonFields(pto_id,data_buf,pto_len,field_index,data_index,values,msgs);
}

//获取数据函数  Get data function
void ParseCommonFields(
    int func_index,       // 功能索引（对应func_table中的位置） Function index (corresponding to the position in func_table)
    uint8_t *data_buf,    // 原始数据缓冲区 Raw data buffer
    uint8_t num,          // 数据总长度（含头尾）   Total length of data (including head and tail)
    uint8_t *field_index, // 字段分隔符位置数组（逗号的位置）   Array of field separator positions (positions of commas)
    uint8_t data_index,   // 总字段数（如数据有6个字段）    Total number of fields (if the data has 6 fields)
    int* values,          // 存储整数字段的数组 Array to store integer fields
    char msgs[][PTO_BUF_LEN_MAX]        // 存储字符串的指针数组 Array of pointers to store strings
){
    const FuncDesc* desc = &func_table[func_index-1];
    
    if(func_index != desc->id)
    {
        DEBUG_PRINT("Unsupported protocol ID: %d, Chosen ID:%d\n", func_index,desc->id);
        return;
    }
    
    for (int i = 0; i < desc->field_count; i++) 
    {
        const FieldMeta* meta = &desc->fields[i];
        uint8_t pos = meta->pos;
        
        if (meta->type == FIELD_STRING) {
            int start = field_index[pos] + 1;
            int end = (pos+1 < data_index) ? field_index[pos+1] : (num-1);
            int len = end - start;
            
            len = (len < PTO_BUF_LEN_MAX-1) ? len : PTO_BUF_LEN_MAX-1;
            memcpy(msgs[i], data_buf+start, len);
            msgs[i][len] = '\0';
        } else {
            values[pos] = Pto_Char_To_Int((char*)data_buf + field_index[pos] +1);
        }
    }
    desc->handler(values, msgs);
}



///////////////////////////********************协议处理函数*****************************/////////////////////
///////////////////////////**************Protocol processing function******************/////////////////////

// 处理协议内容   Processing agreement content
void Pto_Loop(void)
{    
    if (New_CMD_flag)
    {
        Pto_Data_Parse((uint8_t*)RxBuffer, New_CMD_length);
        Pto_Clear_CMD_Flag();
    }
    
    Get_LOST_Flag();
    if(Car_Auto_Drive && Lost_Flag)
    {
        Motion_Car_Control(200, 0, 0);
    }
    else if(Lost_Flag)
    {
        Motion_Car_Control(0, 0, 0);
        Lost_Flag = 0; // 清除标志，避免持续触发    Clear the flag to avoid continuous triggering
    }
}


// 处理颜色识别协议 // Handle color detection protocol
void HandleColor(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    DEBUG_PRINT("color:x:%d, y:%d, w:%d, h:%d\n", x, y, w, h);
    switch(color_mode)
    {
        case COLOR_MODE_FOLLOW_LINE:
            Visual_Line_Track(x);
            break;
        case COLOR_MODE_TRACE:
            Color_Trace(x,w,h);
            break;
    }
}

// 处理条形码检测协议 // Handle barcode detection protocol
void HandleBarcode(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    const char* msg = msgs[4];
    DEBUG_PRINT("barcode:x:%d, y:%d, w:%d, h:%d, msg:'%s'\n", x, y, w, h, msg);
}

// 处理二维码检测协议 // Handle QRCode detection protocol
void HandleQRCode(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    const char* msg = msgs[4];
    DEBUG_PRINT("qrcode:x:%d, y:%d, w:%d, h:%d, msg:'%s'\n", x, y, w, h, msg);
    QRCode_Action(msg);
}

// 处理AprilTag协议 // Handle AprilTag protocol
void HandleAprilTag(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    int id = values[6], degrees = values[7];
    DEBUG_PRINT("apriltag:x:%d, y:%d, w:%d, h:%d, id:%d, degrees:%d\n", x, y, w, h, id, degrees);
    AprilTag_Track(x,w,h);
}

// 处理DataMatrix码协议 // Handle DataMatrix code protocol
void HandleDMCode(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    const char* msg = msgs[4];
    int degrees = values[6];
    DEBUG_PRINT("dmcode:x:%d, y:%d, w:%d, h:%d, msg:'%s', degrees:%d\n", x, y, w, h, msg, degrees);
}

// 处理人脸检测协议 // Handle face detection protocol
void HandleFaceDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    DEBUG_PRINT("face:x:%d, y:%d, w:%d, h:%d\n", x, y, w, h);
    Human_Face_Track(x,w,h);
}

// 处理注视方向协议 // Handle gaze direction protocol
void HandleEyeGaze(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x0 = values[2], y0 = values[3], x1 = values[4], y1 = values[5];
    DEBUG_PRINT("eye:x0:%d, y0:%d, x1:%d, y1:%d\n", x0, y0, x1, y1);
    GazeDire_Track(x0, x1);
}

// 处理人脸识别协议 // Handle face recognition protocol
void HandleFaceRecognition(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    const char* name = msgs[4];
    float score = values[6] / 100.0;
    DEBUG_PRINT("face recognition:x:%d, y:%d, w:%d, h:%d, name:'%s', score:%.2f\n", x, y, w, h, name, score);
}

// 处理人体检测协议 // Handle person detection protocol
void HandlePersonDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    DEBUG_PRINT("person:x:%d, y:%d, w:%d, h:%d\n", x, y, w, h);
    HumanBody_Track(x,w,h);
}

// 处理跌倒检测协议 // Handle fall detection protocol
void HandleFallDown(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    const char* state = msgs[4];
    float score = values[6] / 100.0;
    DEBUG_PRINT("falldown:x:%d, y:%d, w:%d, h:%d, state:'%s', score:%.2f\n", x, y, w, h, state, score);
}

// 处理手掌检测协议 // Handle palm detection protocol
void HandleHandDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    DEBUG_PRINT("hand:x:%d, y:%d, w:%d, h:%d\n", x, y, w, h);
    Hand_Track(x,w,h);
}

// 处理手势识别协议 // Handle hand gesture protocol
void HandleHandGesture(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    const char* gesture = msgs[0];
    DEBUG_PRINT("gesture:'%s'\n", gesture);
}

// 处理OCR字符识别协议 // Handle OCR character recognition protocol
void HandleOCRRec(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    const char* text = msgs[0];
    DEBUG_PRINT("ocr_rec:'%s'\n", text);
    OCRrec_Actions(text);
}

// 处理物体检测协议 // Handle object detection protocol
void HandleObjectDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    const char* class_name = msgs[4];
    DEBUG_PRINT("object:x:%d, y:%d, w:%d, h:%d, class:'%s'\n", x, y, w, h, class_name);
}

// 处理目标跟踪协议 // Handle target tracking protocol
void HandleNanoTracker(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    DEBUG_PRINT("tracker:x:%d, y:%d, w:%d, h:%d\n", x, y, w, h);
    Target_Track(x);
}

// 处理自学习物体识别协议 // Handle self-learning object recognition protocol
void HandleSelfLearning(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    const char* category = msgs[0];
    float score = values[1] / 100.0;
    DEBUG_PRINT("category:'%s', score:%.2f\n", category, score);
}

// 处理车牌识别协议 // Handle license plate recognition protocol
void HandleLicenceRec(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    const char* plate = msgs[0];
    DEBUG_PRINT("licence_rec:'%s'\n", plate);
}

// 处理车牌检测协议 //Processing license plate detection protocol
void HandleLicenceDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x1 = values[6], y1 = values[7], x2 = values[4], y2 = values[5],//1:左上,2:左下3:右上4:右下  1: Top left, 2: Bottom left, 3: Top right, 4: Bottom right
        x3 = values[8], y3 = values[9], x4 = values[2], y4 = values[3];
    DEBUG_PRINT("licence_detect:x1:%d, y1:%d, x2:%d, y2:%d, x3:%d, y3:%d, x4:%d, y4:%d, \n", x1,y1,x2,y2,x3,y3,x4,y4);
    Licence_Track(x1,y1,x2,y2,x3);
}

// 处理垃圾检测协议 //Processing spam detection protocol
void HandleGarbageDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    const char* lable = msgs[4];
    DEBUG_PRINT("object:x:%d, y:%d, w:%d, h:%d, class:'%s'\n", x, y, w, h, lable);
}

// 处理路标检测协议 //Handling road sign detection protocol
void HandleGuideDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    const char* lable = msgs[4];
    DEBUG_PRINT("object:x:%d, y:%d, w:%d, h:%d, class:'%s'\n", x, y, w, h, lable);
    RoadSign_Rec(lable);
}

// 处理障碍检测协议 //Handling Obstacle Detection Protocol
void HandleObstacleDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    const char* lable = msgs[4];
    DEBUG_PRINT("object:x:%d, y:%d, w:%d, h:%d, class:'%s'\n", x, y, w, h, lable);
    Autonomous_Avoid(w,h);
}

// 处理多颜色识别协议 //Handling multiple color recognition protocols
void HandleMultiColorRec(int* values, char msgs[][PTO_BUF_LEN_MAX]) {
    int x = values[2], y = values[3], w = values[4], h = values[5];
    const char* color = msgs[4];
    DEBUG_PRINT("object:x:%d, y:%d, w:%d, h:%d, color:'%s'\n", x, y, w, h, color);
    Color_Rec(color);
}
