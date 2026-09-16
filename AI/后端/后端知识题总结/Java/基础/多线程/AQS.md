- `AQS`（**`AbstractQueuedSynchronizer`**）**一个用于构建锁和同步器的框架**
- 是`juc`锁底层基础（比如所有的`ReentrantLock`、读写锁、`CountDownLatch`）
- 原理：**双向链表阻塞队列 + `state`状态变量 + `CAS`**
  - 比如：厕所门口维护一条**双向链表队列**，通过**`state`状态变量**标记蹲位是否被占用

