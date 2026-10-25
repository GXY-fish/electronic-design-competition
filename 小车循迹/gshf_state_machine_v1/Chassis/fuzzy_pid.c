/**
 * @file    fuzzy_pid.c
 * @brief   飞思卡尔模糊 PD — 7 级隶属度 + 49 规则 + 重心法
 *
 *          ┌──────────────────────────────────────┐
 *          │  E  → Ke  → E'  ┐                    │
 *          │                  ├→ 模糊推理 → U' → Ku → turn │
 *          │ EC  → Kec → EC' ┘                    │
 *          └──────────────────────────────────────┘
 *
 *          隶属度函数: 三角形 (trimf)
 *          规则表:     如 Freescale 标准 PD 规则
 *          解模糊:     重心法 (centroid)
 */

#include "fuzzy_pid.h"
#include <math.h>
#include <string.h>
#include <stdint.h>

/* ================================================================
 * 模糊论域等级 (标准化的 7 级)
 * ================================================================ */

#define NB  -3
#define NM  -2
#define NS  -1
#define ZO   0
#define PS   1
#define PM   2
#define PB   3

/* ================================================================
 * 三角形隶属度函数
 *   trimf(x, a, b, c): a=左底, b=顶点, c=右底
 *   返回值 ∈ [0, 1]
 * ================================================================ */

static float trimf(float x, float a, float b, float c)
{
    if (x <= a || x >= c) return 0.0f;
    if (x == b)           return 1.0f;
    if (x > a && x < b)   return (x - a) / (b - a);
    return (c - x) / (c - b);   /* x > b && x < c */
}

/* ================================================================
 * 对输入 x (∈ [-3, 3]) 计算 7 级隶属度
 *   mu[0..6] = {NB, NM, NS, ZO, PS, PM, PB}
 * ================================================================ */

static void fuzzify(float x, float mu[7])
{
    mu[0] = trimf(x, -4.0f, -3.0f, -2.0f);  /* NB */
    mu[1] = trimf(x, -3.0f, -2.0f, -1.0f);  /* NM */
    mu[2] = trimf(x, -2.0f, -1.0f,  0.0f);  /* NS */
    mu[3] = trimf(x, -1.0f,  0.0f,  1.0f);  /* ZO */
    mu[4] = trimf(x,  0.0f,  1.0f,  2.0f);  /* PS */
    mu[5] = trimf(x,  1.0f,  2.0f,  3.0f);  /* PM */
    mu[6] = trimf(x,  2.0f,  3.0f,  4.0f);  /* PB */
}

/* ================================================================
 * 模糊规则表 (7×7 → 输出等级)
 *
 *   E\EC  NB  NM  NS  ZO  PS  PM  PB
 *   NB    NB  NB  NB  NB  NM  NS  ZO
 *   NM    NB  NB  NB  NM  NS  ZO  PS
 *   NS    NB  NB  NM  NS  ZO  PS  PM
 *   ZO    NB  NM  NS  ZO  PS  PM  PB
 *   PS    NM  NS  ZO  PS  PM  PB  PB
 *   PM    NS  ZO  PS  PM  PB  PB  PB
 *   PB    ZO  PS  PM  PB  PB  PB  PB
 *
 *   思想:
 *   - 误差大 + 误差在增大 → 大力纠偏 (NB/PB)
 *   - 误差小 + 变化小     → 小力微调 (NS/PS)
 *   - 误差大 + 正在回正   → 减小输出防止超调
 * ================================================================ */

static const int8_t rule_table[7][7] = {
    /* EC: NB   NM   NS   ZO   PS   PM   PB   ← EC 列 */
    {   NB,  NB,  NB,  NB,  NM,  NS,  ZO },  /* E=NB */
    {   NB,  NB,  NB,  NM,  NS,  ZO,  PS },  /* E=NM */
    {   NB,  NB,  NM,  NS,  ZO,  PS,  PM },  /* E=NS */
    {   NB,  NM,  NS,  ZO,  PS,  PM,  PB },  /* E=ZO */
    {   NM,  NS,  ZO,  PS,  PM,  PB,  PB },  /* E=PS */
    {   NS,  ZO,  PS,  PM,  PB,  PB,  PB },  /* E=PM */
    {   ZO,  PS,  PM,  PB,  PB,  PB,  PB },  /* E=PB */
};

/* ================================================================
 * 重心法解模糊 (centroid)
 *   U = Σ(μ_i × level_i) / Σ(μ_i)
 *   level_i ∈ {-3, -2, -1, 0, 1, 2, 3}
 * ================================================================ */

static float defuzzify(float strength[7])
{
    float num = 0.0f, den = 0.0f;
    for (int i = 0; i < 7; i++)
    {
        float lvl = (float)(i - 3);  /* -3, -2, -1, 0, 1, 2, 3 */
        num += strength[i] * lvl;
        den += strength[i];
    }
    if (den < 1e-6f) return 0.0f;
    return num / den;   /* ∈ [-3, 3] */
}

/* ================================================================
 * 模糊推理: E' × EC' → 输出强度 (min-max 推理)
 * ================================================================ */

static float fuzzy_infer(float muE[7], float muEC[7])
{
    float out_strength[7] = {0};

    for (int i = 0; i < 7; i++)         /* E 维度 */
    {
        if (muE[i] < 1e-6f) continue;

        for (int j = 0; j < 7; j++)     /* EC 维度 */
        {
            if (muEC[j] < 1e-6f) continue;

            /* min 推理 */
            float fire = (muE[i] < muEC[j]) ? muE[i] : muEC[j];

            int k = rule_table[i][j] + 3;  /* 映射到 0..6 */

            /* max 合成 */
            if (fire > out_strength[k])
                out_strength[k] = fire;
        }
    }

    return defuzzify(out_strength);
}

/* ================================================================
 * 初始化
 * ================================================================ */

void FuzzyPD_Init(FuzzyPD_t *f, float Ke, float Kec, float Ku)
{
    memset(f, 0, sizeof(*f));
    f->Ke  = Ke;
    f->Kec = Kec;
    f->Ku  = Ku;
}

/* ================================================================
 * 一次模糊 PD 计算
 *   error      原始偏差 (如 -3.5~3.5)
 *   derivative 偏差变化率
 *   返回       转向修正量
 * ================================================================ */

float FuzzyPD_Compute(FuzzyPD_t *f, float error, float derivative)
{
    f->e  = error;
    f->ec = derivative;

    /* 量化到模糊论域 [-3, 3] */
    float e_q  = f->Ke  * error;
    float ec_q = f->Kec * derivative;

    /* 限幅 */
    if (e_q  >  3.0f) e_q  =  3.0f;
    if (e_q  < -3.0f) e_q  = -3.0f;
    if (ec_q >  3.0f) ec_q =  3.0f;
    if (ec_q < -3.0f) ec_q = -3.0f;

    /* 模糊化 */
    float muE[7], muEC[7];
    fuzzify(e_q,  muE);
    fuzzify(ec_q, muEC);

    /* 推理 + 解模糊 */
    float u = fuzzy_infer(muE, muEC);  /* ∈ [-3, 3] */

    /* 反量化 */
    f->output = f->Ku * u;

    return f->output;
}
