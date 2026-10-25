#ifndef __KEY_H__
#define __KEY_H__


#include "ti_msp_dl_config.h"
#define key0 DL_GPIO_readPins(KEY_PORT, KEY_KEY1_PIN_A23_PIN)
#define key1 DL_GPIO_readPins(KEY_PORT, KEY_KEY2_PIN_A21_PIN)
#define key2 DL_GPIO_readPins(KEY_PORT, KEY_KEY4_PIN_A17_PIN)


#endif
