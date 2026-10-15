# L3：应用 / JVM

> 进程内部：线程、堆、GC、本地资源。  
> **动手实操**：[../../../jvm排查/](../../../jvm排查/)  
> - 内存 GC：`diagnostics/oom-jvm.md`  
> - 卡死线程：`diagnostics/卡死无响应大面积超时-jvm.md`  
> - 池化资源：`diagnostics/pool-resource-jvm.md`

---

## 1. 何时进入本模块

常见组合：用户侧 **U1/U2/U3/U4** + 信号 **S-MEM / S-GC / S-THREAD / S-ERR（OOM、Rejected）/ S-CPU（热点）/ S-DISK（FD）**。

- 日志出现 `OutOfMemoryError`（heap / Metaspace / Direct / GC overhead）  
- `jstack`：deadlock、死循环 RUNNABLE、线程名数量持续涨  
- GC：Full GC 极勤且 `前M->后M` 几乎不降  
- `RejectedExecutionException`、本地 `Too many open files`  
- CPU 高且热点在业务代码或 GC 线程  

**先排除**：栈堵在 `getConnection` / Redis / HttpClient → 先去数据库/中间件。

---

## 2. 子问题手册

### 2.1 内存与 GC（常对应 U1/U3 + S-MEM/S-GC）

| 子问题 | 说明 | 思路 | 关键现象 | 命令 |
|--------|------|------|----------|------|
| 堆泄漏 | 集合/缓存只增不减 | 确认基线抬升 → dump → MAT | `Java heap space`；Old 持续高 | 日志 OOM；`jcmd PID GC.class_histogram`；`GC.heap_dump`（慎）；MAT |
| 无界缓存 | 本地 Cache 无上限 | 查 Caffeine/Guava 配置 | 同泄漏 | 代码 + 缓存 size 指标 |
| 堆过小 | 峰值超过 `-Xmx` | 先排除泄漏再扩容 | 频繁 GC 后仍 OOM | 对比峰值与 Xmx |
| 大对象 | 一次加载过大 | 对齐接口/SQL 时间 | 尖刺后可回落 | histogram 看 `[B`/巨集合；慢 SQL |
| Metaspace | 类元数据耗尽 | 看类数量，不看堆 | **`OOM: Metaspace`** | `jstat -gcmetacapacity`；`jcmd PID VM.classloader_stats`；`MaxMetaspaceSize` |
| 堆外 Direct | DirectByteBuffer 等 | RSS≫堆 | **`Direct buffer memory`**；OOMKilled 也可能 | `ps -o rss=`；NMT；`MaxDirectMemorySize` |
| GC Thrashing | 堆被占满仍狂分配 | GC 日志 + jstat | FGC 风暴；`63M->62M` | `-Xlog:gc*`；`jstat -gcutil PID 1000` |
| 容器杀进程 | cgroup 内存不够 | 无 Java OOM 也死 | Exit **137** / OOMKilled | `kubectl describe pod`；`dmesg`；核算 limit≥堆+元空间+Direct+余量 |

**GC 日志怎么读（两问）**

1. **极勤吗？** Full / 长 Pause 是否很密；`FGC`/`FGCT` 是否狂涨  
2. **回收有效吗？** `63M->62M(64M)` 差值≈0 就是白忙  

### 2.2 线程与并发（常对应 U2/U3/U4 + S-THREAD/S-CPU）

| 子问题 | 说明 | 思路 | 关键现象 | 命令 |
|--------|------|------|----------|------|
| 死锁 | 锁顺序环 | jstack 搜 deadlock | CPU 低；有明确段 | `jstack`；`grep deadlock` |
| 锁拥堵 | 持锁做 IO | 大量 BLOCKED 等同一锁 | 慢/卡 | `jstack`×2 |
| 死等 | join/latch/无超时 | WAITING 看在等什么 | 无 deadlock 也挂 | `jstack` |
| 死循环 | 空转 | 高 CPU + 同一 RUNNABLE | 核打满 | `top -Hp` → tid 转十六进制 → 对 `nid=` |
| 线程泄漏 | 只建不关 | 两次 dump 比数量 | 线程数持续涨 | `jstack`×2；监控 Threads |
| 线程池打满 | 队列满后拒绝 | 日志 + 池指标 | `RejectedExecutionException` | 日志；`jstack` 看 pool 线程 |
| 日志阻塞 | 同步 appender | 栈在 log4j/logback | 低 CPU 假死 | `jstack` 搜 Appender |

### 2.3 其它本地资源

| 子问题 | 现象 | 命令 |
|--------|------|------|
| FD 泄漏 | `Too many open files` | Linux：`ls /proc/PID/fd \| wc -l`；`lsof -p PID \| wc -l`；`ulimit -n` |
| 栈溢出 | `StackOverflowError` | 看异常栈重复帧；`-Xss` 仅治标 |

---

## 3. 推荐顺序

```text
1. 异常原文（OOM 类型 / Rejected / StackOverflow）
2. CPU 高 → 热点 nid；CPU 低+卡 → jstack 看堵点
3. 内存 → 四选一：堆 / Metaspace / Direct / 容器杀
4. 需要 MAT 再 dump；能 jstat/histogram/日志解决的不上 dump
```

---

## 4. 和生产启动参数（建议常备）

```bash
# 示例（按容量改数值）
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/data/dump
-Xlog:gc*:file=/var/log/app/gc.log:time,uptime,level,tags:filecount=5,filesize=50M
-XX:MaxMetaspaceSize=256m
-XX:MaxDirectMemorySize=512m
# 可选：-XX:NativeMemoryTracking=summary
```

容器内务必保证：**limit > Xmx + Metaspace + Direct + 线程栈余量**。

---

## 5. 环境要点

| 环境 | 注意 |
|------|------|
| 单机 | 直接 jcmd/jstack；dump 看磁盘 |
| 集群 | 先定位坏实例再上机 |
| K8s | 镜像可能无 JDK 工具 → 靠 GC 日志/APM/临时诊断容器；dump 落到 volume |
| 阿里云 | ARMS JVM/线程面板可先看 |

详见 [L4](../../L4-环境/部署环境差异.md)。
