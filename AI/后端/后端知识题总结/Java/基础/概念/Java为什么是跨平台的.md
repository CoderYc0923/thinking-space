跨平台依赖的是 **「字节码 + 各平台各自的 JVM 实现」**，不是源码直接到处跑。

1. `.java` 被 `javac` 编译成统一的 `.class` 字节码（与 OS/CPU 无关）
2. 不同系统安装对应平台的 JVM（Windows / Linux / macOS 实现不同）
3. JVM 加载字节码后：**解释执行**，热点再 **JIT** 成本地机器码

所以：**一次编译，到处运行**——换平台换的是 JVM，不用改业务源码、也不用重新针对每台机器写机器码。

![](https://cdn.xiaolincoding.com//picgo/1713860588639-bb89fc8e-30b6-4d18-a329-f3fea52c729a.png)
