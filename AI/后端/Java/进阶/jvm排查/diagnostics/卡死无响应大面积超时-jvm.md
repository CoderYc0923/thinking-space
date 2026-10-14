- 由`jvm`引起的卡死、无响应、接口大面积超时，主要看CPU高低区分
  - 死锁、线程池打满、锁无限等待
  - `CountDownLatch` / 栅栏未放开（某线程异常退出、其余永久等待）
  - 高 CPU 死循环、日志框架阻塞（也常表现为「慢到像挂了」）

- 口诀：
  
  - CPU低 + 卡住，先看`jstack`
  - CPU高 + 卡住/狂转，`jstack`对齐繁忙线程
  - 有明确`deadlock`段，死锁
  - 没有明确`deadlock`段，可能是无限等待
  
- 采证前公共准备（四个模拟通用）
  - 工作目录：
    ```powershell
    cd D:\code-self\thinking-space\AI\后端\Java\进阶\jvm排查\diagnostics
    ```
  - JDK 工具（建议与脚本同一套）：
    ```powershell
    $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
    ```
  - 总原则：启动窗口**不要关** → 另开终端 `jps` 找 PID → `jstack`/`jcmd` 打线程栈 → 看完 `Ctrl+C` 结束

---

- 模拟B Deadlock（死锁）
  - 故障画像：业务卡住 / 接口大面积超时 / 进程还在但像假死；**CPU 往往不高**（区别于死循环占满核）
  - 两个线程互相持有对方需要的锁，形成环等待
  - 与【锁竞争导致慢】不同：死锁是**永久卡死**，不是单纯变慢
  - lab 源码本质（`DeadlockSimulator`）：
    ```java
    // t1: 先锁 lock1，再锁 lock2
    // t2: 先锁 lock2，再锁 lock1
    // sleep 一点时间，提高交叉持锁概率 → 环等待 → BLOCKED
    ```
  - 启动命令：
    ```powershell
    # 方式1：lab 专用脚本
    .\run-deadlock.ps1
    
    # 方式2：usecases
    .\run-usecase.ps1 Deadlock
    ```
  - 排查命令（另开终端）：
    ```powershell
    $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
    & "$jdk\jps.exe" -l
    # 记下 application.jar / MainApp 对应 PID
    
    & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\threads-deadlock.txt
    # 或
    & "$jdk\jcmd.exe" <pid> Thread.print | Out-File -Encoding utf8 .\threads-deadlock.txt
    ```
  - 在 `threads-deadlock.txt` 里搜：
    - `Found one Java-level deadlock`
    - `BLOCKED`
    - `waiting to lock` / `locked`
  - 口述：交叉持锁环等待 → 统一加锁顺序 / 缩小锁范围 / `tryLock` 超时
  - 结束：回到启动窗口 `Ctrl+C`

---

- 模拟C InfiniteWait（低 CPU 无限等待 —— 本 case 只演示其中一种）
  - 故障画像（广义）：进程还在、业务不往前走；**CPU 很低**，像「挂死」
  - **先纠偏**：线上「无限等待」≠ 只会等锁。常见还有：
    | 在等什么 | jstack 里常看到 | 本仓库后续可练 |
    |----------|-----------------|----------------|
    | 锁 / synchronized / Lock | BLOCKED / waiting to lock | 本 case、Deadlock |
    | `join` / `CountDownLatch` / `CyclicBarrier` | WAITING（等线程结束、等计数归零） | 本 case 含 join |
    | 线程池队列 / 自己提交的任务永远跑不完 | WAITING/TIMED_WAITING 在 pool、queue | `ThreadPoolSaturation` |
    | 数据库连接池拿不到连接 | WAITING 在 Hikari/池的 getConnection | `ConnectionPoolExhaustion` |
    | `wait()` / 条件队列没人 `notify` | WAITING on object monitor | — |
    | 网络/RPC 阻塞读 | WAITING/TIMED_WAITING 在 socket/read | — |
  - 排查共性：低 CPU → 先 `jstack`，看线程卡在**哪一类等待**，不要一上来断定「死锁」
  - 和 Deadlock 的区别：
    - Deadlock：环等待，常有 `Found one Java-level deadlock`
    - 广义 InfiniteWait：**没有 deadlock 段也可能永久挂**；本 case 是「持锁 + join」这一种
  - **本 case 具体模拟的是**（`InfiniteWait` 源码）：锁 + join，不是线程池/连接池
    ```java
    Object waitObj = new Object();
    synchronized (waitObj) {          // 主线程先拿到锁
        Thread t = new Thread(() -> {
            synchronized (waitObj) {  // 子线程要同一把锁 → 永远进不去
                // ...
            }
        });
        t.start();
        t.join();                     // 主线程在仍持锁时 join 等子线程结束 → 互相等死
    }
    ```
  - 本质一句话（仅对本 case）：持锁线程去等另一个需要同锁的线程结束 → **锁 + join 组合挂起**
  - 启动命令：
    ```powershell
    .\run-usecase.ps1 InfiniteWait
    ```
  - 排查命令（另开终端）：
    ```powershell
    $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
    & "$jdk\jps.exe" -l
    
    & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\threads-infinitewait.txt
    # 或
    & "$jdk\jcmd.exe" <pid> Thread.print | Out-File -Encoding utf8 .\threads-infinitewait.txt
    ```
  - 在 `threads-infinitewait.txt` 里搜（针对本 case）：
    - `WAITING` / `BLOCKED`
    - `join`
    - `synchronized`
    - 画清：谁持锁、谁在等锁、谁在 join
    - **通常没有** `Found one Java-level deadlock`
  - 口述：
    - 广义：低 CPU 挂起 → 线程在等锁/join/池/IO/栅栏…，用栈定位「等什么」
    - 本 case：主线程持锁 join，子线程抢同锁失败 → 勿在持锁临界区里 join
  - 结束：`Ctrl+C`

---

- 模拟D InfiniteLoop（高 CPU 死循环）
  - 故障画像：服务卡住或极慢；**CPU 很高**（某核/某线程打满）——和 B/C 的低 CPU 假死相反
  
  - 与死锁不同：不是锁环，而是线程在**空转计算**，占满 CPU
  - usecases 源码本质（`InfiniteLoop`）：
    ```java
    // 名为 calculation 的线程：
    while (true) {
        result = 15 * 3;   // 无退出条件的死循环
    }
    // 主线程 join 这些线程 → 进程一直不退出
    ```
    
  - 启动命令：
    ```powershell
    .\run-usecase.ps1 InfiniteLoop
    ```
    
  - 排查命令（另开终端）：
    ```powershell
    $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
    & "$jdk\jps.exe" -l
    
    # 1）先确认高 CPU：任务管理器看 java.exe，或
    Get-Process -Id <pid> | Select-Object Id, ProcessName, CPU
    
    # 2）打线程栈（建议隔几秒打两次，对比是否同一热点）
    & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\threads-infiniteloop-1.txt
    Start-Sleep -Seconds 3
    & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\threads-infiniteloop-2.txt
    
    # 通过两次dump判断同一业务线程是否还停留在同一行代码上，若是，说明它一直在转，像死循环。
    ```
    
  - 在 dump 里搜：
    - 线程名 `calculation`
    - 状态 `RUNNABLE`
    - 两次 dump 栈几乎不变 → 死循环嫌疑大
    
  - 口述：高 CPU + RUNNABLE 热点栈 → 死循环/热点计算；修退出条件或限流，不是先加机器
  
  - 结束：`Ctrl+C`

---

- 模拟E Log4j（日志 appender 阻塞）
  - 故障画像：接口很慢 / 像卡住；CPU **不一定为 0**（可能有一点），内存往往正常；压力一大更容易爆
  - 本质：大量线程狂打日志，卡在 **Log4j 同步写 / appender 锁** 上，业务线程被日志拖死
  - usecases 源码本质（`Log4JCase`，参数名是 `Log4j`）：
    ```java
    // 起 30 个线程，每线程死循环：
    while (true) {
        log.debug("...");   // 争用 log4j 内部同步，大量 BLOCKED / 等待
    }
    ```
  - 启动命令：
    ```powershell
    .\run-usecase.ps1 Log4j
    ```
  - 排查命令（另开终端）：
    ```powershell
    $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
    & "$jdk\jps.exe" -l
    
    & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\threads-log4j.txt
    # 或
    & "$jdk\jcmd.exe" <pid> Thread.print | Out-File -Encoding utf8 .\threads-log4j.txt
    
    # 看到大量业务线程BLOCKED且线程名都相同，栈都在log4j / callAppenders，且同一个锁地址（都在抢一同一把RootLogger）锁，所以判断日志同步锁把线程堵住了
    ```
  - 在 `threads-log4j.txt` 里搜：
    - 线程名 `waiting-log4j-t`
    - `log4j` / `Appender` / `Logger`
    - `BLOCKED` / `WAITING`
    - 是否大量线程堵在同一日志调用栈
  - 口述：慢不一定是业务死锁；先看是否日志同步阻塞；异步 appender、降日志级别、限流打点
  - 结束：`Ctrl+C`

---

- 四类「卡死/超时」怎么一眼分辨

  | 模拟 | 启动 | 典型 CPU | jstack 关键信号 | 一句话根因 |
  |------|------|----------|-----------------|------------|
  | Deadlock | `.\run-deadlock.ps1` 或 `.\run-usecase.ps1 Deadlock` | 低 | `Found one Java-level deadlock` | 锁顺序环等待 |
  | InfiniteWait | `.\run-usecase.ps1 InfiniteWait` | 低 | WAITING/BLOCKED（本 case：join+持锁；线上还可能等池/IO/栅栏） | 低 CPU 永久等「某样东西」 |
  | InfiniteLoop | `.\run-usecase.ps1 InfiniteLoop` | **高** | `calculation` + RUNNABLE | 空转占满 CPU |
  | Log4j | `.\run-usecase.ps1 Log4j` | 低～中 | `waiting-log4j-t*` 堵在 log | 日志同步拖死业务 |

---

- 排查速查（复制即用）

  ```powershell
  cd D:\code-self\thinking-space\AI\后端\Java\进阶\jvm排查\diagnostics
  $jdk = "D:\Java\jdks\jdk-21.0.11_10\bin"
  
  # --- 终端1：启动其中一个 ---
  # .\run-deadlock.ps1
  # .\run-usecase.ps1 InfiniteWait
  # .\run-usecase.ps1 InfiniteLoop
  # .\run-usecase.ps1 Log4j
  
  # --- 终端2：采证 ---
  & "$jdk\jps.exe" -l
  & "$jdk\jstack.exe" <pid> | Out-File -Encoding utf8 .\threads.txt
  # & "$jdk\jcmd.exe" <pid> Thread.print | Out-File -Encoding utf8 .\threads.txt
  ```
