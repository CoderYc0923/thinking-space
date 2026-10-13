- 由`jvm`引起的卡死、无响应、接口大面积超时
  - 死锁、线程池打满、锁等待
  - `CountDownLatch` / 栅栏未放开（某线程异常退出、其余永久等待）

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
  - 采证重点：Thread Dump（不是 hprof）
    - 搜：`Found one Java-level deadlock`、`BLOCKED`、`waiting to lock` / `locked`
  - 口述：交叉持锁环等待 → 统一加锁顺序 / 缩小锁范围 / `tryLock` 超时

- 启动脚本（本目录）
  - `.\run-deadlock.ps1` 或双击 `run-deadlock.cmd`
  - 脚本会用 JDK21 跑：`MainApp deadlock`
  - 进程会一直挂着（两个非守护线程卡在锁上），**不要关这个窗口**
  - 另开终端采证（建议用同一 JDK 的 bin）：
    ```powershell
    jps -l
    jstack <pid> | Out-File -Encoding utf8 .\threads.txt
    # 或
    jcmd <pid> Thread.print | Out-File -Encoding utf8 .\threads.txt
    ```
  - 看完可用 Ctrl+C 结束脚本进程
