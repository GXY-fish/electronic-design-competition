#include "vision_protocol.h"

#include "ball_config.h"

#include <stddef.h>

static int16_t decode_i16_le(uint8_t low, uint8_t high)
{
    const uint16_t value = (uint16_t)low | ((uint16_t)high << 8U);
    return (int16_t)value;
}

static uint16_t decode_u16_le(uint8_t low, uint8_t high)
{
    return (uint16_t)low | ((uint16_t)high << 8U);
}

static void restart_from_byte(VisionProtocol *protocol, uint8_t byte)
{
    protocol->index = 0U;
    if (byte == 0xAAU) {
        protocol->frame[0] = byte;
        protocol->index = 1U;
    }
}

void VisionProtocol_Init(VisionProtocol *protocol)
{
    if (protocol == NULL) {
        return;
    }

    protocol->index = 0U;
    protocol->has_latest = false;
    protocol->latest.sequence = 0U;
    protocol->latest.camera_timestamp_ms = 0U;
    protocol->latest.x_mm = 0.0f;
    protocol->latest.v_mm_s = 0.0f;
    protocol->latest.v_diff_mm_s = 0.0f;
    protocol->latest.confidence = 0U;
    protocol->latest.flags = 0U;
    protocol->latest.received_ms = 0U;
}

uint8_t VisionProtocol_Crc8(const uint8_t *data, size_t length)
{
    uint8_t crc = 0x00U;

    if (data == NULL) {
        return crc;
    }

    for (size_t i = 0U; i < length; ++i) {
        crc ^= data[i];
        for (uint8_t bit = 0U; bit < 8U; ++bit) {
            if ((crc & 0x80U) != 0U) {
                crc = (uint8_t)((uint8_t)(crc << 1U) ^ 0x07U);
            } else {
                crc = (uint8_t)(crc << 1U);
            }
        }
    }
    return crc;
}

bool VisionProtocol_PushByte(VisionProtocol *protocol,
                             uint8_t byte,
                             uint32_t received_ms)
{
    uint8_t crc;

    if (protocol == NULL) {
        return false;
    }

    if (protocol->index == 0U) {
        if (byte == 0xAAU) {
            protocol->frame[0] = byte;
            protocol->index = 1U;
        }
        return false;
    }

    if (protocol->index == 1U) {
        if (byte != 0x55U) {
            restart_from_byte(protocol, byte);
            return false;
        }
        protocol->frame[1] = byte;
        protocol->index = 2U;
        return false;
    }

    if (protocol->index == 2U) {
        if (byte != 0x0BU) {
            restart_from_byte(protocol, byte);
            return false;
        }
        protocol->frame[2] = byte;
        protocol->index = 3U;
        return false;
    }

    protocol->frame[protocol->index] = byte;
    protocol->index++;
    if (protocol->index < VISION_PACKET_SIZE) {
        return false;
    }

    protocol->index = 0U;
    crc = VisionProtocol_Crc8(&protocol->frame[2], 12U);
    if ((crc != protocol->frame[14]) ||
        ((protocol->frame[13] & VISION_MEASUREMENT_VALID) == 0U)) {
        return false;
    }

    protocol->latest.sequence = protocol->frame[3];
    protocol->latest.camera_timestamp_ms =
        decode_u16_le(protocol->frame[4], protocol->frame[5]);
    protocol->latest.x_mm =
        (float)decode_i16_le(protocol->frame[6], protocol->frame[7]) *
        VISION_POSITION_SIGN;
    protocol->latest.v_mm_s =
        (float)decode_i16_le(protocol->frame[8], protocol->frame[9]) *
        VISION_POSITION_SIGN;
    protocol->latest.v_diff_mm_s =
        (float)decode_i16_le(protocol->frame[10], protocol->frame[11]) *
        VISION_POSITION_SIGN;
    protocol->latest.confidence = protocol->frame[12];
    protocol->latest.flags = protocol->frame[13];
    protocol->latest.received_ms = received_ms;
    protocol->has_latest = true;
    return true;
}

bool VisionProtocol_GetLatest(const VisionProtocol *protocol,
                              VisionMeasurement *measurement)
{
    if ((protocol == NULL) || (measurement == NULL) ||
        !protocol->has_latest) {
        return false;
    }

    *measurement = protocol->latest;
    return true;
}

bool VisionMeasurement_IsUsable(const VisionMeasurement *measurement,
                                uint32_t now_ms)
{
    if (measurement == NULL) {
        return false;
    }

    return ((measurement->flags & VISION_MEASUREMENT_VALID) != 0U) &&
           (measurement->confidence >= VISION_CONFIDENCE_MIN) &&
           ((uint32_t)(now_ms - measurement->received_ms) <=
            BALL_VISION_TIMEOUT_MS);
}
