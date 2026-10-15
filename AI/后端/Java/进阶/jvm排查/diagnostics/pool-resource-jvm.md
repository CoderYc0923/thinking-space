# 第 3 周：资源与池化（选做，很像线上）实操笔记

> 对应：[jvm-dump-usecases实操教程](../jvm-dump-usecases实操教程.md) **第 3 周**  
> 仓库 case：`ThreadLeak` / `ThreadPoolSaturation` / `ConnectionPoolExhaustion` / `FileDescriptorLeak` / `StackOverflow`  
> 和前两周关系：第 1 周练「卡住怎么分」；第 2 周练「内存涨哪块」；本周练 **线程/连接/FD/栈** 这类线上最常见的资源打满

---

- 由「资源与池化」引起的线上故障（很常见）
  - **线程泄漏**：只 `new Thread` / 只提交不结束，线程数持续涨 → 内存涨、上下文切换多、最终创建失败
  - **线程池打满**：核心/最大线程 + 队列都满 → 新任务拒绝或调用方一直堵着
  - **连接池耗尽**：DB/Redis/HTTP 连接借出不还，或慢 SQL 占满 → 接口大面积超时（CPU 往往不高）
  - **FD / 句柄泄漏**：文件/Socket 打开不关 → `Too many open files`（Linux）或句柄耗尽
  - **栈溢出**：深递归 / 过大栈帧 → `StackOverflowError`（和堆 OOM 不是一类）

- 口诀：
  - 线程数持续涨、CPU 不一定高 → 先 `jstack` **打两次对比**线程名数量
  - 接口超时 + CPU 低 + 大量 WAITING → 先怀疑 **等锁 / 等连接池 / 等队列**
  - 池相关：看是 **池满拒绝**（日志 `RejectedExecutionException`）还是 **线程堵在 getConnection**（栈在池里）
  - I/O 突然全挂 → 想 FD/句柄，不只盯堆
  - 异常是 `StackOverflowError` → 看栈深度 / `-Xss`，别当堆 OOM 去 dump

- 口诀 → 线上常用命令

  | 场景 | 线上先看 | 常用命令 / 动作 |
  |------|----------|-----------------|
  | 线程泄漏 | 监控 Threads；两次线程 dump 对比 | `jstack <pid> > t1.txt`，隔 30～60s 再打 `t2.txt`；或 `jcmd <pid> Thread.print` |
  | 线程池打满 | 应用日志拒绝；池指标 active/queue | 日志搜 `RejectedExecutionException`；`jstack` 看 `pool-*-thread-*` 是否全忙 |
  | 连接池耗尽 | Hikari/Druid 超时日志；大量 WAITING | 日志搜 `Connection is not available` / `request timed out`；`jstack` 搜 `HikariPool` / `getConnection` / `Semaphore.acquire` |
  | FD 泄漏 | `Too many open files`；FD 计数涨 | Linux：`ls /proc/<pid>/fd \| wc -l`、`lsof -p <pid> \| wc -l`、`ulimit -n` |
  | 栈溢出 | 异常栈本身 | 日志里的 `StackOverflowError` 与重复栈帧；启动参数 `-Xss` |

  - 本机练习写法（工具相同）：
    ```powershell
    $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
    & "$jdk\jps.exe" -l
    & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\usecases\threads-1.txt
    Start-Sleep -Seconds 5
    & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\usecases\threads-2.txt
    ```

- 五个 case 一眼分清

  | Case | 故障画像 | CPU | 第一工具 | 关键信号 |
  |------|----------|:---:|----------|----------|
  | `ThreadLeak` | 线程只增不减 | 低 | `jstack`×2 | 大量 `thread-N`，TIMED_WAITING |
  | `ThreadPoolSaturation` | 池+队列满，任务被拒 | 低～中 | 控制台拒绝日志 + `jstack` | `RejectedExecutionException`；pool 线程忙/睡在任务里 |
  | `ConnectionPoolExhaustion` | 等连接卡住 | **低** | `jstack` | 大量 `WAITING` + `Semaphore.acquire`（线上常是 Hikari） |
  | `FileDescriptorLeak` | 打开文件不关 | 低 | 句柄/FD 计数 | `Too many open files`（Windows 文案可能不同） |
  | `StackOverflow` | 深递归炸栈 | 低 | 异常栈 | `StackOverflowError`，同一方法反复出现 |

- 采证前公共准备
  - 工作目录：
    ```powershell
    cd D:\code-self\thinking-space\AI\后端\Java\进阶\jvm排查\diagnostics
    ```
  - JDK：
    ```powershell
    $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
    ```
  - 总原则：启动窗口**不要关** → 另开终端采证 → 证据落到 `usecases/` → `Ctrl+C` 结束  
  - 推荐顺序（由像线上到概念）：连接池 → 线程池 → 线程泄漏 → 栈溢出 → FD（Windows 上概念为主）

---

## 模拟 A：ConnectionPoolExhaustion（连接池耗尽）★最像线上

- 故障画像：接口大面积超时 / 像假死；**CPU 往往不高**；日志里常见等连接超时；和「死锁」不同——通常**没有** `Found one Java-level deadlock`
- 本质：池容量有限；连接借出后不归还（或占太久）→ 后来者一直等
- usecases 源码本质（用 `Semaphore` 模拟池，不是真 Hikari，但栈形态同类）：
  ```java
  Semaphore connectionPool = new Semaphore(5);  // 池大小 5
  // 起 20 个线程：
  connectionPool.acquire();          // 拿不到就 WAITING
  Thread.sleep(30000);               // 占着连接
  // finally 里故意不 release() → 许可回不来
  ```
- 启动：
  ```powershell
  .\run-usecase.ps1 ConnectionPoolExhaustion
  ```
- 排查（另开终端，建议在打印 `Waiting: N` 之后打栈）：
  ```powershell
  $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
  & "$jdk\jps.exe" -l
  New-Item -ItemType Directory -Force -Path .\usecases | Out-Null
  & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\usecases\threads-conn-pool.txt
  ```
- 在 `threads-conn-pool.txt` 里搜：
  - 线程名 `ConnectionWorker-`
  - `WAITING`（或 `TIMED_WAITING`）
  - `Semaphore.acquire` / `AbstractQueuedSynchronizer`
  - **通常没有** deadlock 段
- 线上对照：Hikari 日志 `Connection is not available, request timed out`；栈在 `HikariPool.getConnection`
- 口述：连接借出不还或慢查询占满池 → 加大池只是缓兵之计；修泄漏、`try-with-resources`、慢 SQL、合理超时
- 结束：等演示跑完或 `Ctrl+C`

---

## 模拟 B：ThreadPoolSaturation（线程池打满）

- 故障画像：任务变慢 / 失败；日志出现拒绝；后台任务不再消化；压力一大更明显
- 本质：`最大线程数 + 队列容量` 有上限，提交速度 > 消化速度 → 队列满后 **拒绝**（默认 `AbortPolicy`）
- usecases 源码本质：
  ```java
  // core=2, max=4, queue=10  → 最多同时「在飞」约 4+10=14
  // 提交 50 个、每个 sleep 10s 的任务 → 超出部分 RejectedExecutionException
  ```
- 启动：
  ```powershell
  .\run-usecase.ps1 ThreadPoolSaturation
  ```
  - 注意：该 case **会自己结束**（约半分钟监控后 shutdown）。要在出现 `REJECTED` / `Queue: 10` 时尽快打 `jstack`
- 排查：
  ```powershell
  $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
  & "$jdk\jps.exe" -l
  & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\usecases\threads-pool-sat.txt
  ```
- 看什么：
  - 控制台：`❌ Task N REJECTED`、`Pool Status - Active: 4/4, Queue: 10`
  - jstack：`pool-*-thread-*` 多在 `TIMED_WAITING`（本 case 在 `Thread.sleep`）或 RUNNABLE；说明工人都占着，不是空闲
- 口述：池+队列打满 → 拒绝或调用方阻塞；修：加大合理容量、异步削峰、缩短任务耗时、换拒绝策略并做好降级，别无限加大队列把内存打爆
- 和连接池区别：
  | | 连接池耗尽 | 线程池打满 |
  |---|------------|------------|
  | 在等什么 | DB 连接 | 执行线程 / 队列位 |
  | 常见日志 | getConnection 超时 | `RejectedExecutionException` |
  | jstack | 堵在池的 acquire | pool worker 全忙或调用方提交处卡住 |

---

## 模拟 C：ThreadLeak（线程泄漏）

- 故障画像：运行越久线程越多；RSS/堆可能跟着涨；最终可能 `OutOfMemoryError: unable to create new native thread`（视 OS 限制）
- 本质：不断 `new Thread().start()`，线程不退出，引用还握着
- usecases 源码本质：
  ```java
  while (true) {
      Thread t = new ImProperThread();  // run() 里 while(running) sleep
      t.setName("thread-" + i);
      t.start();                        // 只增不减
      sleep(100);
  }
  ```
- 启动：
  ```powershell
  .\run-usecase.ps1 ThreadLeak
  ```
  - 跑十几秒再采证即可，不必等到系统吃紧
- 排查（**必须打两次**）：
  ```powershell
  $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
  & "$jdk\jps.exe" -l
  & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\usecases\threads-leak-1.txt
  Start-Sleep -Seconds 10
  & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\usecases\threads-leak-2.txt

  # 粗看 thread- 数量是否明显增加
  (Select-String -Path .\usecases\threads-leak-1.txt -Pattern '"thread-\d+"').Count
  (Select-String -Path .\usecases\threads-leak-2.txt -Pattern '"thread-\d+"').Count
  ```
- 在 dump 里搜：
  - `"thread-123"` 这类名字大量出现
  - 状态多为 `TIMED_WAITING`（sleep）
  - 第二次比第一次明显更多 → 泄漏
- 口述：线程只建不关 → 用线程池、可结束的任务、禁止无界狂 `new Thread`
- 结束：`Ctrl+C`（线程会很多，尽早停）

---

## 模拟 D：StackOverflow（栈溢出）

- 故障画像：某个请求/任务直接失败；日志 `java.lang.StackOverflowError`；**不是** `Java heap space`
- 本质：调用栈太深（无限递归或超深调用），超过 `-Xss` 栈空间
- usecases 源码本质：
  ```java
  void recursiveMethod() {
      recursionDepth++;
      // 局部变量占一点栈
      recursiveMethod();  // 无退出
  }
  ```
- 启动：
  ```powershell
  .\run-usecase.ps1 StackOverflow

  # 想更快炸：把线程栈改小（通过 ExtraJvmArgs）
  .\run-usecase.ps1 StackOverflow -ExtraJvmArgs "-Xss256k"
  ```
- 排查：
  - **主看启动窗口异常**即可（本 case 会 catch 并打印前几帧）
  - 搜：`StackOverflowError`、`recursiveMethod` 反复出现
  - 一般**不需要** hprof；需要时看业务日志里的完整栈
- 口述：栈溢出看调用深度与 `-Xss`；修递归终止条件、改迭代、避免过深调用链；加大 `-Xss` 只能治标
- 结束：进程打印完会退出

---

## 模拟 E：FileDescriptorLeak（文件句柄泄漏）

- 故障画像：忽然不能打开文件/连网/写日志；Linux 常见 `Too many open files`；堆可能看起来还行
- 本质：`InputStream`/Socket 等打开后不 `close`，FD/句柄占满
- usecases 源码本质：
  ```java
  List<FileInputStream> leakedStreams = new ArrayList<>();
  while (true) {
      Path temp = Files.createTempFile(...);
      FileInputStream in = new FileInputStream(temp.toFile());
      leakedStreams.add(in);  // 故意不 close
  }
  ```
- 启动：
  ```powershell
  .\run-usecase.ps1 FileDescriptorLeak
  ```
- **Windows 注意**：
  - 可能不会出现 Linux 同款文案 `Too many open files`，而表现为别的 IO 异常或很慢才爆
  - 本机重点理解「打开不关」；精确数 FD 更适合 Linux：`ls /proc/<pid>/fd | wc -l`、`lsof -p <pid>`
  - Windows 可粗看句柄：任务管理器 → 详细信息 → 句柄数，或：
    ```powershell
    Get-Process -Id <pid> | Select-Object Id, HandleCount
    ```
    隔几秒看 `HandleCount` 是否持续涨
- 口述：FD/句柄泄漏 → `try-with-resources` / 确保 close；查谁重复打开同一类文件或连接
- 结束：case 捕获异常后会尝试清理；也可 `Ctrl+C`

---

## 和「卡死」第 1 周的关系（别混）

| 第 1 周 | 第 3 周 | 怎么分 |
|---------|---------|--------|
| `Deadlock` | — | 有明确 deadlock 环 |
| `InfiniteWait` | `ConnectionPoolExhaustion` | 都是低 CPU 等；本周明确是**等池许可** |
| `InfiniteLoop` | — | 高 CPU 空转，不是池满 |
| `Log4j` | `ThreadPoolSaturation` | 都可能「慢」；一个堵在日志锁，一个池/队列满 |

低 CPU + 超时：**先 `jstack`**，再看栈底是锁、join、**连接池**还是别的。

---

## 通关自检（第 3 周加分项）

- [ ] `ConnectionPoolExhaustion`：能指到 `Semaphore.acquire` / 说明线上等价 Hikari 等待
- [ ] `ThreadPoolSaturation`：能解释拒绝发生在「线程满 + 队列满」之后
- [ ] `ThreadLeak`：两次 `jstack` 能看出线程数上涨
- [ ] `StackOverflow`：能区分 `StackOverflowError` vs 堆 OOM
- [ ] `FileDescriptorLeak`：知道 Linux 看 `/proc/.../fd`，Windows 以句柄/概念为主

每案可记：

```text
Case：
现象（CPU / 超时 / 拒绝 / 异常文案）：
第一工具：
关键证据（栈 5～10 行或日志一行）：
根因一句话：
修复思路：
线上对应（Hikari / 线程池 / ulimit …）：
```

---

## 推荐动手顺序（复制即用）

```powershell
cd D:\code-self\thinking-space\AI\后端\Java\进阶\jvm排查\diagnostics
$jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"

.\run-usecase.ps1 ConnectionPoolExhaustion
.\run-usecase.ps1 ThreadPoolSaturation
.\run-usecase.ps1 ThreadLeak
.\run-usecase.ps1 StackOverflow -ExtraJvmArgs "-Xss256k"
.\run-usecase.ps1 FileDescriptorLeak
```

官方英文步骤：`jvm-dump-usecases/docs/connection-pool-exhaustion.md`、`threadpool-saturation.md`、`threadleak.md`、`filedescriptor-leak.md`。

做完连接池 + 线程池，第 3 周「很像线上」的主干就过了；FD 在 Windows 上理解到位即可。
