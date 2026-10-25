#include "menu.h"
#include "board.h"

uint8_t display_buf[20];



int i1 = 0;
int i2 = 0;


/**********************************************************

                     以下为一级菜单

**********************************************************/
int menu1()           
{
	int flag=1; 
   //记录你的选择
      OLED_ShowString(12,0,(uint8_t *)"1.mode1",16,1);
      OLED_ShowString(12,16,(uint8_t *)"2.mode2",16,1);
      OLED_ShowString(12,32,(uint8_t *)"3.mode3",16,1);
      OLED_ShowString(12,48,(uint8_t *)"4.mode4",16,1);
           OLED_Refresh();
	while(1)
	{


		if(key0==0)       //***下一项***
		{		
			delay_ms(1);	  //防抖
			while(key0==0); //按下后不松手，则停在这
			delay_ms(1);	  //防抖
			flag++;
			if(flag==5) flag=1;			
		}
		
		if(key1==0)       //***确认***
		{
			delay_ms(1);	  //防抖
			while(key1==0); //按下后不松手，则停在这
			delay_ms(1);	  //防抖			
			OLED_Clear();   //清屏
			return(flag);   //返回你的选择
		}
		
            switch(flag)      //光标移动
            {
               case 1:
               {
                  OLED_ShowString(0,16,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,32,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,48,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,0,(uint8_t *)"*",16,1);
                   OLED_Refresh();

               }break;
               case 2:
               {
                  OLED_ShowString(0,0,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,32,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,48,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,16,(uint8_t *)"*",16,1);
                   OLED_Refresh();

               }break;
               case 3:
               {
                  OLED_ShowString(0,0,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,16,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,48,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,32,(uint8_t *)"*",16,1);	
                   OLED_Refresh();

                  
               }break;
               case 4:
               {
                  OLED_ShowString(0,0,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,16,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,32,(uint8_t *)" ",16,1);
                  OLED_ShowString(0,48,(uint8_t *)"*",16,1);		
                     OLED_Refresh();
                  
               }break;
            }		
		
	}
}

/**********************************************************

                     以下为二级菜单

**********************************************************/
int menu2()
{
//   int i=0;
//   int i1 = 0;
      OLED_ShowString(0,0,(uint8_t *)"mode1",16,1);
      OLED_Refresh();   
   	while(1)
{

      if( key1==0) 
  { 
     delay_ms(1);//消抖
     while( key1==0) ;
     delay_ms(1);//消抖
     i1=!i1;
  }

    if(i1==1) 
  {

      OLED_ShowString(0,16,(uint8_t *)"start",16,1);   
      OLED_Refresh();     

     
     
     
     
  }
  else if(i1==0)
  {

      OLED_ShowString(0,16,(uint8_t *)"stop  ",16,1);   
      OLED_Refresh(); 
     
     
     
     
 
  }    
  
		if(key2 == 0)//***返回***
		{
			delay_ms(1);	    //防抖
			while(key2 == 0); //按下后不松手，则停在这
			delay_ms(1);	    //防抖
			OLED_Clear();
			return 0;
		}


   }
}



int menu3()
{
//   uint8_t i=0;
   OLED_ShowString(0,0,(uint8_t *)"mode2",16,1);
   
   	while(1)
	{
            if( key1 == 0) 
        {
           delay_ms(1);//消抖
           while( key1 == 0) ;
           delay_ms(1);//消抖
           i2=!i2;
        }
          if(i2==1) 
        {
      OLED_ShowString(0,16,(uint8_t *)"start",16,1);   
      OLED_Refresh();   
		Set_Pwm(50,50);			

        }
        else 
        {
      OLED_ShowString(0,16,(uint8_t *)"stop  ",16,1);   
      OLED_Refresh();
			Set_Pwm(-50,-50);
        }    
   
		if(key2 == 0)//***返回***
		{
			delay_ms(1);	    //防抖
			while(key2 == 0); //按下后不松手，则停在这
			delay_ms(1);	    //防抖
			OLED_Clear();
			return 0;
		}

   }
}

int menu4()
{
   uint8_t i=0;
      OLED_ShowString(0,0,(uint8_t *)"mode3",16,1);
      OLED_Refresh();   	
   while(1)
	{
       if( key1 == 0) 
        {
           delay_ms(1);//消抖
           while( key1 == 0) ;
           delay_ms(1);//消抖
           i=!i;
        }
          if(i==1) 
        {
      OLED_ShowString(0,16,(uint8_t *)"start",16,1);   
      OLED_Refresh();    

        }
        else 
        {
           OLED_ShowString(0,16,(uint8_t *)"stop  ",16,1);
           OLED_Refresh();
       //  Set_Pwm1(0,0);

        }   
   
		if(key2 == 0)//***返回***
		{
			delay_ms(1);	    //防抖
			while(key2 == 0); //按下后不松手，则停在这
			delay_ms(1);	    //防抖
			OLED_Clear();
			return 0;
		}


   }
}
int menu5()
{
   uint8_t i=0;
      OLED_ShowString(0,0,(uint8_t *)"mode4",16,1);
      OLED_Refresh();   	
   while(1)
	{
     
       if( key1 == 0) 
        {
           delay_ms(1);//消抖
           while( key1 == 0) ;
           delay_ms(1);//消抖
           i=!i;
        }
          if(i==1) 
        {
      OLED_ShowString(0,16,(uint8_t *)"start",16,1);   
      OLED_Refresh(); 
        
        }
        else 
        {
            OLED_ShowString(0,16,(uint8_t *)"stop  ",16,1);
            OLED_Refresh();      
        }   
      
		if(key2==0)//***返回***
		{
			delay_ms(1);	    //防抖
			while(key2 == 0); //按下后不松手，则停在这
			delay_ms(1);	    //防抖
			OLED_Clear();
			return 0;
		}


   }
}