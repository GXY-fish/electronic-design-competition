/**
 * @file    fuzzy_pid.h
 * @brief   飞思卡尔模糊 PD 控制器 — 自适应巡线转向
 *
 *          输入:  E (位置偏差), EC (偏差变化率)
 *          输出:  turn (转向修正量)
 *
 *          7 级隶属度: NB NM NS ZO PS PM PB
 *          49 条规则 + 重心法解模糊
 */

#ifndef __FUZZY_PID_H
#define __FUZZY_PID_H

/* 模糊控制器对象 */
typedef struct
{
    float   Ke;       /* E  量化因子  (输入缩放) */
    float   Kec;      /* EC 量化因子  (输入缩放) */
    float   Ku;       /* U  比例因子  (输出缩放) */

    float   e;        /* 当前误差 (原始值) */
    float   ec;       /* 当前误差变化率 (原始值) */
    float   output;   /* 模糊推理输出 */

} FuzzyPD_t;

void  FuzzyPD_Init(FuzzyPD_t *f, float Ke, float Kec, float Ku);
float FuzzyPD_Compute(FuzzyPD_t *f, float error, float derivative);

#endif /* __FUZZY_PID_H */
