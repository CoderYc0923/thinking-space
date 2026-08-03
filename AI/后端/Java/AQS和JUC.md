## AQS & JUC 精简详解

## 一、基础边界

1. **JUC**：`java.util.concurrent`，并发工具包，所有工具底层核心几乎都是 **AQS**。
2. **AQS**：`AbstractQueuedSynchronizer`，抽象队列同步器；**底层模型 = 双向阻塞队列 + 单个同步状态 state**。
   - 定位：AQS 是**同步器框架**，不直接使用，由同步组件内部静态内部类继承实现。

## 二、AQS 核心结构

1. state（int 同步状态）

   - volatile int state；CAS 修改，原子操作。
   - 独占模式：0 = 未锁定，1 = 持有锁，>1 = 可重入次数（ReentrantLock）
   - 共享模式：state 代表剩余许可（Semaphore）、闭锁计数（CountDownLatch）

2. CLH 双向阻塞队列（FIFO）

   - Node 节点：封装等待线程、等待状态 waitStatus
   - 核心节点状态：
     - SIGNAL (-1)：后继线程需要被唤醒
     - CANCELLED (1)：线程取消等待（超时 / 中断）
     - CONDITION (-2)：等待 Condition 条件队列
     - PROPAGATE (-3)：共享模式唤醒传播

3. 两种工作模式（互斥，不可混用）

   - 

   - | 模式           | 特征                        | 典型组件                                                     |
     | -------------- | --------------------------- | ------------------------------------------------------------ |
     | 独占 Exclusive | 同一时刻仅 1 线程获取 state | ReentrantLock、ReentrantReadWriteLock 写锁                   |
     | 共享 Shared    | 多线程可同时获取 state      | Semaphore、CountDownLatch、CyclicBarrier、ReentrantReadWriteLock 读锁 |

## 三、AQS 核心模板方法（子类必须重写）

1. AQS 提供**模板方法（acquire/release）**，内部调用以下可覆写钩子方法：
   - 独占模式
     - `tryAcquire(int arg)`：尝试获取独占锁，true 成功
     - `tryRelease(int arg)`：尝试释放独占锁，true 完全释放
   - 共享模式
     - `tryAcquireShared(int arg)`：≥0 获取成功；负数失败
     - `tryReleaseShared(int arg)`：尝试释放共享资源
   - 重点歧义消除：AQS**不实现锁逻辑**，只实现排队、阻塞、唤醒；锁规则由子类实现上述 4 个方法。

## 四、acquire () 独占获取完整流程（精简）

1. `tryAcquire()` 尝试直接拿锁；成功直接返回
2. 获取失败 → `addWaiter()` 创建 Node 入 CLH 阻塞队列尾部
3. `acquireQueued()` 在队列中自旋：
   - 当前节点前驱是 head，再次尝试 tryAcquire
   - 获取成功：把自己设为 head，清空旧 head 引用
   - 获取失败：判断前驱 waitStatus=SIGNAL → `park()`阻塞线程
4. 线程被 unpark 唤醒后继续自旋；响应中断逻辑**后置处理**（默认不抛出中断）

## 五、release () 独占释放流程

1. `tryRelease()` 修改 state，判断是否完全释放锁
2. 完全释放成功：找到 head 后继有效节点，`unpark()`唤醒后继线程

## 六、共享模式关键区别

1. `acquireShared` 获取成功后，需要**向后传播唤醒**（PROPAGATE），保证多个等待线程持续唤醒；独占模式只唤醒一个后继。

## 七、Condition 条件队列（容易混淆点）

1. AQS 拥有两套队列：
   - **同步队列（CLH 主队列）**：等待锁
   - **Condition 条件队列**：等待条件 signal
2. `await()`：释放持有的锁 → 线程加入条件队列 → park 阻塞
3. `signal()`：将条件队列首节点**转移到同步队列**，等待重新竞争锁
4. 歧义重点：await 必须先持有锁；signal 不会立刻运行线程，只是丢回抢锁队列。

## 八、JUC 常用组件与 AQS 映射

1. **ReentrantLock**：独占 AQS，支持公平 / 非公平，可重入
   - 公平：入队后严格按顺序获取
   - 非公平：新来线程先 CAS 抢锁，抢失败再入队（默认）
2. **ReentrantReadWriteLock**：一把 AQS，state 高低位拆分
   - 高 16 位：读锁（共享）；低 16 位：写锁（独占）
   - 锁降级：写锁→读锁允许；读锁→写锁禁止
3. **Semaphore**：共享 AQS，state = 许可总数，限流工具
4. **CountDownLatch**：共享 AQS，state = 计数器；await 等待 state=0，countDown 递减 state
5. **CyclicBarrier**：**不直接依赖 AQS**！基于 ReentrantLock+Condition 实现，可循环复用屏障
   - 高频坑：CyclicBarrier ≠ AQS 直接实现，很多资料写错。

## 九、关键易错歧义澄清

1. **误区**：AQS = 锁
   - ✅ **正解**：AQS 是**通用同步排队框架**，本身不是锁。锁（ReentrantLock 等）是上层 API，内部组合 AQS，由子类实现获取 / 释放资源规则。AQS 只负责：线程排队、阻塞、唤醒、维护 state。
2. **误区**：CLH 队列里线程一直自旋空转，消耗 CPU
   - ✅ **正解**：仅前驱为 head 时短暂自旋尝试抢锁；抢不到就调用`LockSupport.park()`阻塞，交出 CPU。绝大多数时间线程休眠，不会持续轮询。自旋只是优化，避免频繁切换内核态。
3. **误区**：调用`interrupt()`中断线程，能直接抢锁、跳出阻塞
   - ✅ **正解**：`interrupt()`只会唤醒 park 阻塞的线程。唤醒后线程依然要进入队列正常竞争锁；中断标记只是状态，**不能强制获取同步资源**。
   - 补充：AQS 独占 acquire 默认**不立即抛出中断异常**，只是记录中断状态，拿到锁之后再处理。
4. **误区**：state 是用来记录等待线程数量
   - ✅ **正解**：state 只是一个 volatile int 变量，**本身无固定含义**，语义完全由实现 AQS 的子类自定义。
   - ReentrantLock：重入次数
   - Semaphore：剩余许可
   - CountDownLatch：剩余计数
   - ReentrantReadWriteLock：高低位分别存读锁、写锁计数
5. **误区**：只要是共享模式，就一定允许多线程同时执行
   - ✅ **正解**：共享模式只是 AQS 提供的一套 API 范式，代表支持多线程同时获取资源。**能否并发由子类控制**。
   - 例：读写锁读锁 = 共享并发；写锁 = 独占。共享≠天然并发。
6. **误区**：`condition.signal()`调用后，等待线程立刻恢复执行
   - ✅ **正解**：signal 仅仅把条件队列的节点迁移到**同步队列**。线程依旧需要排队竞争锁；没有抢到锁之前继续阻塞。
   - 硬性前提：await () /signal () 都必须在持有锁时调用，否则抛异常。
7. **误区**：CountDownLatch、CyclicBarrier 底层都是直接 AQS 实现
   - ✅ **正解**：CountDownLatch、Semaphore → 直接继承 AQS（共享模式）
   - CyclicBarrier → **没有直接继承 AQS**，内部使用`ReentrantLock + Condition`封装实现，屏障可以循环复用。
8. **误区**：unpark 多次调用会累积许可
   - ✅ **正解**：LockSupport 许可最多为 1。连续多次 unpark，等同于 1 次 unpark；一次 park 就消耗掉许可，多余 unpark 无效。
9. **误区**：公平锁 = 绝对不会出现线程插队
   - ✅ **正解**：ReentrantLock 公平锁规则：线程尝试获取锁前先检查队列是否有等待节点；
   - 但**刚唤醒出队的线程、正在队列内的线程不存在插队**。
   - 唯一容易混淆点：非公平锁新来线程可以直接 CAS 抢锁，不先入队。
10. **误区**：Node.CANCELLED 节点会主动被后台线程清理
    - ✅ **正解**：没有清理线程。取消状态的节点，只会在后续其他线程入队、自旋抢锁的过程中**被动剔除**。

## 十、LockSupport（AQS 依赖基础）

1. `park()/unpark()`：底层操作系统阻塞原语
   - unpark 可先于 park 执行（持有许可）
   - 与 Thread.stop/suspend 区别：不会产生死锁风险，AQS 唯一阻塞工具

