![](https://cdn.xiaolincoding.com//picgo/image-20240725230247664.png)

- JVM是java虚拟机，是Java程序运行的环境。
  - 它负责将Java字节码（Java编译器javac生成）编译成机器码，并执行程序。使得Java程序具备跨平台性
  - JVM提供了内存管理、垃圾回收、安全性等功能。
- JDK是Java开发工具包。
  - 包含了JVM、编译器（javac）、调试器（jdb）等开发工具，以及一系列的类库（比如标准库和开发工具库）
  - JDK提供了开发、编译、调试和运行Java程序所需的全部工具和环境
- JRE是Java运行时环境，是Java程序运行所需的最小环境。
  - 包含了JVM、类加载器、字节码验证器和一组Java类库（Swing、net、I/O等），用于支持Java程序的执行
  - JRE不包含开发工具，只提供运行时所需的运行环境