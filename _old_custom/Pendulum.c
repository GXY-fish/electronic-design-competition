#include "stm32f10x.h"
#include "Pendulum.h"
#include <math.h>

// ---- 编码器分辨率(每转计数, TI12 四倍频) ----
// 常用 11 线/13 线正交编码器 -> 11*4=44 / 13*4=52 计数每转
// 按你实际编码器改这两个值
#define ARM_PPR   52      // 臂角编码器每转计数 (TIM3, PA6/PA7)
#define DEG_PER_CNT_ARM  (360.0f / (float)ARM_PPR)

// ---- 摆杆电位器参数 (SENSOR1 -> PB0 = ADC1_IN8) ----
// 360°电位器, 0~3.3V 对应 0~360°, ADC 12bit -> 360/4095 °/LSB
// 实际斜率可能因电位器行程/安装略有偏差, 上板后可校准
#define PEND_ADC_DEG_PER_LSB  (360.0f / 4095.0f)

// ---- ADC 抗噪: 高阻电位器必须"长采样 + 过采样" ----
// 与江协 7-1 的区别: 江协测的是 PA0 上低阻电位器, 55.5 周期就稳;
// 本板摆杆电位器在 PB0, 源阻抗更高(长线/360°电位器), 55.5 周期充电不足 -> 读数带噪声。
// 修法: 采样时间拉到最长 239.5 周期 + 每次读内部 8 次过采样平均(噪声约降到 1/2.8)。
#define PEND_ADC_SAMPLE_CYC  ADC_SampleTime_239Cycles5
#define PEND_ADC_OVERSAMPLE  8u    // 每次读取内部过采样次数(硬件平均, 抑制电位器噪声)

// ---- 滤波 / 零位跟踪 ----
#define PEND_FILT_A      0.80f   // 角度 EMA: y = A*y + (1-A)*x (时间常数≈25ms)
#define ZERO_AVG_SAMPLES 128u    // 上电零位采样平均次数
#define ZERO_TRACK_GAIN 0.01f   // 空闲时零位跟踪增益(由 main 约每 50ms 调一次 -> 时间常数≈5s)

static float g_armDeg     = 0;   // 臂绝对角(度)
static float g_pendRelDeg = 0;   // 摆杆相对臂角(度)
static float g_pendRelDegU = 0;   // ★360°电位器解卷后的连续摆角(度): 折叠±180跳变得连续, 杜绝 pk=335 失真
static float g_theta      = 0;   // 当前原始摆角(度, 0=下垂)
static float g_thetaFilt  = 0;   // EMA 滤波后摆角(给显示与控制用)
static float g_thetaPrevF = 0;
static float g_thetaDot   = 0;   // 角速度(度/秒)

static float    g_adcZero = 2048.0f; // 下垂零位对应 ADC 值(浮点, 可带小数跟踪)
static uint16_t g_adcRaw  = 2048;    // 最近一次原始 ADC(诊断用)

// 通用正交编码器初始化 (TI12 四倍频, 计数器清零)
static void Encoder_InitTIM(TIM_TypeDef *TIMx, GPIO_TypeDef *GPIOx,
                            uint16_t Pin1, uint16_t Pin2)
{
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOB, ENABLE);
    if (TIMx == TIM1)      RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM1, ENABLE);
    else if (TIMx == TIM3)  RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);

    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_InitStructure.GPIO_Pin = Pin1 | Pin2;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOx, &GPIO_InitStructure);

    TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure;
    TIM_TimeBaseStructInit(&TIM_TimeBaseInitStructure);
    TIM_TimeBaseInitStructure.TIM_Period = 65536 - 1;
    TIM_TimeBaseInit(TIMx, &TIM_TimeBaseInitStructure);

    TIM_ICInitTypeDef TIM_ICInitStructure;
    TIM_ICStructInit(&TIM_ICInitStructure);
    TIM_ICInitStructure.TIM_ICFilter = 0xF;
    TIM_ICInitStructure.TIM_Channel = TIM_Channel_1;
    TIM_ICInit(TIMx, &TIM_ICInitStructure);
    TIM_ICInitStructure.TIM_Channel = TIM_Channel_2;
    TIM_ICInit(TIMx, &TIM_ICInitStructure);

    TIM_EncoderInterfaceConfig(TIMx, TIM_EncoderMode_TI12, TIM_ICPolarity_Rising, TIM_ICPolarity_Rising);
    TIM_SetCounter(TIMx, 0);
    TIM_Cmd(TIMx, ENABLE);
}

// ADC1 单通道读取 (channel 8 = PB0), 内部 8 次过采样平均。
// 注意: 通道配置只在 Pendulum_ADC_Init 里做一次(与江协 7-1 例程一致),
// 这里只做 软件触发 -> 等 EOC -> 取结果, 不在每次读时重复配置(避免隐患)。
// 过采样: 连续采 PEND_ADC_OVERSAMPLE 次后取平均, 显著降低高阻电位器噪声。
static uint16_t ADC1_ReadChannel8(void)
{
    uint32_t sum = 0;
    for (uint8_t i = 0; i < PEND_ADC_OVERSAMPLE; i++)
    {
        ADC_SoftwareStartConvCmd(ADC1, ENABLE);
        while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);
        sum += ADC_GetConversionValue(ADC1);
    }
    return (uint16_t)(sum / PEND_ADC_OVERSAMPLE);
}

static void Pendulum_ADC_Init(void)
{
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1 | RCC_APB2Periph_GPIOB, ENABLE);
    RCC_ADCCLKConfig(RCC_PCLK2_Div6);               // 72/6 = 12MHz ADC 时钟

    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;   // 模拟输入
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    ADC_InitTypeDef ADC_InitStructure;
    ADC_StructInit(&ADC_InitStructure);
    ADC_InitStructure.ADC_Mode = ADC_Mode_Independent;
    ADC_InitStructure.ADC_ScanConvMode = DISABLE;
    ADC_InitStructure.ADC_ContinuousConvMode = DISABLE;
    ADC_InitStructure.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;
    ADC_InitStructure.ADC_DataAlign = ADC_DataAlign_Right;
    ADC_InitStructure.ADC_NbrOfChannel = 1;
    ADC_Init(ADC1, &ADC_InitStructure);

    // 规则组通道配置: 仅上电做一次(与江协 7-1 一致), 不要在每次读取时重复配置
    // 采样时间用最长 239.5 周期(高阻电位器需要充足充电时间, 否则读数带噪声)
    ADC_RegularChannelConfig(ADC1, ADC_Channel_8, 1, PEND_ADC_SAMPLE_CYC);

    ADC_Cmd(ADC1, ENABLE);

    // 复位校准
    ADC_ResetCalibration(ADC1);
    while (ADC_GetResetCalibrationStatus(ADC1) == SET);
    ADC_StartCalibration(ADC1);
    while (ADC_GetCalibrationStatus(ADC1) == SET);
}

void Pendulum_Init(void)
{
    Encoder_InitTIM(TIM3, GPIOA, GPIO_Pin_6, GPIO_Pin_7); // 臂角编码器 (TIM3)
    Pendulum_ADC_Init();                                   // 摆杆电位器 (ADC1_IN8 / PB0)
    Pendulum_Zero();
}

// 把"当前摆杆位置"记为 0°(假设此刻处于自然下垂)。
// 上电零位用 128 次平均, 消除单次采样噪声。
// 注: 请在上电时让摆杆处于自然下垂, 否则 0° 会带一个固定偏移。
// 另外: 按 K1 启动 swing 时会再次调用本函数重新取零位。
void Pendulum_Zero(void)
{
    TIM_SetCounter(TIM3, 0);
    uint32_t sum = 0;
    for (uint16_t i = 0; i < ZERO_AVG_SAMPLES; i++) sum += ADC1_ReadChannel8();
    g_adcZero = (float)(sum / ZERO_AVG_SAMPLES);
    g_adcRaw  = (uint16_t)g_adcZero;
    g_armDeg = g_pendRelDeg = g_pendRelDegU = g_theta = g_thetaFilt = g_thetaPrevF = g_thetaDot = 0;
}

// 每个控制节拍(5ms)调用: 读臂角编码器 + 读摆杆电位器 -> 绝对摆角与角速度
void Pendulum_Update(void)
{
    int16_t dArm  = (int16_t)TIM_GetCounter(TIM3); TIM_SetCounter(TIM3, 0);
    g_armDeg += dArm * DEG_PER_CNT_ARM;   // 臂方位角(预留: 后续平衡控制用, 不参与起摆角度)

    uint16_t adc = ADC1_ReadChannel8();
    g_adcRaw = adc;
    // 相对下垂零位的原始角(±180°内)
    float raw = ((float)(int16_t)adc - g_adcZero) * PEND_ADC_DEG_PER_LSB;
    // ★ 360°电位器解卷: 摆杆摆过电位器间隙时 ADC 会突跳 ±360°, 直接相减会得到错角(旧版 pk=335 失真由来)。
    //   用"本次增量折叠到 ±180°"累加成连续角, 任何单点跳变都被吸收, 摆角始终连续可信。
    float d = raw - g_pendRelDegU;
    while (d >  180.0f) d -= 360.0f;
    while (d < -180.0f) d += 360.0f;
    g_pendRelDegU += d;
    g_pendRelDeg = g_pendRelDegU;

    // 旋转倒立摆: 摆杆绝对摆角 = 摆杆相对"下垂"的转角(仅由电位器决定),
    // 与臂方位角无关 —— 电机只转臂方位, 不会直接抬高摆杆
    g_theta = THETA_SIGN * g_pendRelDeg;

    // EMA 滤波(降噪, 也让角速度更稳)
    g_thetaFilt = PEND_FILT_A * g_thetaFilt + (1.0f - PEND_FILT_A) * g_theta;

    // 角速度(用滤波后角度)
    g_thetaDot = (g_thetaFilt - g_thetaPrevF) / CONTROL_TS;
    g_thetaPrevF = g_thetaFilt;
}

// 只把【臂角参考】归零到当前物理位置(TIM3 计数清0 + g_armDeg清0),
// 不碰摆杆零位/角度(摆杆此刻可能已微微起摆, 零位须保持=真下垂).
// 用于起摆前标定完编码器后, 让正弦目标以当前臂位为 0 中心往复.
void Pendulum_ZeroArm(void)
{
    TIM_SetCounter(TIM3, 0);
    g_armDeg = 0;
}

// 空闲时由 main 周期调用(约每 50ms): 极缓慢把零位拉向当前 ADC, 抵消热漂移。
// 仅在空闲(摆杆本就挂着)时跟踪; 运行中不调用, 零位不会被摆动角度带偏。
void Pendulum_TrackZero(void)
{
    g_adcZero += ((float)g_adcRaw - g_adcZero) * ZERO_TRACK_GAIN;
}

float   Pendulum_GetAngle(void)   { return g_thetaFilt; }
float   Pendulum_GetSpeed(void)   { return g_thetaDot; }
float   Pendulum_GetArmAngle(void){ return g_armDeg; }   // 臂方位角(度), 稳摆位置环用
uint16_t Pendulum_GetRawAdc(void) { return g_adcRaw; }
