# jvm-dump-usecases 实操教程

> **定位**：在 [diagnostic-lab](./diagnostic-lab实操与JVM原理.md) 三场景练熟后，用更全的病例库练「见症状 → 选工具 → 定根因」  
> **仓库**：[Pamir/jvm-dump-usecases](https://github.com/Pamir/jvm-dump-usecases)（已克隆到本目录 `jvm-dump-usecases/`）  
> **和 lab 的区别**：lab 练手感；usecases 练广度（高 CPU、Metaspace、堆外、连接池、FD…）

---

## 一、你已经会什么，这里补什么

| diagnostic-lab | 本仓库对应 / 扩展 |
|----------------|-------------------|
| memory 泄漏 OOM | `MemoryLeak`（再加深）+ `SingleThreadHighMemoryUsage` + `GCThrashing` |
| deadlock 低 CPU 卡死 | `Deadlock` + `InfiniteWait`（低 CPU 挂起）+ `Log4j` / 连接池等待 |
| gc 分配压力变慢 | `GCThrashing`（堆几乎满后再狂分配，更接近「GC 忙死」） |
| （未覆盖） | 高 CPU 死循环、`MetaspaceOOM`、堆外、线程泄漏、线程池打满、FD 泄漏、栈溢出 |

**标准闭环不变**：

```text
现象 → 认类型(CPU/内存/线程/FD/元空间) → 采证 → 定位 → 口述根因
```

---

## 二、环境准备

### 2.1 目录

```text
Java/进阶/jvm排查/
├── diagnostic-lab/                 # 已完成
├── jvm-dump-usecases/              # 本仓库
├── diagnostics/run-usecase.ps1     # 本地一键跑某个 case
└── jvm-dump-usecases实操教程.md    # 本文
```

若还没有仓库：

```powershell
cd Java/进阶/jvm排查
git clone https://github.com/Pamir/jvm-dump-usecases.git
```

### 2.2 编译

本项目 `pom` 是 **Java 8** 字节码，用 JDK8 或 JDK21 都能跑（推荐继续用你本机 JDK21）。

```powershell
cd jvm-dump-usecases
mvn -DskipTests package
```

产物：`target/application.jar`

### 2.3 推荐跑法：本地 jar（Windows 优先）

官方 README 偏 Docker + `jattach`；你在 Windows 上更省事的是：

```powershell
cd Java/进阶/jvm排查/diagnostics
.\run-usecase.ps1 Deadlock
```

或手工：

```powershell
& "D:\Java\jdks\jdk-21.0.11_10\bin\java.exe" -jar ..\jvm-dump-usecases\target\application.jar Deadlock
```

**参数大小写必须与下表一致**（README 里有的小写示例是错的，以 `Application.java` 为准）。

### 2.4 Docker（可选）

```bash
cd jvm-dump-usecases
docker build -t jvm-dump-cases .
docker run -it --rm jvm-dump-cases Deadlock
```

进容器采证要用 `docker exec` / sidecar；本地 jar + `jps`/`jstack` 对你更直接。

---

## 三、全部 Case 一览（参数名可直接抄）

| 参数名 | 症状画像 | CPU | 内存 | 第一工具 |
|--------|----------|:---:|:----:|----------|
| `InfiniteWait` | 低 CPU 挂起（等锁/join） | 低 | 正常 | `jstack` |
| `InfiniteLoop` | 高 CPU 死循环 | 高 | 正常 | `jstack` + 看占用核的线程 |
| `MemoryLeak` | 堆持续涨 | 低/中 | 涨 | hprof + MAT |
| `SingleThreadHighMemoryUsage` | 单线程内存尖峰 | 低 | 尖峰 | hprof + MAT |
| `CrashOnError` | 崩溃 / 错误退出 | — | — | 日志 / crash 相关参数 |
| `ClassloaderLeak` | 类加载器泄漏 → 元数据涨 | 低 | Metaspace/类多 | histogram / dump |
| `ThreadLeak` | 线程数持续涨 | 中 | 涨 | `jstack` 多次对比 |
| `Log4j` | 日志 appender 阻塞 | 低 | 正常 | `jstack` 看 BLOCKED |
| `NonFinalized` | Finalizer 队列堆积 | 低 | 涨 | dump 看 Finalizer |
| `Deadlock` | 死锁卡死 | 低 | 正常 | `jstack`（deadlock 段） |
| `GCThrashing` | GC 忙死、吞吐崩 | 高(GC) | 几乎满 | `jstat` + gc.log |
| `MetaspaceOOM` | 元空间 OOM | 低 | Metaspace | 限 `MaxMetaspaceSize` + 类统计 |
| `OffHeapLeak` | 堆不大 RSS 涨 | 低 | RSS 涨 | NMT / 堆外 |
| `ConnectionPoolExhaustion` | 等连接卡死 | 低 | 正常 | `jstack` WAITING |
| `ThreadPoolSaturation` | 线程池打满/拒绝 | 中 | 正常 | `jstack` + 池状态 |
| `StackOverflow` | 栈溢出 | 低 | 正常 | 异常栈 / `-Xss` |
| `FileDescriptorLeak` | FD 耗尽 | 低 | 正常 | `lsof` / 句柄数（Linux 更直观） |

官方分场景说明在：`jvm-dump-usecases/docs/*.md`（英文步骤 + 截图，可对照）。

---

## 四、建议练习路线（别一次刷 17 个）

结合你已会 lab，按周推进：

### 第 1 周：线程症状分化（必做）

目标：看到「卡住」能分清低 CPU / 高 CPU / 死锁。

| 顺序 | Case | 你要练什么 |
|------|------|------------|
| 1 | `Deadlock` | 巩固 lab：搜 `Found one Java-level deadlock` |
| 2 | `InfiniteWait` | 低 CPU 挂起，但不一定是经典 deadlock 报告 |
| 3 | `InfiniteLoop` | **高 CPU**：找出占用 CPU 的线程名/栈 |
| 4 | `Log4j` | BLOCKED 在日志/IO 上的「假死」 |

口诀：

- CPU 低 + 卡住 → 先 `jstack`  
- CPU 高 + 卡住/狂转 → `jstack` 对齐繁忙线程  
- 有明确 deadlock 段 → 锁环  
- 没有 deadlock 段也可能在等锁 / join / 池子

### 第 2 周：内存与 GC（必做）

实操笔记（启动 / 采证 / 口述）：→ [diagnostics/oom-jvm.md](./diagnostics/oom-jvm.md)

| 顺序 | Case | 和 lab 对比 |
|------|------|-------------|
| 1 | `MemoryLeak` | 同「强引用挂住」思路，换仓库再跑一遍 MAT |
| 2 | `GCThrashing` | **不是**单纯短命对象；先占满约 90% 再狂分配 → GC 开销极大（建议小堆 `-Xmx64m`） |
| 3 | `MetaspaceOOM` | 补齐 lab 没练的：`OutOfMemoryError: Metaspace` |
| 4 | `OffHeapLeak` | 堆看着还行、机器内存/RSS 涨 → 堆外 |

`GCThrashing` 示例：

```powershell
.\run-usecase.ps1 GCThrashing -Xmx 64m
```

### 第 3 周：资源与池化（选做，很像线上）

| Case | 线上味道 |
|------|----------|
| `ThreadLeak` | 线程只建不关 |
| `ThreadPoolSaturation` | 池满、队列满、任务堆着 |
| `ConnectionPoolExhaustion` | 等数据库连接，接口大面积超时 |
| `FileDescriptorLeak` | Too many open files（Windows 上工具不同，理解概念为主） |
| `StackOverflow` | 深递归 / 过大栈帧 |

---

## 五、通用采证命令（本地 jar）

另开终端，**尽量用同一 JDK 的 bin**：

```powershell
$jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
& "$jdk\jps.exe" -l

# 线程
& "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\threads.txt

# GC
& "$jdk\jstat.exe" -gcutil <pid> 1000

# 堆直方图（轻量）
& "$jdk\jcmd.exe" <pid> GC.class_histogram

# 堆转储（慎用，文件大，勿提交 Git）
& "$jdk\jcmd.exe" <pid> GC.heap_dump $PWD\heap.hprof
```

证据落盘目录建议：`diagnostics/usecases/`（已在 `.gitignore` 思路里忽略 `*.hprof`）。

---

## 六、和 lab 易混点（必看）

| 说法 | 对不对 |
|------|--------|
| `MemoryLeak` ≈ lab memory（引用挂住） | ✅ 同类问题 |
| `Deadlock` ≈ lab deadlock | ✅ |
| `GCThrashing` = lab gc（短命对象可回收） | ⚠️ **不完全一样**：Thrashing 先用 List **占住大部分堆**，再制造垃圾，GC 几乎捞不出空间 |
| `MetaspaceOOM` = heap space | ❌ 类元数据，不是业务对象堆 |
| `OffHeapLeak` 用 MAT 看堆就够 | ❌ 堆可能很健康，要看 RSS/NMT/堆外 |
| `InfiniteLoop` 和 `InfiniteWait` 都是卡死所以一样查 | ❌ 一个高 CPU、一个低 CPU，栈形态不同 |

---

## 七、每案笔记模板（手敲用）

```text
Case：
现象（CPU/内存/是否超时）：
第一工具：
关键证据（贴 5～10 行栈或 MAT 结论）：
根因一句话：
修复思路：
和 lab / 线上哪类故障对应：
```

---

## 八、通关标准

### 最低通关（做完第 1～2 周必做）

- [ ] 能不看文档说出 6 个以上 case 参数名与用途  
- [ ] `InfiniteLoop` vs `InfiniteWait` vs `Deadlock` 能区分  
- [ ] `MetaspaceOOM` 能讲清与 `Java heap space` 区别  
- [ ] `GCThrashing` 能讲清「堆被占满 + 持续分配 → GC 忙死」  
- [ ] `OffHeapLeak` 知道为什么只看堆会误判  

### 加分

- [ ] 连接池 / 线程池各跑通一次，`jstack` 能指到 WAITING/RUNNABLE 特征  
- [ ] 对照官方 `docs/` 走完一个完整英文排查步骤  

---

## 九、启动脚本

```powershell
cd Java/进阶/jvm排查/diagnostics
.\run-usecase.ps1              # 打印可用 case
.\run-usecase.ps1 Deadlock
.\run-usecase.ps1 MetaspaceOOM -MaxMetaspaceSize 32m
.\run-usecase.ps1 GCThrashing -Xmx 64m
```

脚本会优先使用 `D:\Java\jdks\jdk-21.0.11_10\bin\java.exe`，与 lab 一致。

---

## 十、一句话

**usecases 不是再学一套 JVM，而是把 lab 的肌肉记忆，扩展到「高 CPU / 元空间 / 堆外 / 池化 / FD」这些更像线上的病例。**  
先刷线程三件套 + Metaspace + GCThrashing + OffHeap，再碰池子和 FD。
