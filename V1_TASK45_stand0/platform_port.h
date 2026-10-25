#ifndef PLATFORM_PORT_H
#define PLATFORM_PORT_H

#include <stdint.h>

uint32_t Platform_GetMillis(void);
void Platform_ServoWriteUs(uint16_t pulse_us);
void Platform_DisplayResult(uint32_t elapsed_ms,
                            float error_mm,
                            uint16_t fault_flags);

#endif
