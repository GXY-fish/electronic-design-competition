#include "yb_protocol.h"

#define K230Serial  Serial 

void setup()
{
  K230Serial.begin(115200);
  Pto_Clear_CMD_Flag();
}

void loop()
{
  
  while(K230Serial.available())
  {
    Pto_Data_Receive(K230Serial.read());
    Pto_Loop();
   }
  
} 
