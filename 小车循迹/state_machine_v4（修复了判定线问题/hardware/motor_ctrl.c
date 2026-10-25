/**
 * @file    motor_ctrl.c
 * @brief   4 通道电机控制 + PID 控制器
 *          PWM TIMA0: C0=PA0(M1), C1=PA1(M2), C2=PA15(M3), C3=PB24(M4)
 *          Dir: M1(PA7/8), M2(PA12/13), M3(PB15/16), M4(PB17/18)
 */

#include "motor_ctrl.h"

/* 电机使能标志 */
uint8_t MOTOR1_ENABLE_FLAG = 0;
uint8_t MOTOR2_ENABLE_FLAG = 0;
uint8_t MOTOR3_ENABLE_FLAG = 0;
uint8_t MOTOR4_ENABLE_FLAG = 0;

uint8_t Turn_PID_Flag     = 0;
uint8_t Distance_PID_Flag = 0;

/* ---- PID 实例 (分别对应4个电机速度环 + 差速转向 + 距离) ---- */

pid_t pid_Motor1_Speed = {
    .Kp = 100, .Ki = 20, .Kd = 10,
    .Target = 0, .Measure = 0,
    .Error = {0,0,0},
    .KpOut = 0, .KiOut = 0, .KdOut = 0, .PID_Out = 0,
    .PID_Limit_MAX = 1000, .Ki_Limit_MAX = 1000,
};

pid_t pid_Motor2_Speed = {
    .Kp = 100, .Ki = 20, .Kd = 10,
    .Target = 0, .Measure = 0,
    .Error = {0,0,0},
    .KpOut = 0, .KiOut = 0, .KdOut = 0, .PID_Out = 0,
    .PID_Limit_MAX = 1000, .Ki_Limit_MAX = 1000,
};

pid_t pid_Motor3_Speed = {
    .Kp = 100, .Ki = 20, .Kd = 10,
    .Target = 0, .Measure = 0,
    .Error = {0,0,0},
    .KpOut = 0, .KiOut = 0, .KdOut = 0, .PID_Out = 0,
    .PID_Limit_MAX = 1000, .Ki_Limit_MAX = 1000,
};

pid_t pid_Motor4_Speed = {
    .Kp = 100, .Ki = 20, .Kd = 10,
    .Target = 0, .Measure = 0,
    .Error = {0,0,0},
    .KpOut = 0, .KiOut = 0, .KdOut = 0, .PID_Out = 0,
    .PID_Limit_MAX = 1000, .Ki_Limit_MAX = 1000,
};

pid_t pid_Turn = {
    .Kp = 5, .Ki = 0, .Kd = 20,
    .Target = 0, .Measure = 0,
    .Error = {0,0,0},
    .KpOut = 0, .KiOut = 0, .KdOut = 0, .PID_Out = 0,
    .PID_Limit_MAX = 1000, .Ki_Limit_MAX = 1000,
};

pid_t pid_Distance = {
    .Kp = 10, .Ki = 0, .Kd = 5,
    .Target = 0, .Measure = 0,
    .Error = {0,0,0},
    .KpOut = 0, .KiOut = 0, .KdOut = 0, .PID_Out = 0,
    .PID_Limit_MAX = 1000, .Ki_Limit_MAX = 1000,
};

/* ---- PID 限幅 ---- */
static void PID_Limit(float *a, float ABS_MAX)
{
    if (*a > ABS_MAX) *a = ABS_MAX;
    if (*a < -ABS_MAX) *a = -ABS_MAX;
}

float PID_Calculate(pid_t *pid, float Measure, float Target)
{
    pid->Target  = Target;
    pid->Measure = Measure;
    pid->Error[0] = Target - Measure;

    pid->KpOut = pid->Kp * pid->Error[0];
    pid->KiOut += pid->Ki * pid->Error[0];
    PID_Limit(&pid->KiOut, pid->Ki_Limit_MAX);
    pid->KdOut = pid->Kd * (pid->Error[0] - pid->Error[1]);

    pid->PID_Out = pid->KpOut + pid->KiOut + pid->KdOut;
    PID_Limit(&pid->PID_Out, pid->PID_Limit_MAX);

    pid->Error[2] = pid->Error[1];
    pid->Error[1] = pid->Error[0];

    return pid->PID_Out;
}

void Set_PID_Param(pid_t *pid, float P, float I, float D)
{
    pid->Kp = P; pid->Ki = I; pid->Kd = D;
    pid->KpOut = 0; pid->KiOut = 0; pid->KdOut = 0; pid->PID_Out = 0;
}

/* ---- PWM 限幅 ---- */
static void PWM_Limit(int *a, int ABS_MAX)
{
    if (*a > ABS_MAX) *a = ABS_MAX;
    if (*a < -ABS_MAX) *a = -ABS_MAX;
}

/* ---- 单电机 PWM 控制 ---- */
#define PWM_MAX 1000    /* 与 SysConfig PWM Period Count 一致 */

static void Set_Motor_PWM(uint32_t ccIdx, int Target_PWM)
{
    PWM_Limit(&Target_PWM, PWM_MAX);
    /* Edge-aligned Down 模式: CC=PERIOD→0%, CC=0→100%, 需反转 */
    DL_TimerA_setCaptureCompareValue(PWM_0_INST,
        (uint32_t)(PWM_MAX - Target_PWM), ccIdx);
}

/* ---- 4 路电机速度控制 ---- */

void Set_Motor1_Speed(int Target_Speed)
{
    if (MOTOR1_ENABLE_FLAG == 1) {
        if (Target_Speed >= 0) {
            Set_Motor_PWM(GPIO_PWM_0_C0_IDX, Target_Speed);
            Motor1_Forward();
        } else {
            Set_Motor_PWM(GPIO_PWM_0_C0_IDX, -Target_Speed);
            Motor1_Backward();
        }
    } else {
        Motor1_Brake();
        pid_Motor1_Speed.KpOut = 0; pid_Motor1_Speed.KiOut = 0;
        pid_Motor1_Speed.KdOut = 0; pid_Motor1_Speed.PID_Out = 0;
    }
}

void Set_Motor2_Speed(int Target_Speed)
{
    if (MOTOR2_ENABLE_FLAG == 1) {
        if (Target_Speed >= 0) {
            Set_Motor_PWM(GPIO_PWM_0_C1_IDX, Target_Speed);
            Motor2_Forward();
        } else {
            Set_Motor_PWM(GPIO_PWM_0_C1_IDX, -Target_Speed);
            Motor2_Backward();
        }
    } else {
        Motor2_Brake();
        pid_Motor2_Speed.KpOut = 0; pid_Motor2_Speed.KiOut = 0;
        pid_Motor2_Speed.KdOut = 0; pid_Motor2_Speed.PID_Out = 0;
    }
}

void Set_Motor3_Speed(int Target_Speed)
{
    if (MOTOR3_ENABLE_FLAG == 1) {
        if (Target_Speed >= 0) {
            Set_Motor_PWM(GPIO_PWM_0_C2_IDX, Target_Speed);
            Motor3_Forward();
        } else {
            Set_Motor_PWM(GPIO_PWM_0_C2_IDX, -Target_Speed);
            Motor3_Backward();
        }
    } else {
        Motor3_Brake();
        pid_Motor3_Speed.KpOut = 0; pid_Motor3_Speed.KiOut = 0;
        pid_Motor3_Speed.KdOut = 0; pid_Motor3_Speed.PID_Out = 0;
    }
}

void Set_Motor4_Speed(int Target_Speed)
{
    if (MOTOR4_ENABLE_FLAG == 1) {
        if (Target_Speed >= 0) {
            Set_Motor_PWM(GPIO_PWM_0_C3_IDX, Target_Speed);
            Motor4_Forward();
        } else {
            Set_Motor_PWM(GPIO_PWM_0_C3_IDX, -Target_Speed);
            Motor4_Backward();
        }
    } else {
        Motor4_Brake();
        pid_Motor4_Speed.KpOut = 0; pid_Motor4_Speed.KiOut = 0;
        pid_Motor4_Speed.KdOut = 0; pid_Motor4_Speed.PID_Out = 0;
    }
}

/* ---- 批量 4 路速度设定 ---- */
void SET_MOTORS_SPEED(int s1, int s2, int s3, int s4)
{
    Set_Motor1_Speed(s1);
    Set_Motor2_Speed(s2);
    Set_Motor3_Speed(s3);
    Set_Motor4_Speed(s4);
}

/**
 * @brief 差速控制（四驱）
 *        M1=左前, M2=右前, M3=左后, M4=右后
 *        baseSpeed: 基础速度
 *        diff: 差速量 (正值右转, 负值左转)
 */
void SET_MOTORS_SPEED_DIFF(int baseSpeed, int diff)
{
    int leftSpeed  = baseSpeed - diff;   /* 左侧: M1, M3 */
    int rightSpeed = baseSpeed + diff;   /* 右侧: M2, M4 */

    Set_Motor1_Speed(leftSpeed);
    Set_Motor3_Speed(leftSpeed);
    Set_Motor2_Speed(rightSpeed);
    Set_Motor4_Speed(rightSpeed);
}
