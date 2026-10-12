![](https://cdn.xiaolincoding.com//picgo/image-20240725230247664.png)

**包含关系（由外到内）**

```
JDK ⊃ JRE ⊃ JVM
```

- **JVM（Java Virtual Machine）**：虚拟机**核心**，负责真正跑字节码。
  - 类加载子系统（类加载器）、字节码验证、链接与初始化
  - 运行时数据区（堆、栈、方法区等）
  - 执行引擎（解释器 + JIT）、垃圾回收、JNI/本地方法接口
  - 注意：类加载器、字节码验证器都是 **JVM 内部模块**，不是和 JVM 平级、单独塞在 JRE 里的东西
- **JRE（Java Runtime Environment）**：程序**运行**所需的最小环境。
  - = **JVM** + **Java 标准类库**（如 `java.lang`、`java.io`、集合、网络等）
  - 不含 javac 等开发工具；只跑程序装 JRE 即可（经典模型）
- **JDK（Java Development Kit）**：开发工具包。
  - = **JRE** + 开发工具（`javac`、`jdb`、`javadoc`、`jar` 等）
  - 开发、编译、调试、运行一整套都在 JDK

**一句话区分**

| | 干什么 | 有没有编译器 |
|---|---|---|
| JVM | 执行字节码 | 否（执行，不是 javac） |
| JRE | 跑程序（JVM + 类库） | 否 |
| JDK | 写程序 + 跑程序 | 有 javac |

**补充（面试加分）**

- Java 9 起官方不再单独发行传统 JRE，日常装的是 JDK；但「JDK ⊃ JRE ⊃ JVM」仍是常考概念模型。
- 说「JVM 把字节码变成机器码」不全面：默认是**解释执行**，热点代码再由 **JIT** 编译成本地机器码。
