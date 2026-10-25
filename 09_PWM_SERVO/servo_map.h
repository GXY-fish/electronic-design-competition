#ifndef SERVO_MAP_H
#define SERVO_MAP_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define SERVO_MAP_MAX_POINTS 8U

typedef struct {
    float angle_deg;
    uint16_t pulse_us;
} ServoMapPoint;

typedef struct {
    ServoMapPoint points[SERVO_MAP_MAX_POINTS];
    size_t count;
    bool valid;
} ServoMap;

bool ServoMap_Init(ServoMap *map, const ServoMapPoint *points, size_t count);
uint16_t ServoMap_AngleToPulse(const ServoMap *map, float angle_deg);

#endif
