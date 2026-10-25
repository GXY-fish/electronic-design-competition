#include "ti_msp_dl_config.h"
#include "stdio.h"
#include "usart.h"
#include "yb_protocol.h"


int main(void)
{
    SYSCFG_DL_init(); 
    uart0_init();
    uart2_init();

    uart0_send_char(0x32);
    uart0_send_char(0x32);
    uart0_send_char(0x33);


    while(1)
    {
    }
}


