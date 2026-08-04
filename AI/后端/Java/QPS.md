## 基础定义

1. QPS（Queries Per Second）：每秒查询率

   - 单位时间（1秒）服务器能够处理的请求数量

   - 查询 ≠ 只读请求：现在行业通用含义泛指**所有接口请求**（GET/POST/PUT/DELETE）

   - 同义概念：TPS（Transactions Per Second，每秒事务数）

     - 接口场景：QPS ≈ TPS
     - 数据库事务场景：一次接口可能包含多次 DB 事务，TPS < QPS

   - 区分容易混淆指标：

   - 

   - | 指标   | 含义                                      |
     | ------ | ----------------------------------------- |
     | QPS    | 每秒收到并处理完成的**请求数**            |
     | RT     | Response Time，单次请求**响应耗时（ms）** |
     | 并发数 | 同一时刻正在执行中的请求数量              |

2. 核心公式（性能测试最重要）

   - 并发数 = QPS * RT / 1000

   - RT 单位：毫秒 (ms)

   - 举例：

     接口平均 RT=200ms，服务 QPS=500

     并发数 = 500 × 200 / 1000 = **100**

     代表稳定运行时，系统同时有 100 个请求在处理

   - 反向推导：Tomcat 核心线程数设置参考：**预估最大并发数 × 1.2~1.5**

3. Java 应用中 QPS 由什么决定？

   - CPU 瓶颈（最常见）
     - 大量计算、JSON 序列化、循环逻辑、频繁 GC
     - 现象：CPU 占用持续 >85%，RT 变长，QPS 上不去
   - IO 瓶颈（微服务 / 数据库主流）
     - MySQL 查询、Redis 调用、HTTP 远程调用、文件读写
     - Java 线程大量阻塞等待 IO，线程池耗尽
     - IO 密集型服务：**QPS 上限不由 CPU 决定，由 IO 等待时长决定**
   - 资源限制
     - Tomcat/Undertow 线程池容量、数据库连接池、Redis 连接数
     - JVM 堆内存不足、频繁 FullGC 直接打垮 QPS

4.  Java 如何统计 QPS？

   - 方式 1：监控框架（生产推荐）

     - SpringBoot：**Micrometer + Prometheus + Grafana**

     - ```sql
       meterRegistry.counter("api.request").increment();
       ```

     - Alibaba Sentinel、Hystrix 内置实时 QPS 统计

     - SkyWalking / Pinpoint 链路监控自动展示接口 QPS

   - 方式 2：简单代码实现（限流 / 本地统计）

     - ```java
       // 使用Guava RateLimiter 或者滑动窗口统计
       // 简易滑动窗口思想：记录1s内请求总数
       AtomicInteger count = new AtomicInteger(0);
       
       // 每次请求入口
       count.incrementAndGet();
       
       // 定时任务每秒输出QPS
       ScheduledExecutorService timer = Executors.newSingleThreadScheduledExecutor();
       timer.scheduleAtFixedRate(() -> {
           int qps = count.getAndSet(0);
           System.out.println("当前QPS：" + qps);
       },1,1, TimeUnit.SECONDS);
       ```

     - ⚠️ 简易计数器存在**临界误差**，生产要用**滑动时间窗口**（Sentinel 采用）。

5. 常见误区

   - QPS 越高代表接口越快？❌
     - 相同服务器下，同等并发，RT 越低，QPS 才能越高。
     - 高 QPS 可能是压测并发量堆出来的，RT 已经严重恶化。
   - 单机 QPS 可以无限扩容？❌
     - 存在拐点：到达临界点后，继续增加请求，QPS 不升反降，RT 暴涨（雪崩）
   - QPS ≠ 用户并发人数
     - 用户会多次点击、刷新页面；1 个活跃用户可能产生 3~10 次请求。

6. 实战例子（Java 后端压测）

   - 单机 SpringBoot 应用，无 DB，纯内存逻辑：
     - RT=10ms，线程池 200
     - 理论最大 QPS ≈ 200 / (10/1000) = **20000 QPS**
   - 如果加上 MySQL 查询，RT 变成 200ms
     - 理论最大 QPS ≈ 200 / (200/1000) = **1000 QPS**

   

7. 延伸：和限流关系

   - Sentinel 限流规则直接基于 QPS 配置：

   - ```java
     flowRule.setCount(1000);
     ```

   - 代表限制接口最大每秒处理 1000 次请求，超过直接拒绝。



