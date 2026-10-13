- `JVM`是一套虚拟计算机规范，执行.class字节码。特点是一次编译，到处运行。
  - `.java`文件被编译器`javac`编译成`.class`文件 → `ClassLoader`类加载子系统加载`.class`文件 → 运行时数据区运行 → 执行引擎（解释 + `JIT`）  →  需要时走`JNI`  → 本地方法库



- 线上问题映射
  - 内存涨  / `OOM`·：多半在【运行时数据区 + `GC`】
  - CPU高 / 变慢：可能`GC`太频繁、热点代码、业务死循环（执行引擎 + 线程）
  - 类找不到 / 热部署泄漏：类加载子系统
  - 堆看着不大但是机器内存爆了：可能`Metaspace` / 堆外 / `Native`



- `JVM`五大模块
  - 类加载子系统`ClassLoader`
    - 把`.class`字节码读进来，校验、解析、初始化，在方法区放好类元数据，堆中生成`Class`对象
    - 三个阶段
      - 加载`Load`
        - 按**全限定类名**读字节流 → 方法区数据结构 → 堆里`Class`对象
      - 链接`Link`
        - **验证**：字节码安全验证：格式/元数据/字节码/符号引用
        - **准备**：静态变量分配内存 + 默认零值（`static、final`常量可直接赋值）
        - **解析**：符号引用 → 直接引用
      - 初始化`Initialize`
        - 执行静态赋值、`static{}`（父类优先于子类）
    - **双亲委派**
      - 类加载器层级：`Bootstrap启动类加载器` → `Extension扩展类加载器` → `Application应用程序类加载器` → `自定义类加载器`
      - 规则：**先问父加载器，父加载不了再给子加载器**
      - 作用：安全（防止自定义`java.lang.String`这类原生类）+ 类唯一
      - 破坏双亲委派：
        - `SPI`JDK的服务扩展机制比如`JDBC`,`SpringBoot自动装配`等需要父类依赖子类，通过`TCCL`线程上下文类加载器绕过双亲委派实现
        - 热部署`DevTools / JRebel`，因为同一个类文件加载后会永久缓存，不重新编译类就不会自定变化，通过自定义类重写`loadClass`方法实现
        - `OSGI`：平级`Boundle`网状委派
        - 加密`Class`/远程`Jar`：自定义`findClass`方法
    
  - 运行时数据区（内存模型，排查核心）
    - 先背总表（就这五块，并列关系）
  
      | 区域 | 私有/共享 | 典型异常 |
      |------|-----------|----------|
      | 程序计数器（PC） | 私有 | 无 `OOM`（唯一） |
      | 虚拟机栈 | 私有 | `StackOverflowError` / `OOM` |
      | 本地方法栈 | 私有 | `StackOverflowError` / `OOM` |
      | 堆 Heap | 共享 | `OutOfMemoryError: Java heap space` |
      | 方法区（实现：元空间 `Metaspace`） | 共享 | `OutOfMemoryError: Metaspace` |
  
    - 逐块说明
      - **程序计数器 PC**（Program Counter）
        - 记住当前线程执行到哪一条字节码
        - 线程切换时靠它恢复现场
      - **虚拟机栈**
        - 一线程一栈；每调用一个方法压入一个**栈帧**，返回后弹出
        - 栈帧五件套：**局部变量表**、**操作数栈**、**动态链接**、**返回地址**、**附加信息**
        - 局部变量表：基本类型存值，引用类型存堆里对象地址 → 重要 `GC Roots` 来源
        - `StackOverflowError`：栈帧太多（典型：无限递归）
        - `OOM`：栈需要扩容但内存不够（相对少见）
      - **本地方法栈**
        - 给 `native` 方法用（C/C++），异常类型与虚拟机栈同类
      - **堆 Heap（GC 主战场）**
        - 几乎所有对象实例、数组都在这里
        - 分代视角：
          - 新生代：`Eden + Survivor0 + Survivor1`（新对象先来 `Eden`）
          - 老年代：活得久的对象、大对象
        - 注意：`Metaspace `**不属于堆**
      - **方法区 Method Area（`HotSpot` 实现 = `Metaspace` 元空间）**
        - 存什么：类元数据、运行时常量池、静态变量、`JIT` 相关信息等
        - 实现用的是**本地内存**，不是 `-Xmx` 那块堆
        - 可用 `-XX:MaxMetaspaceSize` 限制上限
      
    - 方法区下面的两条注释（不是第六、第七块区域）
      - **实现变迁**：`JDK7 `及更早多用永久代 `PermGen`（易 `PermGen space`）；`JDK8+` 换成 `Metaspace`
      - **运行时常量池**：方法区的**子区域**；其中**字符串常量池从` JDK7` 起放到堆里**（字符串过多可能贡献 heap `OOM`，不一定是 `Metaspace`）
    
    - 和线上对应
      - `Java heap space` → 对象问题：泄漏 / 堆过小 / 一次加载太多
      - `Metaspace` → 类元数据问题：类太多或 `ClassLoader `卸不掉
      - 堆看着不大但机器 `RSS `很大 → 再想：堆外、Native、`Metaspace`
    
  - 执行引擎（解释器 + `JIT`）
    - 作用：类加载完成后，把字节码真正跑起来
    - **解释器 Interpreter**
      - **逐条解释执行字节码**
      - 优点：启动快、不用预热
      - 缺点：热点代码反复解释，长期性能差
    - **即时编译器 `JIT`（`Just-In-Time`）**
      - **监控代码热度**：循环、频繁调用的方法 → 热点代码
      - **把热点字节码编译成当前机器的本地机器码并缓存**，以后直接跑机器码
      - 两套编译器：
        - `C1`（客户端）：**编译快、优化浅**，适合**桌面/启动**阶段
        - `C2`（服务端）：**编译慢、优化深**，**后端**长期吞吐更好
    - **分层编译**（`JDK `默认思路）
      - 冷启动：解释器 / `C1`，先跑起来并采集统计
      - 足够热：交给 `C2` 深度优化
      - 平衡：启动速度 + 长期性能
    - 和线上对应
      - 刚启动偏慢、跑一阵变快：正常（预热 / `JIT`）
      - 持续变慢：别只怪 `JIT`，优先查 `GC`、锁竞争、业务逻辑

  - `JNI` + 本地方法库
    
    - **`JNI`（`Java Native Interface`）**
      - Java 与底层 C/C++ 的桥梁
      - 用途：调`系统 API`、`硬件`、`文件/线程`等底层能力；也可反向让 C/C++ 调 Java
    - **本地方法库 Native Library**
      - 真正的 native 实现：Windows `dll` / Linux `so` / Mac `dylib`
      - 由 `JNI` 去调用
    - 和线上对应
      - 堆不大、`RSS `很大：可能堆外（如 `DirectBuffer`）、`JNI`、驱动/压缩库等 Native 内存
      - 排查方向不同于纯 `Java heap space`，不能只靠普通业务对象 dump 完事
    
  - 垃圾回收 `GC`
    - **目标**：自动找出堆里「死对象」并释放内存（对比 C/C++ 手动 free）
    - **怎么判断死活**
      - 引用计数：有循环引用缺陷，`HotSpot `不用
      - **可达性分析**（`HotSpot `默认）：从 `GC Roots` 往下摸引用链，摸不到 → 可回收
    - **常见 `GC Roots`**
      - **虚拟机栈**局部变量表引用的对象
      - **本地方法栈** `JNI `引用的对象
      - **方法区静态变量 / 常量**引用的对象
      - 活跃 `Thread`
      - `synchronized` 持有的**监视器对象**
      - `JVM `内部全局引用（如 Class、系统类异常相关等）
      - 对应工具：MAT 的 **`Path to GC Roots`**
    - **四种引用**（强度从强到弱）
      - **强引用**：**还在就永不回收**（日常 99% 代码；lab 里 `leakyList` 就是）
      - **软引用**：内存将尽 / 快 `OOM `前才回收 → 适合缓存
      - **弱引用**：只要 `GC` 就回收 → 如 `WeakHashMap`
      - **虚引用**：`get()` 永远 null，只配合 `ReferenceQueue` 做回收通知 → **堆外资源监听**
    - **分代**
      - **新生代**：**朝生夕灭**；Eden 满 → `Minor GC`；熬过多次年龄阈值 → 晋升老年代
      - **老年代**：**长期存活 / 大对象**；空间紧 → `Major GC` / 常伴随更重回收
      - `Full GC`：**新生代 + 老年代 + 元空间等整堆级回收**，`STW` 最长，生产要压
    - **三种基础算法**
      - **复制**：无碎片、浪费空间 → 适合**新生代**
      - **标记-清除**：有碎片 → `CMS `等**老年代**场景
      - **标记-整理**：无碎片但移动贵 → **老年代**部分收集器
    - **主流收集器（定位即可）**
      - 吞吐向：Parallel 系列
      - 低停顿老方案：`CMS`（**碎片、浮动垃圾、并发失败**等缺陷，已非主流首选）
      - **现代默认常见**：`G1`（Region 分区，可设停顿目标，兼顾吞吐与延迟）
      - 超低延迟：`ZGC` / Shenandoah（大堆、低延迟场景）
    - **`STW`（Stop-The-World）**
      - `GC` 时**用户线程全部暂停**，只跑`GC`
      - `Serial/Parallel`：几乎全程 `STW`
      - `CMS/G1/ZGC`：主要**在初始标记、重新标记等短阶段** `STW`
      - 生产目标：**减少 `Full GC` 次数、缩短 `STW`**
    - 和线上对应
      - 接口毛刺 / 周期性卡顿 → 看 `GC `日志、`jstat`，是否 `Full GC `/ 停顿过长
      - 内存持续上涨且回收后基线抬高 → 结合 dump 查强引用泄漏（`GC Roots` 路径）
      - 先认异常类型（`heap / Metaspace`），再决定抓 `hprof `还是查类加载

- 三、常用参数（排查时会改 / 会看）
  - 堆
    - `-Xms`：堆初始大小
    - `-Xmx`：堆最大大小（建议与 `-Xms` 相等，避免运行中扩容抖动）
    - `-Xmn`：新生代大小（按需）
    - `-XX:SurvivorRatio=8`：`Eden : S0 : S1` 约 `8:1:1`
  - 元空间
    - `-XX:MetaspaceSize`：元空间初始阈值相关
    - `-XX:MaxMetaspaceSize`：元空间上限（防类元数据把机器内存吃光）
  - 收集器
    - `-XX:+UseG1GC`：G1（现代常见默认/首选之一）
    - `-XX:+UseZGC`：超低延迟场景（`JDK11+`）
    - `Parallel / CMS` 等了解即可，新项目少首选 `CMS`
  - `GC` 日志
    - 旧写法：`-XX:+PrintGCDetails`、`-Xloggc:/path/gc.log`
    - `JDK9+`推荐：`-Xlog:gc*:file=/path/gc.log:time,uptime,level,tags`
  - `OOM` 自动 dump（生产强烈建议）
    - `-XX:+HeapDumpOnOutOfMemoryError`
    - `-XX:HeapDumpPath=/path/oom.hprof`
  - 记一句：参数是「手段」，先认准异常类型和证据，再改 `-Xmx` / 收集器

- **四、一条对象的一生（把宏观微观串起来）**
  
  1. 写 `User.java`
  2. `javac` → `User.class` 字节码
  3. 启动后 `Application ClassLoader` 加载该类
  4. 经历加载 → 链接 → 初始化（静态变量 / `static{}`）
  5. `new User()`：对象进堆的 **Eden**；引用进当前线程栈帧的**局部变量表**
  6. 调方法：虚拟机栈压入新栈帧，执行引擎解释 / `JIT `执行
  7. **Eden 满 → `Minor GC`：可达性分析，存活对象进 Survivor**
  8. **多次存活** → 晋升**老年代**；**老年代紧 / 元空间满**等 → 可能 `Full GC`（`STW`）
  9. 程序结束，进程退出，操作系统回收 `JVM `占用内存
  - lab 变体：局部变量 `leakyList` 一直强引用 → 一直可达 → `GC `不收 → 小堆 `Java heap space` → 自动 dump → MAT` Path to GC Roots` 指回这条链
  
- 五、线上排查怎么对号入座
  - 对照表

    | 现象 | 先怀疑 | 第一证据 | 对应知识点 |
    |------|--------|----------|------------|
    | `Java heap space` | 泄漏 / 堆小 / 大对象 | `.hprof` + MAT | 堆、强引用、`GC Roots` |
    | `Metaspace` | 类太多 / `ClassLoader` 卸不掉 | 类数量、加载器 | 类加载、热部署风险 |
    | 卡顿毛刺 | `GC / Full GC` | `gc.log`、`jstat` | `STW`、分代、`G1` |
    | 低 CPU 卡死 | 死锁 | `jstack` / `jcmd Thread.print` | 线程与锁 |
    | 高 CPU | 死循环 / 热点方法 | `jstack` + 采样 / profiler | 线程 + 执行热点 |
    | 堆不大机器内存爆 | 堆外 / Native / `Metaspace` | `RSS、NMT` 等 | `JNI、DirectBuffer` |

  - 标准闭环
    ```
    现象 → 认准异常类型 → 采证(dump/日志/线程栈) → 定位引用链或栈 → 改代码/参数 → 复测
    ```
  - 纠偏
    - 看到 `OOM `不要第一反应只加 `-Xmx`
    - dump 最好事先配好；进程挂了往往来不及再 dump
    - 占内存看大小（Dominator Tree）；定根因看 `Path to GC Roots`

- 六、面试题自检清单（一句话能答即可）
  1. 五大内存区：谁私有/共享？各自典型异常？
  2. 双亲委派：流程、作用、四类破坏场景？
  3. CMS vs G1？CMS 主要缺陷？
  4. GC Roots 有哪些？
  5. 强/软/弱/虚引用区别与场景？
  6. Minor / Major / Full GC 区别与触发？
  7. 复制 / 标记清除 / 标记整理：优缺点与适用区？
  8. 为什么 PermGen 换成 Metaspace？
  9. STW 是什么？各收集器大概哪里停？
  10. JIT 是什么？分层编译解决什么问题？
  - OOM 加练（见 `面试题/OOM相关.md`）
    - `Java heap space` vs `Metaspace`
    - 为什么 dump 比盲目加大 `-Xmx` 更重要
    - GC Roots 清单口述

