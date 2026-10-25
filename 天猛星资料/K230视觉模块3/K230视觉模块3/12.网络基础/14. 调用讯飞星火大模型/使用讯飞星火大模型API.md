# 使用讯飞星火大模型 API

[TOC]

## 讯飞星火大模型简介

讯飞星火大模型是科大讯飞推出的一款基于多模、多能力的AI大语言模型，支持语音识别、语音合成、语义理解、知识问答、代码生成等多种场景和应用。

Yahboom K230 封装的 LLM 模块集成了快速调用星火大模型的方法函数，

本节教程我们来介绍一下如何申请星火大模型的API，并在K230上调用

## 注册并申请 API

我们打开讯飞星火大模型的网站链接：

[讯飞星火大模型API-大模型API-大模型接口-科大讯飞](https://xinghuo.xfyun.cn/sparkapi)

点击登录按钮

![image-20250331172441395](1.png)

如果是首次使用，需要进行实名认证

![image-20250331172944668](2.png)

注册登录成功后，我们向下滑动，找到免费申请 API 部分

我们以 Pro版 128K 为例（更推荐申请Lite版，Lite版目前可以无限制使用，且个人感觉响应速度更快）

![image-20250331172819332](3.png)

点击免费领取后，会跳转至订单页面。

我们点击 “+” 号，添加一个应用

![image-20250331173526165](4.png)

应用信息可以随意填写。填写完成后我们点击提交按钮

![image-20250331173647095](5.png)

会到订单页面后，勾选一下确认同意协议，然后点击确认下单

![image-20250331173821217](add1.png)





## 在控制台中查询API

点击左侧的Spark Pro-128K (如果申请的是lite模型，则点击Spark Lite。其他模型也是同理)

![image-20250331174005036](6.png)

在控制台中，我们复制一下这个API Password

![image-20250331174214502](7.png)

## 调用讯飞星火大模型

我们使用 ybUtils.LLM 库来调用讯飞星火大模型

完整的示例代码如下

```python
from ybUtils.LLM import *

def network_use_wlan(ssid, key):
    import network
    sta = network.WLAN(0)
    sta.connect(ssid, key)
    while not sta.isconnected():
        time.sleep(1)
    return sta.ifconfig()[0]
# 测试代码
if __name__ == "__main__":

    # 连接网络
    print("等待连接网络 waiting connect to wifi")
    network_use_wlan("SSID", "PASSWORD")

    # Spark示例
    spark_api_key = "API Password"

    print("正在等待响应 ...")
    simple_chat_example(
        api_key=spark_api_key,
        prompt="给我唱首歌吧",
        model_type=LLM.MODEL_TYPE_SPARK,
        model=LLM.SPARK_MODELS["PRO_128K"]
    )

```

注意，请自行将代码中的"SSID", "PASSWORD",  "API Password" 这三部内容修改为真实的参数

点击左下角运行按钮，等待几秒钟之后

可以看到如下的输出 （ “回复” 部分不一定和下面的内容完全相同）

```
等待连接网络
连接网络成功
正在等待响应 ...
回复: 您好！我乃科大讯飞所研发的认知智能大模型，名曰讯飞星火认知大模型。我能够与人类展开自然交流，解答各类问题，并且高效地完成各领域的认知智能需求。

使用的token: 49 (输入: 4, 输出: 45)
```



## 注意事项

1. 该例程依赖于网络环境，请确保K230连接的WIFI网络能正常的访问互联网，且WIFI信号的频段为2.4Ghz
2. 测试过程中发现偶尔会出现访问超时的现象(返回-1)，属于正常情况，可以多运行几次试试（该现象在首次使用时最为明显）
