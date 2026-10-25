#include "servo_map.h"

#include <math.h>

bool ServoMap_Init(ServoMap *map, const ServoMapPoint *points, size_t count)
{
    size_t i;

    if ((map == NULL) || (points == NULL) || (count < 2U) ||
        (count > SERVO_MAP_MAX_POINTS)) {
        return false;
    }

    map->valid = false;
    map->count = 0U;

    for (i = 1U; i < count; ++i) {
        if (!(points[i].angle_deg > points[i - 1U].angle_deg)) {
            return false;
        }
    }

    for (i = 0U; i < count; ++i) {
        map->points[i] = points[i];
    }
    map->count = count;
    map->valid = true;
    return true;
}

uint16_t ServoMap_AngleToPulse(const ServoMap *map, float angle_deg)
{
    size_t i;

    if ((map == NULL) || !map->valid || (map->count < 2U)) {
        return 1500U;
    }

    if (angle_deg <= map->points[0].angle_deg) {
        return map->points[0].pulse_us;
    }
    if (angle_deg >= map->points[map->count - 1U].angle_deg) {
        return map->points[map->count - 1U].pulse_us;
    }

    for (i = 1U; i < map->count; ++i) {
        if (angle_deg <= map->points[i].angle_deg) {
            const ServoMapPoint *low = &map->points[i - 1U];
            const ServoMapPoint *high = &map->points[i];
            const float ratio =
                (angle_deg - low->angle_deg) /
                (high->angle_deg - low->angle_deg);
            const float pulse =
                (float)low->pulse_us +
                ratio * ((float)high->pulse_us - (float)low->pulse_us);
            return (uint16_t)lroundf(pulse);
        }
    }

    return map->points[map->count - 1U].pulse_us;
}
