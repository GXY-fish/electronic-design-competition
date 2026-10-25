#ifndef __OLED_FONT_H
#define __OLED_FONT_H

// 自绘 6x8 点阵字模（仅下列字符，未收录字符以占位框显示）
//   每字符 6 字节 = 6 列，每字节 1 列，MSB 为顶行(bit7=row0)
// 收录：空格 / 数字 0-9 / 字母 A-Z,a-z / 标点 ':' '+' '-' '.'
// 字模数据定义在 OLED.c 中（const 数组 OLED_Font），此处仅声明宽度。
#define OLED_FONT_W 6

#endif
