#ifndef _YB_PROTOCOL_H_
#define _YB_PROTOCOL_H_
#include "AllHeader.h"

#define PTO_BUF_LEN_MAX           (50)

#define PTO_HEAD                  (0x24)
#define PTO_TAIL                  (0x23)

//协议的ID号    The ID number of the agreement
typedef enum
{
    ID_COLOR = 1,
    ID_BARCODE = 2,
    ID_QRCODE = 3,
    ID_APRILTAG = 4,
    ID_DMCODE = 5,
    ID_FACE_DETECT = 6,
    ID_EYE_GAZE = 7,
    ID_FACE_RECOGNITION = 8,
    ID_PERSON_DETECT = 9,
    ID_FALLDOWN_DETECT = 10,
    ID_HAND_DETECT = 11,
    ID_HAND_GESTURE = 12,
    ID_OCR_REC = 13,
    ID_OBJECT_DETECT = 14,
    ID_NANO_TRACKER = 15,
    ID_SELF_LEARNING = 16,
    ID_LICENCE_REC = 17,
    ID_LICENCE_DETECT = 18,
    ID_GARBAGE_DETECT = 19,
    ID_GUIDE_DETECT = 20,
    ID_OBSTACLE_DETECT = 21,
    ID_MULTI_COLOR = 22,
}PTO_FUNC_ID;


// 字段类型枚举 Field type enumeration
typedef enum {
    FIELD_INT,
    FIELD_STRING
} FieldType;

// 字段描述结构体   Field Description Structure
typedef struct {
    uint8_t pos;        // 字段在协议中的位置（如2代表第3个字段）   The position of the field in the protocol (e.g. 2 represents the third field)
    FieldType type;     // 字段类型 Field Type
} FieldMeta;

// 功能描述结构体   Function description structure
typedef struct {
    PTO_FUNC_ID id;
    const FieldMeta* fields;  // 字段元数据数组 Field metadata array
    uint8_t field_count;
    void (*handler)(int* values, char msgs[][PTO_BUF_LEN_MAX]); 
} FuncDesc;

typedef enum {
    COLOR_MODE_FOLLOW_LINE = 1,  // 巡线模式    Line patrol mode
    COLOR_MODE_TRACE,    // 追踪模式    Tracking Mode
} ColorMode;


extern int x,y,w,h;
extern ColorMode color_mode;
extern volatile int lost_count;

void Pto_Data_Receive(uint8_t Rx_Temp);
void Pto_Data_Parse(uint8_t *data_buf, uint8_t num);
void Pto_Clear_CMD_Flag(void);
void Pto_Loop(void);
void ParseCommonFields(
    int func_index,      
    uint8_t *data_buf,   
    uint8_t num,         
    uint8_t *field_index,
    uint8_t data_index,  
    int* values,         
    char msgs[][PTO_BUF_LEN_MAX]         
);
    
void HandleColor(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleBarcode(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleQRCode(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleAprilTag(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleDMCode(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleFaceDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleEyeGaze(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleFaceRecognition(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandlePersonDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleFallDown(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleHandDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleHandGesture(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleOCRRec(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleObjectDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleNanoTracker(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleSelfLearning(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleLicenceRec(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleLicenceDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleGarbageDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleGuideDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleObstacleDetect(int* values, char msgs[][PTO_BUF_LEN_MAX]);
void HandleMultiColorRec(int* values, char msgs[][PTO_BUF_LEN_MAX]);


#endif
