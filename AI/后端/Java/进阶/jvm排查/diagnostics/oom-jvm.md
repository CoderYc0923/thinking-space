# 内存与 GC（必做）实操笔记

> 对应：[jvm-dump-usecases实操教程](../jvm-dump-usecases实操教程.md) **第 2 周**  
> 仓库 case：`MemoryLeak` / `GCThrashing` / `MetaspaceOOM` / `OffHeapLeak`  
> lab 对照：`diagnostic-lab` 的 `memory`（仅堆泄漏）+ `gc`（短命对象压力，**不等于** Thrashing）

---

- 由jvm引起的OOM场景
  - 可能堆内存泄漏（集合/缓存无限增长、监听器未移除、ThreadLocal未清理）
  - 本地无界缓存（本地Cache无上限、无过期；Guava/Caffeine配置不当）
  - 堆过小（-Xmx，相对业务峰值不够或负载上涨后未扩容）
  - 大对象/一次加载过多（超大List、一次性读全表进内存、导出未分页）
  - 元空间泄漏（动态代理/热加载/脚本引擎反复生成类；-XX:MaxMetaspaceSize过小）
  - 直接内存/堆外（Netty/NIO DirectByteBuffer、未限制 -XX:MaxDirectMemorySize）
  - 本地内存（非堆）（JNI、压缩包、某些驱动；堆看着不大但RSS暴涨）`RSS指的是Resident Set Size，常驻集大小。指进程当前实际占用的物理内存RAM`
  - 内存碎片/晋升失败（老年代碎片或分配失败触发OOM（相对少见，看GC日志））

- 本周实操时，先分清「涨的是哪一块」（对应上面场景落地到 case）
  - **堆（Heap）**：业务对象；MAT / hprof 主战场 → `MemoryLeak`、部分 `GCThrashing`
  - **GC 忙死**：堆几乎满、回收极少、CPU 在 GC 上 → `GCThrashing`（未必立刻 OOM，先是吞吐崩）
  - **元空间（Metaspace）**：类元数据，不是业务对象堆 → `MetaspaceOOM`
  - **堆外 / Direct**：`DirectByteBuffer` 等；堆看着不大、RSS 涨 → `OffHeapLeak`

- 口诀（判断方向；下面「线上命令」才是真环境常用写法）：
  - 堆持续涨 + 最终 `Java heap space` → 先 hprof + MAT
  - 堆几乎满 + GC 频繁/耗时长 + 业务极慢 → 先 `jstat` / gc 日志，再看是否泄漏占坑
  - 报错带 `Metaspace` → 看类数量 / `MaxMetaspaceSize`，别只盯堆
  - RSS 涨、堆平稳 → 怀疑堆外 / NMT，MAT alone 会误判

- 口诀 → 线上常用命令（Linux / 容器；本机 PowerShell 只是换皮）

  | 口诀场景 | 线上先看什么 | 常用命令 / 动作 |
  |----------|--------------|-----------------|
  | 堆 OOM / 堆持续涨 | 异常日志里的 OOM 文案；是否已有自动 dump | 日志搜 `OutOfMemoryError`、`Java heap space`；确认启动参数是否有 `-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=...` |
  | | 进程还在时打堆（慎用，停顿大） | `jps -l` 或 `ps -ef \| grep java` 找 PID → `jcmd <pid> GC.heap_dump /tmp/heap.hprof` 或 `jmap -dump:format=b,file=/tmp/heap.hprof <pid>` → 拉回用 **MAT** 看 |
  | | 轻量先看谁占堆 | `jcmd <pid> GC.class_histogram \| head -30` |
  | GC 忙 / 极慢 | **优先 GC 日志**（线上最常见） | 启动带 `-Xlog:gc*:file=/var/log/app/gc.log:time,uptime,level,tags`（JDK9+）；看 Full GC 是否极勤、回收是否几乎为 0（看GC一次清了多少空间，比如：63M->62M(64M)就只是回收了1M） |
  | | 登机器即时看 | `jstat -gcutil <pid> 1000`（每秒一行；看 O / FGC / FGCT / GCT） |
  | | 监控（很多公司第一现场） | Grafana：Heap、GC pause、GC time%、Old gen；不必先 SSH |
  | Metaspace | 异常原文必须含 `Metaspace` | 日志搜 `OutOfMemoryError: Metaspace`；对照是否设了 `-XX:MaxMetaspaceSize=` |
  | | 类 / 元空间是否在涨 | `jstat -gcmetacapacity <pid> 1000`；`jcmd <pid> VM.classloader_stats` |
  | | 可选 NMT | 需启动带 `-XX:NativeMemoryTracking=summary` → `jcmd <pid> VM.native_memory summary`（看 Class 段） |
  | 堆外 / RSS | 堆不大但容器/机器内存爆 | `ps -o pid,rss,vsz,cmd -p <pid>` 看 RSS；对比 `jcmd <pid> GC.heap_info`；K8s 看是否 OOMKilled |
  | | Direct / NMT | 启动带 `-XX:MaxDirectMemorySize=`、`-XX:NativeMemoryTracking=summary` → `jcmd <pid> VM.native_memory summary`；直方图可搜 `DirectByteBuffer`：`jcmd <pid> GC.class_histogram \| grep DirectByteBuffer` |

  - 和本机练习的对应关系（同一工具，写法不同）：
    ```bash
    # 线上 Linux（真环境常见）
    jstat -gcutil <pid> 1000
    jcmd <pid> GC.heap_dump /tmp/heap.hprof
    jcmd <pid> VM.native_memory summary
  
    # 你本机 Windows（练习用，工具相同）
    & "$jdk\jstat.exe" -gcutil <pid> 1000
    & "$jdk\jcmd.exe" <pid> GC.heap_dump "$PWD\usecases\heap.hprof"
    ```
  - 线上注意：很多业务镜像**没有**完整 JDK，可能没有 `jstat`/`jcmd` → 改看 **GC 日志 + 监控**，或用诊断 sidecar / Arthas；能打 dump 时再 MAT。

- 采证前公共准备（四个模拟通用）
  - 工作目录：
    ```powershell
    cd D:\code-self\thinking-space\AI\后端\Java\进阶\jvm排查\diagnostics
    ```
  - JDK 工具（建议与脚本同一套）：
    ```powershell
    $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
    ```
  - 先确认 jar 已编译：
    ```powershell
    cd ..\jvm-dump-usecases
    mvn -DskipTests package
    cd ..\diagnostics
    ```
  - 总原则：启动窗口**不要关** → 另开终端 `jps` 找 PID → 按 case 采证 → 看完 `Ctrl+C` 结束  
  - 大文件（`*.hprof`、长日志）落到 `diagnostics/usecases/`，**不要提交 Git**

- 四个 case 一眼分清

  | Case | 涨哪里 | 典型报错 / 现象 | 第一工具 | 和 lab |
  |------|--------|-----------------|----------|--------|
  | `MemoryLeak` | 堆 | `Java heap space`；CPU 往往不高 | hprof + MAT | ≈ lab `memory` |
  | `GCThrashing` | 堆几乎满 + GC 时间 | 极慢 / `GC overhead limit exceeded` | `jstat` + gc 日志 | ≠ lab `gc`（见下） |
  | `MetaspaceOOM` | 元空间 | `OutOfMemoryError: Metaspace` | 限 Metaspace + 类统计 | lab 未覆盖 |
  | `OffHeapLeak` | Direct / RSS | `Direct buffer memory`；堆可仍小 | NMT / RSS vs 堆 | lab 未覆盖 |

---

## 模拟A OOM（lab：堆泄漏，`run-oom.ps1`）

- 源码使用无界缓存持有强引用的内存泄漏配合小堆

  - ```java
    List<byte[]> leakyList = new ArrayList<>();
    while(true) {
        leakyList.add(new byte[1024 * 1024]); // 每次1MB
        Thread.sleep(100);
    }
    
    // leakyList只加不减，对象一直被强引用，GC回收不掉
    // 每次new byte[1MB]，快速打满堆内存
    // -Xmx256m 小堆快速模拟
    // HeapDumpOnOutOfMemoryError OOM时自动dump，方便MAT分析
    ```

  - 启动脚本

    ```bash
    .\run-oom.ps1
    ```

  - dump 默认：`diagnostics/oomdump.hprof`（见 `run-oom.ps1`）
  - 练法：OOM 后用 MAT 打开 dump，找 Leak Suspects / Dominator（集合无限增长）

---

## 模拟 B：MemoryLeak（usecases：再加深一遍堆泄漏）

- 故障画像：内存（堆）持续上涨；进程可能还能跑一阵；最终 OOM 或被容器杀掉；**CPU 往往不高**（区别于 GC Thrashing 的「GC 核很忙」）
- 本质：强引用挂住对象（集合/缓存只加不减），GC 收不掉 → 堆被吃光（与上面「模拟A」同类，换仓库再跑）
- usecases 源码本质（`MemoryLeak`）：
  ```java
  List<byte[]> leakyCache = new ArrayList<>();
  // 线程 "leaky"：
  while (true) {
      leakyCache.add(new byte[512 * 1024]); // 每次 512KB，引用一直握在 List 里
      Thread.sleep(300);
  }
  ```
- lab 对照：上节 `.\run-oom.ps1`；本节用 usecases 再练一遍 MAT
- 启动命令：
  ```powershell
  # usecases（脚本默认 -Xmx256m + HeapDumpOnOutOfMemoryError）
  .\run-usecase.ps1 MemoryLeak
  
  # 自定义堆示例
  .\run-usecase.ps1 MemoryLeak -Xmx 128m
  ```
  - 默认 dump 路径（usecases 脚本）：`diagnostics/usecases/memoryleak.hprof`
- 排查命令（另开终端；OOM 前也可主动 dump）：
  ```powershell
  $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
  & "$jdk\jps.exe" -l
  # 记下 application.jar 对应 PID
  
  # 轻量：看谁占堆（不必等 OOM）
  & "$jdk\jcmd.exe" <pid> GC.class_histogram | Select-Object -First 30
  
  # 主动堆转储（文件大）
  New-Item -ItemType Directory -Force -Path .\usecases | Out-Null
  & "$jdk\jcmd.exe" <pid> GC.heap_dump "$PWD\usecases\memoryleak-manual.hprof"
  ```
- MAT / 直方图里要看到：
  - 大量 `[B`（byte[]）或持有它们的 `ArrayList`
  - Dominator / Incoming References：根上是 `leakyCache` / 泄漏线程持有的 List
  - Leak Suspects 指向「集合无限增长」一类
- 口述：强引用集合只增不减 → 堆 OOM；修：定界缓存、弱引用/过期淘汰、查清谁还握着引用
- 结束：启动窗口 `Ctrl+C`（若已 OOM 退出则不用）

---

## 模拟 B：GCThrashing（GC 忙死 / 吞吐崩）

- 故障画像：接口极慢、吞吐接近 0；**CPU 往往偏高（GC 线程）**；老年代/整堆长期 90%+；Full GC 很勤且回收很少；可能最终 `GC overhead limit exceeded`
- **和 lab `gc`、和 `MemoryLeak` 的区别（必看）**：
  | | lab `gc` | `MemoryLeak` | `GCThrashing` |
  |---|----------|--------------|---------------|
  | 对象命运 | 短命，多数可回收 | 被 List **永久占住** | 先用 List **占满约 90%**，再狂造短命垃圾 |
  | 主要痛感 | 分配压力、停顿变多 | 堆涨到 OOM | GC 几乎捞不出空间 → **忙死** |
  | 第一反应 | gc 日志 / 分配速率 | MAT 找泄漏根 | `jstat` 看 O% / FGC / 回收量 |
- usecases 源码本质（`GCThrashing`）：
  ```java
  List<byte[]> retainedObjects = new ArrayList<>();
  // 1）先往 retainedObjects 塞满，直到用掉约 maxMemory * 90%
  // 2）再死循环分配 1KB 短命数组（不存引用）+ 周期性 System.gc()
  // → 堆几乎没空，GC 狂跑却回收极少
  ```
- 启动命令（**务必小堆**，否则很难看到 thrashing）：
  ```powershell
  # 脚本未传 -Xmx 时默认 -Xmx64m -Xms64m
  .\run-usecase.ps1 GCThrashing
  
  # 或显式
  .\run-usecase.ps1 GCThrashing -Xmx 64m -Xms 64m
  
  # 建议开 GC 日志（JDK21）
  .\run-usecase.ps1 GCThrashing -Xmx 64m -ExtraJvmArgs "-Xlog:gc*:file=usecases/gc-thrashing.log:time,uptime,level,tags"
  ```
- 排查命令（另开终端，过程中持续观察）：
  ```powershell
  $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
  & "$jdk\jps.exe" -l
  
  # 每秒打一行 GC 利用率（重点看 O / FGC / FGCT / GCT）
  & "$jdk\jstat.exe" -gcutil <pid> 1000
  
  # 或更细
  & "$jdk\jstat.exe" -gc <pid> 1000
  ```
- `jstat -gcutil` 里 thrashing 常见形态：
  - `O`（老年代）长期接近 **99～100**
  - `FGC` / `FGCT` 快速上涨
  - Full GC 后占用几乎不降（日志里常出现 `63M->62M(64M)` 这种）
- 可选：再打一份 histogram / dump，会看到大量被 `retainedObjects` 占住的 `[B`——这是「坑位被占满」，不是单纯短命对象问题
  ```powershell
  & "$jdk\jcmd.exe" <pid> GC.class_histogram | Select-Object -First 20
  ```
- 口述：堆被存活对象占满 + 持续分配 → GC 无效忙；修：加大合理堆 **或** 去掉占坑泄漏/无界缓存，并优化分配；不要只当「再加点 CPU」
- 结束：`Ctrl+C`

---

## 模拟 C：MetaspaceOOM（元空间耗尽）

- 故障画像：报错是 **`OutOfMemoryError: Metaspace`**（或 Compressed class space）；堆用量可能仍「看起来正常」；类数量持续涨；动态代理 / 热加载 / 脚本场景常见
- **和堆 OOM 的区别**：
  - 堆 OOM：业务对象太多 → MAT 看 Dominator
  - Metaspace OOM：类元数据太多 → 看加载了多少类、谁在生成类、ClassLoader 是否泄漏
- usecases 源码本质（`MetaspaceOOM`）：
  ```java
  List<Object> proxyInstances = new ArrayList<>();
  while (true) {
      // JDK Proxy 动态生成代理类 → 吃 Metaspace
      Object proxy = Proxy.newProxyInstance(...);
      proxyInstances.add(proxy);   // 握着实例，相关元数据不易回收
      createAnonymousClass(...); // 再造匿名类加压
  }
  ```
- 启动命令（**必须限制 Metaspace**，否则可能很久或先把机器拖垮）：
  ```powershell
  # 脚本未传时默认 -XX:MaxMetaspaceSize=32m
  .\run-usecase.ps1 MetaspaceOOM
  
  .\run-usecase.ps1 MetaspaceOOM -MaxMetaspaceSize 32m
  
  # 需要 NMT 时（观察 Class 段）
  .\run-usecase.ps1 MetaspaceOOM -MaxMetaspaceSize 32m -ExtraJvmArgs "-XX:NativeMemoryTracking=summary"
  ```
- 排查命令（另开终端；OOM 前抓紧采）：
  ```powershell
  $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
  & "$jdk\jps.exe" -l
  
  # 元空间容量 / 使用（隔几秒多打几次，看涨）
  & "$jdk\jstat.exe" -gcmetacapacity <pid> 1000
  
  # 类加载器 / 类统计（JDK 版本字段略有差异，看 Total / 类数量趋势即可）
  & "$jdk\jcmd.exe" <pid> VM.classloader_stats
  
  # 若启动时开了 NMT：
  & "$jdk\jcmd.exe" <pid> VM.native_memory summary
  # 关注 Class（reserved/committed）是否顶满 MaxMetaspaceSize
  ```
- 控制台应能看到：不断打印 `Generated N proxy classes`，最后 OOM 信息含 **`Metaspace`**
- 口述：动态生成类把元空间打满 → 与 `Java heap space` 不是一类病；修：限制 `MaxMetaspaceSize`、缓存/复用代理与 ClassLoader、修 ClassLoader 泄漏，别盲目只加 `-Xmx`
- 结束：进程 OOM 退出或 `Ctrl+C`

---

## 模拟 D：OffHeapLeak（堆外 Direct 泄漏）

- 故障画像：**堆占用不高甚至平稳**，但进程 **RSS** 持续涨；容器可能 OOMKilled 而堆监控还「健康」；最终常见 `OutOfMemoryError: Direct buffer memory`
- **为什么只看 MAT 会误判**：Direct 内存在堆外；hprof 里最多看到 `DirectByteBuffer` 对象壳，真正大块在 native；必须结合 RSS / NMT / `MaxDirectMemorySize`
- usecases 源码本质（`OffHeapLeak`）：
  ```java
  List<ByteBuffer> directBuffers = new ArrayList<>();
  while (true) {
      ByteBuffer buf = ByteBuffer.allocateDirect(1024 * 1024); // 1MB 堆外
      directBuffers.add(buf);  // 强引用 → Cleaner 清不掉 → 堆外只增不减
      // 周期性 System.gc()：堆仍相对稳定，对照「堆外在涨」
  }
  ```
- 启动命令（建议同时限制堆与 Direct，并开 NMT）：
  ```powershell
  .\run-usecase.ps1 OffHeapLeak -Xmx 128m -ExtraJvmArgs "-XX:MaxDirectMemorySize=64m -XX:NativeMemoryTracking=summary"
  
  # 想慢一点观察 RSS，可把 Direct 调大一点再跑
  .\run-usecase.ps1 OffHeapLeak -Xmx 256m -ExtraJvmArgs "-XX:MaxDirectMemorySize=128m -XX:NativeMemoryTracking=summary"
  ```
- 排查命令（另开终端）：
  ```powershell
  $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
  & "$jdk\jps.exe" -l
  
  # 1）堆是否仍不大
  & "$jdk\jcmd.exe" <pid> GC.heap_info
  & "$jdk\jcmd.exe" <pid> GC.class_histogram | Select-String "DirectByteBuffer"
  
  # 2）进程工作集（Windows 上近似 RSS）
  Get-Process -Id <pid> | Select-Object Id, WorkingSet64, @{N='WS_MB';E={[math]::Round($_.WorkingSet64/1MB,1)}}
  
  # 3）NMT（启动时需带 NativeMemoryTracking）
  & "$jdk\jcmd.exe" <pid> VM.native_memory summary
  # 可 baseline 后再 diff：
  & "$jdk\jcmd.exe" <pid> VM.native_memory baseline
  Start-Sleep -Seconds 30
  & "$jdk\jcmd.exe" <pid> VM.native_memory summary.diff
  ```
- 预期现象：
  - 控制台：`Allocated N direct buffers (N MB off-heap)`，Heap 打印仍较小
  - WorkingSet / RSS 随 N 上涨
  - 最终 OOM 文案含 **`Direct buffer memory`**（若限制了 `MaxDirectMemorySize`）
- 口述：堆外 Direct 只分配不释放 → RSS 杀进程而堆监控骗人；修：限制 `MaxDirectMemorySize`、用完释放/`Cleaner`、Netty 务必 `release`，容器内存按 `Xmx + Direct + Metaspace + 余量` 规划
- 结束：`Ctrl+C` 或等 Direct OOM

---

## 通关自检（第 2 周）

- [ ] `MemoryLeak`：能指到「谁握着 byte[]」、说出和 lab memory 同类
- [ ] `GCThrashing`：能讲清「先占坑再造垃圾 ≠ lab 短命 gc」；会看 `jstat` 的 O / FGC
- [ ] `MetaspaceOOM`：能区分 `Metaspace` vs `Java heap space`；知道要限 `MaxMetaspaceSize`
- [ ] `OffHeapLeak`：能解释为何堆不大仍可能把机器打爆；会用 RSS/NMT 对照堆

每案可按此模板记一笔：

```text
Case：
现象（CPU / 堆 / Metaspace / RSS）：
第一工具：
关键证据（jstat 一行 / OOM 文案 / MAT 结论）：
根因一句话：
修复思路：
和 lab / 线上哪类故障对应：
```

---

## 推荐动手顺序（一次一个）

```powershell
cd D:\code-self\thinking-space\AI\后端\Java\进阶\jvm排查\diagnostics

.\run-usecase.ps1 MemoryLeak
.\run-usecase.ps1 GCThrashing -Xmx 64m
.\run-usecase.ps1 MetaspaceOOM -MaxMetaspaceSize 32m
.\run-usecase.ps1 OffHeapLeak -Xmx 128m -ExtraJvmArgs "-XX:MaxDirectMemorySize=64m -XX:NativeMemoryTracking=summary"
```

官方英文步骤与截图：`jvm-dump-usecases/docs/memoryleak.md`、`gc-thrashing.md`、`metaspace-oom.md`、`offheap-leak.md`。

做完这四个，第 2 周「内存与 GC」必做即通关；下一周再碰线程池 / 连接池 / FD。
