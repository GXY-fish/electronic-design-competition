#ifndef BALL_APP_H
#define BALL_APP_H

#include <stdint.h>

void BallBalanceApp_Init(void);
void BallBalanceApp_OnUartRxByte(uint8_t byte);
void BallBalanceApp_Update20ms(void);
void Ball_SetReference(float target_mm);

#endif
