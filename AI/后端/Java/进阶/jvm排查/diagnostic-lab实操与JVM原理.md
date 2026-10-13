# diagnostic-lab 实操与 JVM 原理

> **目标**：用 [diagnostic-lab](https://github.com/AlekseyBykov/diagnostic-lab) 把「造故障 → 采证 → 分析 → 口述」跑通  
> **前置**：已读 `Java/基础/JVM基础.md`（内存模型、GC Roots、分代、STW）  
> **工具链**：JDK 自带命令 + VisualVM / MAT + [GCeasy](https://gceasy.io/)（GC 日志可选上传）  
> **仓库**：三个场景 —— `memory`（泄漏/OOM）、`deadlock`（死锁）、`gc`（GC 压力）

---

## 一、排查总框架（先背这个）

线上 JVM 问题本质是三类症状，对应三类证据：

| 症状 | 常见根因 | 第一证据 | 深挖工具 |
|------|----------|----------|----------|
| 内存涨 / OOM | 泄漏、堆过小、大对象、缓存无界 | Heap Dump（`.hprof`）+ GC 日志 | MAT / HeapHero / Arthas `heapdump` |
| 卡死 / 无响应 | 死锁、线程池打满、锁等待 | Thread Dump | `jstack` / `jcmd Thread.print` / Arthas `thread` |
| 变慢 / CPU 高 | GC 过频、热点循环、锁竞争 | GC 日志 + 线程栈 + 采样 | `jstat`、GCeasy、`profiler` |

**标准闭环**：

```
现象 → 判断类型(内存/线程/GC) → 采证(dump/日志) → 定位对象或栈 → 修代码/参数 → 复测验证
```

diagnostic-lab 正好覆盖闭环里最基础的三块：**泄漏、死锁、GC 压力**。

---

## 二、原理速览（对接练手场景）

> 细节以 `基础/JVM基础.md` 为准，这里只抽「排查时要用到」的部分。

### 2.1 内存：堆 vs 元空间 vs 栈

| 区域 | 存什么 | 典型异常 | lab 是否覆盖 |
|------|--------|----------|--------------|
| 堆 Heap | 对象实例、数组 | `OutOfMemoryError: Java heap space` | ✅ memory 场景 |
| 元空间 Metaspace | 类元数据 | `OutOfMemoryError: Metaspace` | ❌（进阶用 jvm-dump-usecases） |
| 虚拟机栈 | 栈帧、局部变量 | `StackOverflowError` | ❌ |

**memory 场景原理**：强引用把对象挂在可达链上（如 `ArrayList` 一直 `add`），GC Roots 仍可达 → 对象无法回收 → 堆被吃满 → OOM。  
对照基础笔记：**只要强引用链存在，GC 永远不回收**。

### 2.2 为什么要 Heap Dump？

- Dump = 某一时刻堆上对象的快照  
- 分析重点：
  1. **Dominator Tree**：谁占用了最多 Retained Size  
  2. **Path to GC Roots**：为什么没被回收（谁还引用着）  
  3. **Leak Suspects**：MAT 自动猜的泄漏嫌疑

参数：

```text
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=./diagnostics/oomdump.hprof
```

### 2.3 线程与死锁

- 每个 Java 线程有独立虚拟机栈；死锁时线程状态多为 `BLOCKED`  
- `synchronized` 互斥：A 持锁1 等锁2，B 持锁2 等锁1 → 环等待  
- Thread Dump 里会明确打出 `Found one Java-level deadlock`

### 2.4 GC 压力从哪来？

- 短生命周期对象狂分配 → Eden 很快满 → **Minor GC 频繁**  
- 存活对象过多 / 老年代吃紧 → 可能升级到 **Full GC**，STW 变长  
- 调优目标不是「消灭 GC」，而是：**降低无效分配、控制停顿、避免 Full GC 风暴**

常用观察：

```text
-XX:+UseG1GC
-Xlog:gc*:file=./diagnostics/gc.log:time,uptime,level,tags
```

（旧写法 `-Xloggc` 仍可见于部分教程；JDK9+ 推荐 `-Xlog:gc*`）

### 2.5 和本仓库三场景的映射

```
memory  → 强引用泄漏 → 堆 OOM → dump → MAT 看 ArrayList/byte[]
deadlock → 锁环等待 → 线程 BLOCKED → jstack 看 deadlock 段
gc      → 高频分配 → GC 频繁 → gc.log → jstat/GCeasy 看停顿与吞吐
```

---

## 三、环境准备

### 3.1 必备

- JDK 17 或 21（`java -version`）
- Maven 3.8+
- Git

### 3.2 推荐工具（按优先级）

| 工具 | 用途 | 备注 |
|------|------|------|
| `jps` / `jcmd` / `jstack` / `jstat` | 命令行采证 | JDK 自带，必须会 |
| VisualVM | 实时看堆、线程、手动 dump | 入门友好 |
| Eclipse MAT | 分析 `.hprof` | 生产级分析 |
| GCeasy | 上传 `gc.log` 看报告 | 浏览器即可 |
| Arthas（可选） | 进程仍活着时在线看 | 与 lab 互补，后续单独练 |

### 3.3 拉取与编译

```bash
git clone https://github.com/AlekseyBykov/diagnostic-lab.git
cd diagnostic-lab
mvn -DskipTests package
```

产物一般在：`target/diagnostic-lab-1.0-SNAPSHOT.jar`（以实际 jar 名为准）。

建输出目录：

```bash
mkdir diagnostics
```

Windows PowerShell 同样可用；路径按本机改。

> **注意**：编译完成 ≠ 进程已启动。此时只是打好了 jar，**还没有 Java 业务进程**，所以下一步先不要急着找 PID。

### 3.4 找进程 PID（所有场景通用）

**必须先启动某个场景**（见下文 memory / deadlock / gc 的 `java ... MainApp xxx`），进程起来之后，再**另开一个终端**查 PID。

```bash
# 终端 1：保持运行，不要关（示例：死锁场景，进程会一直挂着）
java -cp target/diagnostic-lab-1.0-SNAPSHOT.jar ^
  dev.abykov.pets.diagnostic_lab.MainApp deadlock

# 终端 2：再执行
jps -l
```

示例输出（数字是 PID，每台机器不同）：

```text
12345 dev.abykov.pets.diagnostic_lab.MainApp
12346 jdk.jcmd/sun.tools.jps.Jps
```

记下带 `MainApp` 那一行的数字（如上例 `12345`），后面 `jcmd` / `jstack` / `jstat` 都用它。

**为什么刚编译完 jps 没有 MainApp？**

| 时机 | jps 里有没有 MainApp |
|------|----------------------|
| 只执行了 `mvn package` | ❌ 没有，正常 |
| 已 `java ... MainApp xxx` 且窗口还在跑 | ✅ 有 |
| memory 场景已经 OOM 退出 | ❌ 进程没了，PID 消失（改用已生成的 `.hprof`） |
| 终端被关掉 / Ctrl+C | ❌ 进程结束，需重新启动场景 |

**Windows 额外提示**：

- `jps` 要用 **JDK 的 bin**，不要只用 JRE；PowerShell 里可先 `where.exe java` / `where.exe jps`
- 若 `jps -l` 几乎是空的，确认终端 1 的 `java` 命令还在前台跑、没有立刻报错退出
- 主类全限定名以仓库实际代码为准；认不出包名时，看 `jps -l` 里带 `diagnostic` / `MainApp` 的那行即可

正确顺序永远是：

```text
编译 jar → 启动场景(终端1) → jps 查 PID(终端2) → jstack/jcmd/jstat 采证
```

---

## 四、场景 A：Memory Leak / OOM（必做第一课）

### 4.1 原理再钉一下

```
GC Roots（静态集合 / 局部变量等）
    └── ArrayList（强引用）
            └── byte[1MB] × N
```

对象一直可达 → 无法回收 → `-Xmx256m` 很快打满 → OOM → 自动 dump。

### 4.2 启动命令

**推荐：直接跑脚本**（dump 会写到本目录 `diagnostics/oomdump.hprof`）

```powershell
cd Java/进阶/jvm排查/diagnostics
.\run-oom.ps1
```

或双击同目录下的 `run-oom.cmd`。

若提示无法运行脚本，可先执行一次：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

脚本会自动找上级目录里的 `diagnostic-lab/target/diagnostic-lab-1.0-SNAPSHOT.jar`；找不到时先去 lab 目录执行 `mvn -DskipTests package`。

注意两点：

1. **主类是** `dev.abykov.pets.diagnostic_lab.MainApp`（上游 README 多写了 `.demo`，已按实际 jar 修正）
2. **要用 JDK 17+**：本机 PATH 若默认 Java 8，脚本会优先用 `D:\Java\jdks\jdk-21.0.11_10\bin\java.exe`；也可手动指定：

```powershell
$env:DIAG_JAVA = "D:\Java\jdks\jdk-21.0.11_10\bin\java.exe"
.\run-oom.ps1
```

**等价手工命令**（在 `diagnostic-lab` 目录下）：

```bash
java -Xms256m -Xmx256m ^
  -XX:+HeapDumpOnOutOfMemoryError ^
  -XX:HeapDumpPath=../diagnostics/oomdump.hprof ^
  -cp target/diagnostic-lab-1.0-SNAPSHOT.jar ^
  dev.abykov.pets.diagnostic_lab.MainApp memory
```

Linux / macOS 把 `^` 换成 `\`。主类以仓库实际为准；参数 `memory` 不变。

### 4.3 预期现象

1. 日志持续分配大数组  
2. 最终 `java.lang.OutOfMemoryError: Java heap space`  
3. `diagnostics/oomdump.hprof`（或你配置的路径）生成

> **PID 时机**：memory 场景堆很小，可能几十秒内就 OOM 退出。想练 `jps`/`jcmd` 时，启动后立刻开第二个终端抓 PID；若已经退出，属正常，直接分析 `.hprof` 即可。练「活进程查 PID」更推荐先跑 **deadlock**（会一直挂着）。

### 4.4 采证与分析步骤

**步骤 1：进程还活着时（可选）**

另开终端：

```bash
jps -l
jcmd <pid> GC.class_histogram | more
```

看哪些类实例数/字节暴涨（常见 `byte[]`、`ArrayList`）。

**步骤 2：OOM 后打开 dump**

- MAT：`File → Open Heap Dump` → 跑 **Leak Suspects Report**  
- 重点看：
  - Suspect 是否指向某个 `ArrayList` / 缓存  
  - Dominator Tree 里 Retained Heap 最大的对象  
  - Path to GC Roots（为什么没死）

**步骤 3：口述结论模板**

> 堆 OOM。MAT 显示某集合持有大量 `byte[]`，Retained Size 接近堆上限；GC Roots 路径表明集合仍被业务静态/成员引用，属于强引用泄漏（或无界缓存）。修复：限制容量 / 弱引用或过期淘汰 / 分页，并复测堆曲线呈锯齿可回落。

### 4.5 通关标准

- [ ] 能复现 OOM 并拿到 hprof  
- [ ] 能在 MAT 指出「谁占内存、为什么没被回收」  
- [ ] 能用 1 分钟讲清：强引用 + 无界增长 = 堆 OOM

### 4.6 对照面试题

- `OutOfMemoryError: Java heap space` 和 `Metaspace` 区别？  
- 为什么 dump 比「把 -Xmx 调大」更重要？  
- GC Roots 有哪些？（栈局部变量、静态变量、活跃线程等）

---

## 五、场景 B：Deadlock（死锁）

### 5.1 原理

```
线程 T1: 持有 lockA，等待 lockB
线程 T2: 持有 lockB，等待 lockA
→ 环等待 → 双方永久 BLOCKED
```

与「锁竞争导致慢」不同：死锁是**永久卡死**，CPU 可能并不高。

### 5.2 启动命令

**推荐：直接跑脚本**

```powershell
cd Java/进阶/jvm排查/diagnostics
.\run-deadlock.ps1
```

或双击 `run-deadlock.cmd`。笔记见同目录 `卡死无响应大面积超时-jvm.md`。

**等价手工命令**（在 `diagnostic-lab` 目录下）：

```bash
java -cp target/diagnostic-lab-1.0-SNAPSHOT.jar ^
  dev.abykov.pets.diagnostic_lab.MainApp deadlock
```

### 5.3 预期现象

- 程序看似还在跑，但相关业务逻辑不再推进  
- CPU 往往不高（区别于死循环占满核）

### 5.4 采证步骤

```bash
jps -l
jstack <pid> > ./diagnostics/threads.txt
# 或
jcmd <pid> Thread.print > ./diagnostics/threads.txt
```

在 `threads.txt` 中搜索：

- `Found one Java-level deadlock`  
- `BLOCKED`  
- 两个线程各自 `waiting to lock` / `locked`

VisualVM：选中进程 → Threads → Thread Dump。

### 5.5 口述结论模板

> Thread Dump 检出 Java-level deadlock：T1/T2 交叉持有锁形成环等待，状态 BLOCKED。修复：统一加锁顺序、缩小锁范围、用 `tryLock` 超时、或改无锁/并发数据结构。

### 5.6 通关标准

- [ ] 独立打出含 deadlock 段的 thread dump  
- [ ] 能画出两把锁的等待环  
- [ ] 能区分：死锁（低 CPU 卡死）vs 死循环（高 CPU）

### 5.7 对照面试题

- `sleep` 和 `wait` 区别？（持锁与否、唤醒方式）  
- 如何预防死锁？（顺序、超时、减少嵌套）  
- 线上只重启不 dump，下次还会不会再来？

---

## 六、场景 C：GC Pressure（GC 压力）

### 6.1 原理

高频创建短命对象 → Eden 反复填满 → Minor GC 次数飙升；若回收跟不上分配或老年代被挤，可能出现：

- 应用吞吐下降  
- 延迟毛刺（STW）  
- 极端情况接近「GC 开销过大」类问题

本场景重点练：**会开 GC 日志 + 会看频率/停顿**，不是一上来调一堆神秘参数。

### 6.2 启动命令

```bash
java -Xms256m -Xmx256m -XX:+UseG1GC ^
  -Xlog:gc*:file=./diagnostics/gc.log:time,uptime,level,tags ^
  -cp target/diagnostic-lab-1.0-SNAPSHOT.jar ^
  dev.abykov.pets.diagnostic_lab.MainApp gc
```

若本机 JDK 对 `-Xlog` 不熟，可先用仓库 README 的 `-Xloggc:./diagnostics/gc.log`，效果类似。

### 6.3 运行中观察

另开终端：

```bash
jstat -gcutil <pid> 1000
```

关注：

| 列 | 含义 |
|----|------|
| E / S0 / S1 | 新生代占用 |
| O | 老年代占用 |
| YGC / YGCT | Young GC 次数 / 累计耗时 |
| FGC / FGCT | Full GC 次数 / 累计耗时 |

压力场景下常见：**YGC 很快增加**；若 FGC 也狂涨，问题更严重。

### 6.4 日志分析

1. 打开 `./diagnostics/gc.log`  
2. 上传 [GCeasy](https://gceasy.io/) 看：
   - GC 次数、吞吐、最大停顿  
   - 是否有内存泄漏趋势（回收后基线持续抬升）  
3. 自己扫日志关键词：`Pause`、`Full`、`Evacuation`

### 6.5 口述结论模板

> 分配速率过高导致 Young GC 频繁，停顿累计影响延迟。先从代码减少无意义临时对象/大循环装箱；再考虑堆大小与 G1 目标停顿；用 jstat + GC 日志验证 YGC/FGC 次数下降。

### 6.6 通关标准

- [ ] 能输出并读懂一份 `gc.log`  
- [ ] 会用 `jstat -gcutil` 看 YGC/FGC  
- [ ] 能说清：频繁 Young GC ≠ 立刻加大堆；先查分配与泄漏

### 6.7 对照面试题

- Minor GC / Major GC / Full GC 区别？  
- 为什么生产常用 G1？  
- STW 是什么，和「并发标记」怎么并存？

---

## 七、三场景对照表（复习用）

| 场景 | 启动参数关键字 | 核心证据 | 关键结论点 |
|------|----------------|----------|------------|
| memory | `-Xmx` + HeapDumpOnOOM | `.hprof` | 强引用无界增长 |
| deadlock | 无特殊内存参数 | `jstack` | 锁顺序环等待 |
| gc | UseG1GC + gc log | `gc.log` + `jstat` | 分配过快 / 停顿过多 |

建议练习顺序：**memory → deadlock → gc**（先会 dump，再会线程，再读 GC）。

---

## 八、通用命令速查

```bash
# 进程
jps -l

# 线程
jstack <pid>
jcmd <pid> Thread.print

# 堆直方图（轻量，先于全量 dump）
jcmd <pid> GC.class_histogram

# 手动堆转储（进程仍存活时）
jcmd <pid> GC.heap_dump ./diagnostics/manual.hprof

# GC 统计（每秒）
jstat -gcutil <pid> 1000

# 查看 VM 参数
jcmd <pid> VM.flags
```

**注意**：

- 生产环境全量 `heap_dump` 可能导致短暂停顿与磁盘暴涨，先评估再做  
- 已 OOM 崩溃时，依赖事先配置的 `HeapDumpOnOutOfMemoryError`  
- 容器内存限制时，还要区分「堆 OOM」与「cgroup OOMKilled」

---

## 九、建议练习节奏（3～5 天）

| 天 | 任务 | 产出 |
|----|------|------|
| Day 1 | 编译仓库 + memory 全流程 | hprof + MAT 截图/笔记 + 口述稿 |
| Day 2 | deadlock 全流程 | threads.txt + 锁环草图 |
| Day 3 | gc 全流程 | gc.log + jstat 记录 + GCeasy 报告链接/截图 |
| Day 4 | 三场景默写命令，不看文档再跑一遍 | 自检清单全勾 |
| Day 5（可选） | 同一进程挂 Arthas：`dashboard` / `thread` / `memory` | 为下一篇 Arthas 笔记铺路 |

每场景笔记建议固定四段：**现象 → 命令 → 证据摘要 → 根因与修复**。

---

## 十、和后续材料的衔接

| 下一步 | 做什么 |
|--------|--------|
| 仍不够手感 | 重复 lab 三场景，换 MAT / VisualVM / 纯命令各做一遍 |
| 要更多病例 | 再上 [jvm-dump-usecases](https://github.com/Pamir/jvm-dump-usecases)（CPU 挂死、Metaspace、连接池等） |
| 线上味更浓 | 写一个 Spring Boot 接口故意泄漏，用 Arthas 边跑边查 |
| 理论回补 | 翻 `基础/JVM基础.md` 的 GC Roots、引用类型、Full GC 触发条件 |

---

## 十一、一句话收束

**diagnostic-lab 不是用来「调出最优 JVM 参数」的，而是用来把排查肌肉记忆练出来：会造、会抓、会看、会讲。**  
三场景跑通后，JVM 排查就算从「看过概念」进到「能动手」。
