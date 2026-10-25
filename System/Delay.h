#ifndef __DELAY_H
#define __DELAY_H

#include <stdint.h>

void Delay_us(uint32_t us);  /* 微秒级阻塞延时 */
void Delay_ms(uint32_t ms);  /* 毫秒级阻塞延时 */
void Delay_s (uint32_t s);   /* 秒级阻塞延时   */

#endif
