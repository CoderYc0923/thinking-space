- 为什么需要它（对比`Future`）

  - 总结：`CompletableFuture`在`Future`基础上加了`CompletionStage`，支持回调和任务编排，用`supplyAsync/runAsync`启动，用`thenApply/thenCompose`串联，`thenCombine/allOf`并联汇总，`exceptionally`做异常降级，比纯`Future`和回调嵌套更清晰；但是也要注意**自定义线程池和异常处理**
  - `Future`
    - 取结果靠`get()`阻塞或者轮询`isDone`，需要等待
    - 编排弱，多个任务依赖容易嵌套
    - 可能存在回调地狱
  - `CompletableFuture`
    - 可回调，取结果不必阻塞
    - `thenApply / thenCombine / affOf`等链式组合，编排强
    - 链式写法不太容易有回调地狱

- 场景：**主要用在主流程不想干等，又能把几件事编排好的时候**

  - **一次请求里并行调用多个下游**

    - 比如：详情页同时查用户信息、库存、优惠、评论 -> `supplyAsync`多个 + `allOf/thenCombine`汇总，总耗时≈最慢的那个。

  - **有依赖的异步链路**

    - 比如：先查订单，再根据订单查物流/支付 -> `thenCompose`串起来，不必层层回调

    - ```java
      // 先查订单，再根据订单并行查物流 + 支付，最后拼结果
      CompletableFuture<OrderDetailVO> future = CompletableFuture
              .supplyAsync(() -> orderService.getById(orderId), executor)   // ① 查订单
          	.thenCompose(order -> {
                  // ② 用订单结果开后面的异步（flatMap：返回的还是 CF）
                  CompletableFuture<Logistics> logisticsCf =
                      CompletableFuture.supplyAsync(
                          () -> logisticsService.getByOrderId(order.getId()), executor);
                  CompletableFuture<Payment> paymentCf =
                      CompletableFuture.supplyAsync(
                          () -> paymentService.getByOrderId(order.getId()), executor);
                  // ③ 物流、支付都好了，组合成 VO
                  return logisticsCf.thenCombine(paymentCf, (logistics, payment) -> {
                      OrderDetailVO vo = new OrderDetailVO();
                      vo.setOrder(order);
                      vo.setLogistics(logistics);
                      vo.setPayment(payment);
                      return vo;
                  });
              });
      
      OrderDetailVO detail = future.join(); // 或 get()
      ```

    - 

  - **主路径先返回，后置慢慢做**

    - 比如：下单成功先返回；发短信、写日志、通知用`runAsync`（要可靠用消息队列）

  - **超时/降级**

    - 比如：调用三方慢或不稳，异步执行 + `orTimeout/completeOnTimeout`或自己`get(timeout)`，失败用`exceptionally`返回默认值

  - **聚合网关 / BFF**

    - 比如：一个接口扇出多个微服务，再拼成一个VO

- 创建方式

  - `supplyAsync`：有返回值

  - `runAsync`： 无返回值

  - `CompletableFuture.completedFuture(value)`：直接得到一个已经完成的

  - ```java
    // 有返回值
    CompletableFuture<String> f1 = CompletableFuture.supplyAsync(() -> "ok", executor);
    
    // 无返回值
    CompletableFuture<Void> f2 = CompletableFuture.runAsync(() -> dosomething(), executor);
    
    // 已完成的
    CompletableFuture.completedFuture("done");
    
    //不传`executor`时，默认常走ForkJoinPool.commonPool
    ```

- 常用编排

  - **单个后续**

    - `thenApply`：拿上一步结果 → 转换 → 返回新值（类似 map）
    - `thenAccept`：消费结果，无返回
    - `thenRun`：不关心上一步结果，只跑一段代码
    - `thenCompose`：平铺嵌套的 CF（类似 flatMap）：下一步还是异步任务时用

  - **两个任务组合**

    - `thenCombine`：两个都成功，用两个结果算一个新结果
    - `thenAcceptBoth`：两个都成功，消费两个结果
    - `applyToEither / acceptEither`：谁先完成用谁

  - **多个任务**

    - ```java
      CompletableFuture.allOf(f1, f2, f3).join();   // 全部完成（返回 Void）
      CompletableFuture.anyOf(f1, f2, f3).join();   // 任意一个完成
      
      // allOf 后若要结果，再分别 f1.join() / f2.join()。
      ```

  - **异常**

    - ```java
      f.exceptionally(ex -> "降级值");           // 出错时给默认
      f.handle((r, ex) -> ex == null ? r : fallback); // 成功失败都能处理
      f.whenComplete((r, ex) -> log...);         // 收尾，不改变结果
      ```

  - **阻塞取结果（少用在业务线程乱堵）**

    - `get()`：可抛受检异常，可设超时
    - `join()`：不抛受检，失败时多是`CompletionException`

- 注意

  - 自建线程池，别事事默认 `commonPool`
  - 区分 `*Async` 后缀：是否把后续步骤丢到线程池执行
  - 异常要 `exceptionally`/`handle`，否则 `join` 才爆
  - 别在 CF 链里再阻塞调别的 `get`，容易占满池子
  - I/O 多、要简单同步风格时，`Java 21 `虚拟线程是另一条路；编排复杂仍常用 CF