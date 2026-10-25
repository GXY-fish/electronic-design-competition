#ifndef VISION_PROTOCOL_H
#define VISION_PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define VISION_PACKET_SIZE 15U
#define VISION_MEASUREMENT_VALID 0x01U
#define VISION_MEASUREMENT_LOST  0x02U
#define VISION_MEASUREMENT_CAL_OK 0x04U

typedef struct {
    uint8_t sequence;
    uint16_t camera_timestamp_ms;
    float x_mm;
    float v_mm_s;
    float v_diff_mm_s;
    uint8_t confidence;
    uint8_t flags;
    uint32_t received_ms;
} VisionMeasurement;

typedef struct {
    uint8_t frame[VISION_PACKET_SIZE];
    size_t index;
    VisionMeasurement latest;
    bool has_latest;
} VisionProtocol;

void VisionProtocol_Init(VisionProtocol *protocol);
uint8_t VisionProtocol_Crc8(const uint8_t *data, size_t length);
bool VisionProtocol_PushByte(VisionProtocol *protocol,
                             uint8_t byte,
                             uint32_t received_ms);
bool VisionProtocol_GetLatest(const VisionProtocol *protocol,
                              VisionMeasurement *measurement);
bool VisionMeasurement_IsUsable(const VisionMeasurement *measurement,
                                uint32_t now_ms);

#endif
