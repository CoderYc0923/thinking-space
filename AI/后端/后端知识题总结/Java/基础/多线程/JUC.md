- **Java中的一个并发工具包**：`java.util.concurrent.*`

- **常用的**：
  - **线程池：**
    - `ThreadPoolExecutor`：最核心的线程池类，用于创建和管理线程池。通过它可以灵活配置线程池参数，如核心线程数、最大线程数、任务队列等。
    - `Executors`：线程池工厂类，提供一系列静态方法来创建不同类型的线程池，如：`newFixedThreadPool（创建固定线程数的线程池）`,`newCachedThreadPool（创建可缓存线程池）`,`newSingleThreadExecutor（创建单线程线程池）`等。
  - **并发集合：**
    - `ConcurrentHashMap`：多线程Map
    - `CopyOnWriteArrayList`：读多写少的List，线程安全。
  - **协作工具：**
    - `CountDownLatch`：让一个或多个线程等待其他一组线程完成后再继续执行（倒计时，用一次）
    - `CyclicBarrier`：一组线程互相等齐再做（可重复用）
    - `Semaphore`：限流，控制同时访问某个资源的线程数量
  - **原子类：**`java.util.concurrent.atomic`
    - `AtomicInteger`，`AtomicLong`等，给单个变量做复合操作时，不用自己加锁。
  
- **示例**

  - `CountDownLatch`：倒计时，一次性，主等子、服务启动检查

    - ```java
      // 一个/多个线程等一组任务做完。countDown()减一，到0时await()放行。不能重置
      // 场景：主线程等3个工作子线程全干完再汇总
      CountDownLatch latch = new CountDownLatch(3);
      // 子线程末尾：latch.countDown();
      // 主线程卡住直到0：latch.await();
      ```

  - `CyclicBarrier`：循环屏障，可复用，多阶段并行

    - ```java
      // 一组线程互相等，都到齐了才一起过，过完可以再开下一轮
      // 场景：多人到齐再出发/分阶段并行计算
      CyclicBarrier barrier = new CyclicBarrier(3, () -> {
          System.out.println("都到了，继续");
      });
      
      // 每个线程：barrier.await();
      ```

  - `Semaphore`：信号量，限流，连接池

    - ```java
      // 控制同时访问资源的线程数，acquire()拿许可，release()还许可
      // 场景：连接池、限流（最多N个并发）
      Semaphore sem = new Semaphore(2); // 最多2个同时进
      sem.acquire();
      try {  } finally { sem.release(); }
      ```

  - `ConcurrentHashMap`：并发Map，缓存、计数

    - ```java
      // 线程安全，适合读多写少
      ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();
      
      map.put("k", 1);
      map.computeIfAbsent("k2", k -> 2);
      ```

    - 