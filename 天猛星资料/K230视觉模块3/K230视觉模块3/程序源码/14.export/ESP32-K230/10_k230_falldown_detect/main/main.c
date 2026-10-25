#include "uart1.h"
#include "yb_protocol.h"

void app_main(void)
{
    
    Uart1_Init();

    Pto_Loop();
}
