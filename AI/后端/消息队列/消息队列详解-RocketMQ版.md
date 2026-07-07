# 消息队列详解 — 以 RocketMQ 为核心

> 消息队列（Message Queue）是分布式系统中负责**异步通信、系统解耦、流量削峰**的核心中间件。
>
> 本文以 RocketMQ 为主线，系统梳理消息队列的全部核心知识，并附 Java + Node.js 双版实战代码。

---

## 目录

1. [基础概念回顾](#一基础概念回顾)
2. [主流 MQ 对比：为什么选 RocketMQ](#二主流-mq-对比为什么选-rocketmq)
3. [RocketMQ 核心架构](#三rocketmq-核心架构)
4. [核心概念深度解析](#四核心概念深度解析)
5. [消息类型与实战场景](#五消息类型与实战场景)
6. [事务消息——RocketMQ 的杀手锏](#六事务消息rocketmq-的杀手锏)
7. [Docker Compose 部署](#七docker-compose-部署)
8. [Java 实战代码](#八java-实战代码)
9. [Node.js 实战代码](#九nodejs-实战代码)
10. [消息可靠性保障](#十消息可靠性保障)
11. [常见问题与避坑指南](#十一常见问题与避坑指南)
12. [运维与监控](#十二运维与监控)

---

## 一、基础概念回顾

### 1.1 什么是消息队列？

消息队列本质上是一个**先进先出的管道**：

- **生产者（Producer）** 往管道里扔消息
- **消费者（Consumer）** 从管道里取消息
- **Broker（消息服务器）** 负责存储和转发

打个比方：快递驿站。你把包裹（消息）放到驿站（队列），收件人（消费者）有空再来取。你不用等收件人在家，收件人也不用时刻等着快递——这就是"异步解耦"。

### 1.2 四大应用场景

#### 场景 1：系统解耦

> 电商下单后，需要通知库存系统减库存、积分系统加积分、物流系统发货。如果直接调用，订单系统就要耦合三个系统。

**用 MQ 后**：订单系统只发一条"订单已支付"消息到 MQ，库存、积分、物流各自订阅，互不干扰。

```
                   ┌─→ 库存服务（扣库存）
订单服务 → MQ ─────┼─→ 积分服务（加积分）
                   └─→ 物流服务（发货）
```

新增一个营销系统？只需订阅消息即可，订单系统**零改动**。

#### 场景 2：异步处理

> 用户注册后要发验证邮件和初始化账户，这两个操作可能耗时 3 秒。用户不能等 3 秒才看到"注册成功"。

**用 MQ 后**：注册成功立即返回，同时扔消息到 MQ，后台 Worker 异步处理。用户体验从 3 秒变成 50ms。

```
同步（慢）：注册 → 发邮件(1.5s) → 初始化(1.5s) → 返回  = 3s
异步（快）：注册 → 发MQ消息(5ms) → 返回                = 50ms
                    ↓ 后台异步
              发邮件 + 初始化
```

#### 场景 3：流量削峰

> 秒杀活动，瞬时 10 万 QPS 打到后端，数据库扛不住。

**用 MQ 后**：请求先进 MQ 排队，后端按自己的处理能力（比如 5000 QPS）匀速消费。

```
瞬时 100000 QPS → MQ（缓冲排队）→ 匀速 5000 QPS → 后端处理
                         ↓
                   多出来的排队等待
                   系统不崩，只是慢一点
```

#### 场景 4：消息分发（发布/订阅）

> 用户"实名认证通过"这一事件，风控系统、额度系统、营销系统都需要知道。

一条消息，多个消费组各自独立消费，互不影响。

---

## 二、主流 MQ 对比：为什么选 RocketMQ

### 2.1 全景对比

| 特性 | RabbitMQ | Kafka | **RocketMQ** | Redis Stream |
|------|----------|-------|-------------|--------------|
| **开发语言** | Erlang | Java/Scala | **Java** | C |
| **吞吐量** | 万级 | **百万级** | 十万级 | 十万级 |
| **延迟** | 微秒级 | 毫秒级 | 毫秒级 | 微秒级 |
| **消息堆积能力** | 一般 | **极强** | 强 | 受内存限制 |
| **事务消息** | ❌ 不支持 | ❌ 不支持 | ✅ **原生支持** | ❌ |
| **顺序消息** | 支持 | 分区内有序 | ✅ **支持** | 支持 |
| **延时消息** | 插件支持 | 不支持 | ✅ **18个等级** | 不支持 |
| **消息重试** | 支持 | 不支持 | ✅ **支持** | 手动实现 |
| **消息过滤** | 有限 | 不支持 | ✅ **SQL/TAG** | 不支持 |
| **集群模式** | 镜像队列 | 分区 | **主从同步** | 主从 |
| **适用场景** | 业务异步解耦 | 日志/流计算 | **电商/金融** | 轻量/已有Redis |

### 2.2 RocketMQ 的独特优势

**1. 事务消息（最大杀器）**

这是 RocketMQ 和 Kafka、RabbitMQ 最大的区别。保证"本地事务"和"消息发送"的原子性。

```
典型场景：下单 + 发消息

❌ 不用事务消息：
  下单成功 → 发消息失败 → 库存没扣，用户付了钱

✅ 用事务消息：
  先发半消息 → 执行下单 → 成功则提交消息
                       → 失败则回滚消息
```

**2. 阿里双十一验证**

经历了 10+ 年双十一的考验，稳定性和性能有真实的大规模验证。

**3. Java 技术栈契合**

纯 Java 开发，和 Spring Boot 集成极其丝滑，调试、排错、二次开发门槛低。

**4. 丰富的消息类型**

普通消息、顺序消息、延时消息、事务消息、批量消息，开箱即用。

### 2.3 选型建议

| 场景 | 推荐 |
|------|------|
| 公司已有 Java 技术栈 + 需要事务消息 | **RocketMQ** |
| 海量日志采集、流计算、大数据管道 | Kafka |
| 传统企业、小团队、Erlang 运维能力强 | RabbitMQ |
| 已有 Redis、轻量异步场景 | Redis Stream |

---

## 三、RocketMQ 核心架构

### 3.1 架构全景图

```
                    ┌──────────────┐
                    │  NameServer  │  路由注册中心（无状态集群）
                    │  (集群)       │
                    └──┬───┬───┬──┘
                       │   │   │
          ┌────────────┼───┼───┼────────────┐
          │            │   │   │            │
          ▼            ▼   ▼   ▼            ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Broker-A │  │ Broker-B │  │ Broker-C │  （主从同步）
    │ Master   │  │ Master   │  │ Master   │
    │  ├Slave  │  │  ├Slave  │  │  ├Slave  │
    └──────────┘  └──────────┘  └──────────┘
          ▲                            ▲
          │                            │
    ┌─────┴─────┐              ┌─────┴─────┐
    │ Producer  │              │ Consumer  │
    │ (生产者)   │              │ (消费者)   │
    └───────────┘              └───────────┘
```

### 3.2 四大核心角色

| 角色 | 职责 | 特点 |
|------|------|------|
| **NameServer** | 路由注册中心，管理 Broker 地址 | 无状态、可集群、类似 DNS |
| **Broker** | 消息存储和转发 | 主从架构、持久化存储 |
| **Producer** | 消息生产者 | 从 NameServer 获取 Broker 地址后直连发送 |
| **Consumer** | 消息消费者 | 支持拉模式（Pull）和推模式（Push） |

### 3.3 工作流程

```
1. 启动阶段
   Broker 启动 → 向 NameServer 注册自己的地址和 Topic 信息
   Producer 启动 → 向 NameServer 查询要发送的 Topic 在哪些 Broker 上
   Consumer 启动 → 向 NameServer 查询要消费的 Topic 在哪些 Broker 上

2. 发送消息
   Producer → 查询 NameServer（定时刷新路由）→ 拿到 Broker 列表
           → 选择一台 Broker → 直连发送消息
           → Broker 持久化消息到磁盘

3. 消费消息
   Consumer → 查询 NameServer → 拿到 Broker 列表
            → 直连 Broker 拉取消息（长轮询）
            → 消费成功 → 返回 ACK
            → 消费失败 → 消息重试
```

### 3.4 为什么 NameServer 不用 ZooKeeper？

RocketMQ 的 NameServer 设计得非常**轻量**：

| 对比 | NameServer | ZooKeeper |
|------|-----------|-----------|
| 一致性协议 | 无，每个节点独立 | ZAB 协议（CP） |
| 数据一致性 | 最终一致 | 强一致 |
| 复杂度 | 极低 | 高 |
| 运维成本 | 几乎为零 | 需要专业运维 |
| 性能 | 极高 | 中等 |

**设计哲学**：路由信息可以短暂不一致（最终一致性），但绝不能因为 NameServer 的协调问题影响 Broker 的收发消息（可用性优先）。这是典型的 **AP 选择**。

---

## 四、核心概念深度解析

### 4.1 Topic（主题）

消息的逻辑分类。一个 Topic 代表一类消息，比如 `OrderTopic`、`PaymentTopic`。

```
Topic: OrderTopic
├── Queue-0（存放在 Broker-A）
├── Queue-1（存放在 Broker-A）
├── Queue-2（存放在 Broker-B）
└── Queue-3（存放在 Broker-B）
```

### 4.2 Queue（消息队列）

- 一个 Topic 可以有多个 Queue
- Queue 分布在不同的 Broker 上，实现**水平扩展**
- Queue 是**持久化存储的最小单元**
- 每个 Queue 内的消息是严格有序的（FIFO）

```
为什么需要多个 Queue？

❌ 1个 Queue：所有消息串行，吞吐量受限于单机
✅ 多个 Queue：并行写入不同的 Broker，吞吐量线性增长
```

### 4.3 Message（消息）

一条消息的核心字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| Topic | 所属主题 | `OrderTopic` |
| Tags | 子标签（用于过滤） | `PAID`、`SHIPPED` |
| Keys | 业务唯一标识 | `orderId:123456` |
| Body | 消息体 | `{"orderId":"123","amount":99.9}` |
| DelayTimeLevel | 延时等级 | `3` = 延时 10 秒 |

### 4.4 Consumer Group（消费组）

- **同一个消费组**内的消费者**均分 Queue**（集群模式）
- **不同消费组**各自独立消费同一条消息（广播效果）

```
Topic: OrderTopic（4个 Queue）

消费组A（库存扣减）：
  Consumer-A1 → Queue-0, Queue-1    ← 均分
  Consumer-A2 → Queue-2, Queue-3

消费组B（积分发放）：
  Consumer-B1 → Queue-0, Queue-1, Queue-2, Queue-3  ← 独立消费
```

**关键规则**：同一个消费组的消费者数量 ≤ Queue 数量，多了的消费者会空闲。

### 4.5 消费模式

| 模式 | 说明 | 场景 |
|------|------|------|
| **集群模式（CLUSTERING）** | 同组消费者均分 Queue，每条消息只被同组一个消费者处理 | 默认模式，最常用 |
| **广播模式（BROADCASTING）** | 同组每个消费者都收到全部消息 | 配置刷新、缓存更新 |

---

## 五、消息类型与实战场景

### 5.1 普通消息（同步/异步/单向）

```java
// 1. 同步发送（等待结果，最常用）
SendResult result = producer.send(msg);
// 发送失败立即知道，可以重试

// 2. 异步发送（不等待，回调通知）
producer.send(msg, new SendCallback() {
    public void onSuccess(SendResult result) { ... }
    public void onException(Throwable e) { ... }
});

// 3. 单向发送（不关心结果，性能最高）
producer.sendOneway(msg);
// 适合日志上报等不重要的场景
```

### 5.2 顺序消息

**保证同一个业务 Key 的消息按发送顺序消费。**

原理：把同一个 Key（如 orderId）的消息发送到**同一个 Queue**，消费者对同一个 Queue **串行消费**。

```
订单生命周期（必须有序）：
创建 → 支付 → 发货 → 完成

❌ 无序消费：创建 → 发货 → 支付（库存还没扣就发货了！）
✅ 顺序消费：创建 → 支付 → 发货 → 完成（同一个 orderId 进同一个 Queue）
```

```java
// 发送时指定选择器，同一个 orderId 进同一个 Queue
producer.send(msg, new MessageQueueSelector() {
    @Override
    public MessageQueue select(List<MessageQueue> mqs, Message msg, Object arg) {
        Long orderId = (Long) arg;
        int index = (int) (orderId % mqs.size());
        return mqs.get(index);
    }
}, orderId);
```

### 5.3 延时消息

消息发送后，延迟指定时间才被消费者消费。

**场景**：
- 下单 30 分钟未支付 → 自动取消订单
- 退款 24 小时后未处理 → 告警提醒
- 会议开始前 15 分钟 → 发送提醒

RocketMQ 支持 **18 个延时等级**：

```
等级:  1    2    3    4    5    6    7    8    9    10   11   12   13   14   15   16   17   18
时间: 1s   5s  10s  30s  1m   2m   3m   4m   5m   6m   7m   8m   9m  10m  20m  30m  1h   2h
```

```java
// 延时 30 分钟 = 等级 16
message.setDelayTimeLevel(16);
producer.send(message);
```

> ⚠️ 注意：延时消息在到达时间前**不会被消费**，存在磁盘上。如果延时等级不满足需求（如需要 3 小时），可以自定义 `messageDelayLevel` 配置。

### 5.4 批量消息

把多条消息打包成一次请求发送，减少网络开销。

```java
List<Message> messages = new ArrayList<>();
messages.add(new Message("TopicTest", "TagA", "Order001".getBytes()));
messages.add(new Message("TopicTest", "TagA", "Order002".getBytes()));
messages.add(new Message("TopicTest", "TagA", "Order003".getBytes()));

// 一次发送，但不能超过 4MB
producer.send(messages);
```

**限制**：
- 同一批次必须是同一个 Topic
- 总大小不能超过 4MB
- 建议单批次不超过 1MB

### 5.5 消息过滤

RocketMQ 支持 **Tag 过滤** 和 **SQL 过滤**两种方式。

#### Tag 过滤（最简单）

```
消息1: Topic=Order, Tag=PAID
消息2: Topic=Order, Tag=SHIPPED
消息3: Topic=Order, Tag=COMPLETED

消费者A：只订阅 Tag=PAID     → 只收到消息1
消费者B：订阅 Tag=PAID||SHIPPED → 收到消息1和消息2
```

#### SQL 过滤（更强大，需要 Broker 开启 enablePropertyFilter=true）

```java
// 只消费金额 > 100 的消息
consumer.subscribe("OrderTopic",
    MessageSelector.bySql("amount > 100"));
```

---

## 六、事务消息——RocketMQ 的杀手锏

### 6.1 为什么需要事务消息？

分布式系统中最经典的问题：**数据库操作和消息发送的一致性**。

```
// 典型的下单场景
@Transactional
public void createOrder(Order order) {
    orderDao.insert(order);     // 1. 插入订单到数据库
    mqProducer.send(orderMsg);  // 2. 发送消息通知扣库存
}

问题：
- 如果 1 成功、2 失败 → 订单创建了但库存没扣
- 如果 1 失败、2 成功 → 订单没创建但库存扣了（这事更大！）
```

### 6.2 事务消息的执行流程

RocketMQ 的事务消息用**两阶段提交 + 事务回查**来解决这个问题：

```
第一阶段：发送半消息
  Producer → Broker：发送一条"半消息"（消费者不可见）
  Broker → Producer：返回半消息发送成功

第二阶段：执行本地事务
  Producer：执行本地数据库操作（如下单）

第三阶段：提交或回滚
  本地事务成功 → Producer → Broker：提交消息（消费者可见）
  本地事务失败 → Producer → Broker：回滚消息（消息删除）

异常处理：事务回查
  如果 Broker 长时间没收到提交/回滚（Producer 挂了）
  → Broker 主动回查 Producer
  → Producer 检查本地事务状态
  → 返回提交或回滚
```

```
时间线：
  │
  ├─ 1. 发送半消息 ─────→ Broker（存储，但消费者看不到）
  │                         │
  ├─ 2. 执行本地事务      │ 等待提交/回滚
  │   (insert order)      │
  │    ↓                  │
  ├─ 3. 成功→提交消息 ────→ 消费者可见 ✅
  │   失败→回滚消息 ────→ 消息删除 ❌
  │
  └─ 异常：Producer 挂掉
      Broker 超时未收到确认
      → 回查 Producer（执行 checkLocalTransaction）
      → 根据本地事务状态决定提交或回滚
```

### 6.3 Java 实现

```java
// 事务消息生产者
public class TransactionProducer {
    public static void main(String[] args) throws Exception {
        // 使用 TransactionMQProducer
        TransactionMQProducer producer = new TransactionMQProducer("tx-producer-group");
        producer.setNamesrvAddr("localhost:9876");

        // 设置线程池（用于回查）
        ExecutorService executorService = Executors.newFixedThreadPool(2);
        producer.setExecutorService(executorService);

        // 设置事务监听器（核心！）
        producer.setTransactionListener(new TransactionListener() {

            /**
             * 执行本地事务
             */
            @Override
            public LocalTransactionState executeLocalTransaction(Message msg, Object arg) {
                try {
                    // 这里执行真正的业务逻辑（比如插入订单到数据库）
                    Order order = (Order) arg;
                    orderService.createOrder(order);

                    // 本地事务执行成功 → 提交消息
                    return LocalTransactionState.COMMIT_MESSAGE;

                } catch (Exception e) {
                    // 本地事务执行失败 → 回滚消息
                    return LocalTransactionState.ROLLBACK_MESSAGE;
                }
            }

            /**
             * Broker 回查本地事务状态（Producer 挂了或超时）
             */
            @Override
            public LocalTransactionState checkLocalTransaction(MessageExt msg) {
                // 根据消息中的 orderId 查询数据库，看订单是否真的创建了
                String orderId = msg.getKeys();
                Order order = orderService.getByOrderId(orderId);

                if (order != null) {
                    return LocalTransactionState.COMMIT_MESSAGE;   // 订单存在，提交
                } else {
                    return LocalTransactionState.ROLLBACK_MESSAGE;  // 订单不存在，回滚
                }
            }
        });

        producer.start();

        // 发送事务消息
        Message msg = new Message("OrderTopic", "PAID", orderId, orderJson.getBytes());
        producer.sendMessageInTransaction(msg, order);  // order 传给 executeLocalTransaction
    }
}
```

### 6.4 事务消息的三种状态

| 状态 | 含义 | 后果 |
|------|------|------|
| `COMMIT_MESSAGE` | 提交消息 | 消费者可见，正常消费 |
| `ROLLBACK_MESSAGE` | 回滚消息 | 消息删除，消费者永远看不到 |
| `UNKNOW` | 状态未知 | Broker 稍后会回查 `checkLocalTransaction` |

> **最佳实践**：如果本地事务执行耗时不确定，可以先返回 `UNKNOW`，在 `checkLocalTransaction` 中真正判断状态。

---

## 七、Docker Compose 部署

### 7.1 单机部署（开发环境）

```yaml
# docker-compose.yml
version: '3.8'

services:
  namesrv:
    image: apache/rocketmq:5.1.4
    container_name: rmq-namesrv
    ports:
      - "9876:9876"
    command: sh mqnamesrv
    environment:
      - JAVA_OPT_EXT=-Xms512m -Xmx512m
    volumes:
      - namesrv_data:/home/rocketmq/logs

  broker:
    image: apache/rocketmq:5.1.4
    container_name: rmq-broker
    ports:
      - "10909:10909"   # gRPC 端口（5.x 新版本）
      - "10911:10911"   # Remoting 端口
      - "10912:10912"   # VIP 通道端口
    environment:
      - NAMESRV_ADDR=namesrv:9876
      - JAVA_OPT_EXT=-Xms1g -Xmx1g
    volumes:
      - broker_data:/home/rocketmq/store
      - ./broker.conf:/home/rocketmq/rocketmq-5.1.4/conf/broker.conf
    command: sh mqbroker -c /home/rocketmq/rocketmq-5.1.4/conf/broker.conf
    depends_on:
      - namesrv

  dashboard:
    image: apacherocketmq/rocketmq-dashboard:latest
    container_name: rmq-dashboard
    ports:
      - "8080:8080"
    environment:
      - JAVA_OPTS=-Drocketmq.namesrv.addr=namesrv:9876
    depends_on:
      - namesrv

volumes:
  namesrv_data:
  broker_data:
```

```properties
# broker.conf（放在 docker-compose.yml 同目录）
brokerClusterName = DefaultCluster
brokerName = broker-a
brokerId = 0
deleteWhen = 04
fileReservedTime = 48
brokerRole = ASYNC_MASTER
flushDiskType = ASYNC_FLUSH

# Broker 对外地址（注意：5.x 版本使用这个配置）
brokerIP1 = 192.168.1.100  # 改成你的实际 IP，或者用宿主机 IP

# 自动创建 Topic（开发环境开启）
autoCreateTopicEnable = true
```

### 7.2 启动与验证

```bash
# 1. 启动
docker compose up -d

# 2. 查看日志
docker logs rmq-namesrv
docker logs rmq-broker

# 3. 访问 Dashboard
# 浏览器打开：http://localhost:8080

# 4. 验证发送消息
# 使用 RocketMQ 自带的测试工具
docker exec -it rmq-broker sh tools.sh org.apache.rocketmq.example.quickstart.Producer
```

### 7.3 生产环境部署要点

```
生产环境最小配置：
- 2 台 NameServer（无状态，两台就够了，不需要更多）
- 2 组 Broker（每组 Master + Slave）
  - Broker-a-master + Broker-a-slave（异步复制）
  - Broker-b-master + Broker-b-slave

高性能配置：
- 关闭自动创建 Topic：autoCreateTopicEnable=false
- 使用 SSD 磁盘
- 异步刷盘：flushDiskType=ASYNC_FLUSH
- 增大内存：-Xms4g -Xmx4g

金融级配置：
- 同步复制：brokerRole=SYNC_MASTER
- 同步刷盘：flushDiskType=SYNC_FLUSH
- 多副本：每个 Master 配 2 个 Slave
```

---

## 八、Java 实战代码

### 8.1 Maven 依赖

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.apache.rocketmq</groupId>
    <artifactId>rocketmq-spring-boot-starter</artifactId>
    <version>2.3.0</version>
</dependency>
```

### 8.2 application.yml 配置

```yaml
# application.yml
rocketmq:
  name-server: localhost:9876
  producer:
    group: order-producer-group
    # 发送超时时间
    send-message-timeout: 3000
    # 重试次数
    retry-times-when-send-failed: 3
    # 异步发送失败重试
    retry-times-when-send-async-failed: 2
  consumer:
    group: order-consumer-group
    # 消费模式
    message-model: CLUSTERING  # CLUSTERING / BROADCASTING
```

### 8.3 生产者（Spring Boot 集成）

```java
@Component
public class OrderProducer {

    @Autowired
    private RocketMQTemplate rocketMQTemplate;

    /**
     * 发送普通消息
     */
    public void sendOrderCreated(Order order) {
        // 方式1：同步发送
        SendResult result = rocketMQTemplate.syncSend("OrderTopic:PAID", order);
        System.out.println("发送结果: " + result.getSendStatus());
    }

    /**
     * 发送顺序消息（同一个 orderId 进同一个 Queue）
     */
    public void sendOrderMessageOrderly(Order order) {
        SendResult result = rocketMQTemplate.syncSendOrderly(
            "OrderTopic:PAID",
            order,
            order.getOrderId()  // 按 orderId 哈希选 Queue
        );
    }

    /**
     * 发送延时消息（30 分钟未支付取消）
     */
    public void sendDelayMessage(Order order) {
        Message<String> msg = MessageBuilder.withPayload(JSON.toJSONString(order))
                .setHeader(RocketMQHeaders.KEYS, order.getOrderId())
                .build();

        // delayLevel 16 = 30 分钟
        rocketMQTemplate.syncSend("OrderTopic:CANCEL", msg, 3000, 16);
    }

    /**
     * 发送事务消息
     */
    public void sendTransactionMessage(Order order) {
        // 使用 @RocketMQTransactionListener 配合（见下方消费者示例）
        rocketMQTemplate.sendMessageInTransaction(
            "tx-producer-group",
            "OrderTopic:PAID",
            MessageBuilder.withPayload(order).build(),
            order
        );
    }
}
```

### 8.4 消费者（Spring Boot 集成）

```java
@Component
@RocketMQMessageListener(
    topic = "OrderTopic",
    consumerGroup = "order-consumer-group",
    selectorExpression = "PAID",           // 只消费 Tag=PAID 的消息
    consumeMode = ConsumeMode.CONCURRENTLY,  // 并发消费
    consumeThreadMax = 10                    // 最大 10 个线程
)
public class OrderConsumer implements RocketMQListener<Order> {

    @Override
    public void onMessage(Order order) {
        System.out.println("收到订单消息: " + order.getOrderId());

        // 执行业务逻辑：扣库存
        try {
            inventoryService.deduct(order);
        } catch (Exception e) {
            // ⚠️ 抛出异常 → RocketMQ 会自动重试
            // 默认重试 16 次，超过则进入死信队列
            throw new RuntimeException("扣库存失败", e);
        }
    }
}
```

### 8.5 顺序消息消费者

```java
@Component
@RocketMQMessageListener(
    topic = "OrderTopic",
    consumerGroup = "order-consumer-group",
    selectorExpression = "PAID",
    consumeMode = ConsumeMode.ORDERLY,  // ← 顺序消费模式
    consumeThreadMax = 1                 // ← 单线程保证顺序
)
public class OrderlyConsumer implements RocketMQListener<Order> {
    @Override
    public void onMessage(Order order) {
        System.out.println("顺序消费: " + order.getOrderId());
        // 同一个 Queue 的消息会串行执行
    }
}
```

### 8.6 事务消息监听器

```java
@RocketMQTransactionListener(txProducerGroup = "tx-producer-group")
public class OrderTransactionListener implements RocketMQLocalTransactionListener {

    @Autowired
    private OrderService orderService;

    /**
     * 执行本地事务
     */
    @Override
    public RocketMQLocalTransactionState executeLocalTransaction(Message msg, Object arg) {
        try {
            Order order = (Order) arg;
            orderService.createOrder(order);  // 执行数据库操作
            return RocketMQLocalTransactionState.COMMIT;
        } catch (Exception e) {
            return RocketMQLocalTransactionState.ROLLBACK;
        }
    }

    /**
     * 回查本地事务状态
     */
    @Override
    public RocketMQLocalTransactionState checkLocalTransaction(Message msg) {
        String orderId = msg.getKeys();
        Order order = orderService.getByOrderId(orderId);
        if (order != null) {
            return RocketMQLocalTransactionState.COMMIT;
        } else {
            return RocketMQLocalTransactionState.ROLLBACK;
        }
    }
}
```

---

## 九、Node.js 实战代码

### 9.1 安装依赖

```bash
npm install rocketmq-client-nodejs
```

> ⚠️ 注意：Node.js 的 RocketMQ 客户端目前社区维护，官方支持不如 Java。生产环境推荐用 Java 做生产者/消费者，Node.js 通过 HTTP/gRPC 调用 Java 服务来间接操作 RocketMQ。
>
> 如果必须用 Node.js 直连，可以试试 `apache-rocketmq` 或 `@aliware/rocketmq` 包，但版本可能滞后。

### 9.2 生产者

```javascript
const { Producer } = require('rocketmq-client-nodejs');

const producer = new Producer('order-producer-group');
producer.setNamesrvAddr('localhost:9876');

async function start() {
  await producer.start();
  console.log('✅ Producer 启动成功');
}

/**
 * 发送普通消息
 */
async function sendOrderCreated(order) {
  const msg = {
    topic: 'OrderTopic',
    tags: 'PAID',
    keys: order.orderId,
    body: JSON.stringify(order),
  };

  const result = await producer.send(msg);
  console.log('✅ 发送成功:', result.msgId);
  return result;
}

/**
 * 发送延时消息（level 16 = 30分钟）
 */
async function sendDelayMessage(order) {
  const msg = {
    topic: 'OrderTopic',
    tags: 'CANCEL',
    keys: order.orderId,
    body: JSON.stringify(order),
    delayTimeLevel: 16,  // 30 分钟
  };

  const result = await producer.send(msg);
  console.log('✅ 延时消息发送成功:', result.msgId);
}

// 优雅关闭
process.on('SIGINT', async () => {
  await producer.shutdown();
  console.log('👋 Producer 已关闭');
  process.exit(0);
});

start();
```

### 9.3 消费者

```javascript
const { Consumer, MessageModel } = require('rocketmq-client-nodejs');

const consumer = new Consumer('order-consumer-group');
consumer.setNamesrvAddr('localhost:9876');
consumer.setMessageModel(MessageModel.CLUSTERING);  // 集群模式

async function start() {
  // 订阅 Topic + Tag
  await consumer.subscribe('OrderTopic', 'PAID');

  // 注册消息处理器
  consumer.on('message', async (msg) => {
    try {
      const order = JSON.parse(msg.body.toString());
      console.log('📩 收到订单:', order.orderId);

      // 执行业务逻辑
      await processOrder(order);

      // ✅ 消费成功，返回 ACK
      return 'SUCCESS';

    } catch (err) {
      console.error('❌ 消费失败:', err.message);
      // ❌ 返回失败，RocketMQ 会自动重试
      return 'RECONSUME_LATER';
    }
  });

  await consumer.start();
  console.log('✅ Consumer 启动成功');
}

async function processOrder(order) {
  // 模拟业务处理
  await new Promise(resolve => setTimeout(resolve, 100));

  // 模拟 10% 失败率
  if (Math.random() < 0.1) {
    throw new Error('模拟业务异常');
  }
}

process.on('SIGINT', async () => {
  await consumer.shutdown();
  console.log('👋 Consumer 已关闭');
  process.exit(0);
});

start();
```

### 9.4 Node.js 使用建议

如果官方 Node.js SDK 不够成熟，推荐用 **HTTP 桥接模式**：

```
Node.js 应用 → HTTP API → Java 代理服务 → RocketMQ
                          (Spring Boot)
```

这样 Node.js 端只需要调 HTTP 接口，RocketMQ 的复杂逻辑全在 Java 代理层处理。

---

## 十、消息可靠性保障

### 10.1 消息丢失的三个环节

```
Producer → Broker → Consumer
  ①         ②         ③
```

#### ① 发送阶段：Producer → Broker

| 机制 | 说明 | 配置 |
|------|------|------|
| 同步发送 | 等待 Broker 确认才返回，失败可重试 | `producer.send(msg)` |
| 重试机制 | 发送失败自动重试 | `retry-times-when-send-failed=3` |
| 事务消息 | 本地事务 + 消息发送原子化 | `sendMessageInTransaction` |

```java
// 同步发送 + 失败重试（默认3次）
producer.setRetryTimesWhenSendFailed(3);
SendResult result = producer.send(msg);
if (result.getSendStatus() != SendStatus.SEND_OK) {
    // 手动补偿逻辑（如写入数据库后补发）
}
```

#### ② 存储阶段：Broker 内部

| 机制 | 说明 | 风险 |
|------|------|------|
| 同步刷盘 | 消息写入磁盘才返回成功 | 性能低，可靠性最高 |
| 异步刷盘 | 消息写入 PageCache 就返回，后台刷盘 | 性能高，断电可能丢 |
| 同步复制 | Master 等 Slave 确认才返回 | 可靠性高，延迟大 |
| 异步复制 | Master 直接返回，异步同步到 Slave | 可靠性低，延迟小 |

```
可靠性等级（从高到低）：
同步刷盘 + 同步复制 > 异步刷盘 + 同步复制 > 同步刷盘 + 异步复制 > 异步刷盘 + 异步复制

性能等级（从高到低）：
异步刷盘 + 异步复制 > 异步刷盘 + 同步复制 > 同步刷盘 + 异步复制 > 同步刷盘 + 同步复制
```

**推荐配置**：
- 金融场景：同步刷盘 + 同步复制
- 电商场景：异步刷盘 + 同步复制（折中方案）
- 日志场景：异步刷盘 + 异步复制

#### ③ 消费阶段：Broker → Consumer

| 机制 | 说明 |
|------|------|
| 消费确认 | 消费成功返回 `CONSUME_SUCCESS`，失败返回 `RECONSUME_LATER` |
| 重试机制 | 失败自动重试，默认 16 次 |
| 死信队列 | 重试 16 次后仍失败，进入 `%DLQ%` 死信队列 |

```
消息重试间隔（默认）：
第1次: 10s    第5次: 1m     第9次:  6m     第13次: 30m
第2次: 30s    第6次: 2m     第10次: 7m     第14次: 1h
第3次: 1m     第7次: 3m     第11次: 8m     第15次: 2h
第4次: 2m     第8次: 4m     第12次: 10m    第16次: 4h

16次后 → 进入死信队列：%DLQ%consumer-group-name
```

### 10.2 幂等消费（防止重复消费）

RocketMQ 保证**至少一次**送达，但不保证**只有一次**。所以消费者**必须做幂等**。

```java
@Component
public class IdempotentConsumer implements RocketMQListener<Order> {

    @Autowired
    private RedisTemplate redisTemplate;

    @Override
    public void onMessage(Order order) {
        // 用 msgId（全局唯一）作为幂等键
        String msgId = RocketMQMessageConverter.getMsgId(order);

        // Redis SET NX：如果 key 已存在，说明重复消费，直接跳过
        Boolean success = redisTemplate.opsForValue()
            .setIfAbsent("msg:consumed:" + msgId, "1", Duration.ofHours(24));

        if (Boolean.FALSE.equals(success)) {
            System.out.println("⚠️ 重复消息，跳过: " + msgId);
            return;
        }

        // 正常业务处理
        doBusinessLogic(order);
    }
}
```

**幂等的多种实现方式**：

| 方式 | 适用场景 | 实现 |
|------|---------|------|
| 数据库唯一键 | 插入操作 | `INSERT ... ON DUPLICATE KEY UPDATE` |
| Redis SET NX | 通用 | `setIfAbsent(msgId, 1, 24h)` |
| 数据库乐观锁 | 更新操作 | `UPDATE ... SET version=version+1 WHERE version=?` |
| 业务状态机 | 有状态流转 | 已支付的订单不重复扣库存 |

---

## 十一、常见问题与避坑指南

### 11.1 消息丢失

| 可能原因 | 排查方向 | 解决方案 |
|---------|---------|---------|
| Producer 异步发送未等待 | 异步发送无回调 | 改同步发送，或异步加回调 + 失败记录 |
| Broker 宕机且异步刷盘 | 查看 Broker 状态 | 改同步刷盘 / 增加 Slave |
| Consumer 自动 ACK | 消费逻辑抛异常但被吞了 | 返回 `RECONSUME_LATER`，不要自己 try-catch |
| 消费逻辑无幂等 | 重复消费导致数据错乱 | 加幂等机制 |

### 11.2 消息堆积

**原因**：消费速度 < 生产速度。

**排查步骤**：
```bash
# 1. 查看消费进度
mqadmin consumerProgress -g order-consumer-group

# 2. 查看堆积量
mqadmin consumerProgress -g order-consumer-group | grep "Diff"
```

**解决方案**：

| 方案 | 操作 |
|------|------|
| 增加消费者 | 同一个消费组加机器（但不能超过 Queue 数量） |
| 增加 Queue | 扩容 Topic 的 Queue 数量（需 Broker 支持） |
| 优化消费逻辑 | 减少数据库查询、加缓存、批量处理 |
| 消息过期 | 设置消息 TTL，过期的直接丢弃 |
| 紧急处理 | 临时把消息转发到新 Topic，用更多消费者处理 |

### 11.3 顺序消息的坑

```
❌ 错误做法：
  消费组设 CONCURRENTLY（并发消费）但指望消息有序

✅ 正确做法：
  1. Producer 端：同一个 orderId 发到同一个 Queue
  2. Broker 端：同一个 Queue 天然有序
  3. Consumer 端：设置 consumeMode = ORDERLY
  4. 关键：一个 Queue 只被一个消费者线程消费

⚠️ 顺序消费的性能代价：
  - 单 Queue 单线程消费，吞吐量降低
  - 如果一条消息处理慢，后面的消息都会排队
  - 不是所有场景都需要严格有序，评估后慎用
```

### 11.4 事务消息的坑

```
⚠️ 事务消息不适合高吞吐场景：
  - 每条事务消息有额外 2-3 次网络交互
  - 回查机制增加 Broker 和 Producer 的负担
  - 吞吐量比普通消息低一个数量级

⚠️ checkLocalTransaction 必须实现：
  - 如果不实现回查逻辑，消息可能永远处于半消息状态
  - 回查时数据库可能还没写完，注意处理延迟
```

### 11.5 Consumer Group 的坑

```
⚠️ 同一个消费组内：
  - 消费者数 ≤ Queue 数（多了的消费者空闲）
  - 每个 Queue 只被组内一个消费者消费

⚠️ Consumer Group 名称变更：
  - 改了 group 名称 → RocketMQ 认为你是新消费者 → 从最新消息开始消费
  - 如果要从头消费，需要设置 CONSUME_FROM_FIRST_OFFSET

⚠️ 不同环境的 group 名称：
  - 开发环境和生产环境不要用同一个 group 名称
  - 否则会互相抢消息
```

---

## 十二、运维与监控

### 12.1 常用运维命令

```bash
# 查看集群状态
mqadmin clusterList -n localhost:9876

# 查看 Topic 列表
mqadmin topicList -n localhost:9876

# 查看 Topic 详情
mqadmin topicStatus -n localhost:9876 -t OrderTopic

# 查看消费组消费进度
mqadmin consumerProgress -n localhost:9876 -g order-consumer-group

# 查看消费堆积
mqadmin consumerProgress -n localhost:9876 -g order-consumer-group

# 查看 Broker 状态
mqadmin brokerStatus -n localhost:9876 -b broker-a

# 发送测试消息
mqadmin sendMessage -n localhost:9876 -t OrderTopic -p '{"test":true}'

# 重置消费位点（从最新开始消费）
mqadmin resetOffsetByTime -n localhost:9876 -g order-consumer-group -t OrderTopic -s now
```

### 12.2 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| 消息堆积量 | 待消费的消息数量 | > 10000 |
| 消费延迟 | 消息从发送到消费的时间 | > 1s |
| 发送 TPS | 每秒发送消息数 | 和基线对比 |
| 消费 TPS | 每秒消费消息数 | 和基线对比 |
| Broker CPU/Memory | 资源使用 | > 80% |
| 死信队列消息数 | 处理失败的消息 | > 0（需要人工关注） |

### 12.3 告警配置示例（Prometheus + Grafana）

RocketMQ 5.x 原生支持 Prometheus 指标导出：

```yaml
# broker.conf 中添加
enableMetrics = true
metricsPrometheusExporterPort = 5557
metricsPrometheusExporterHost = 0.0.0.0
```

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'rocketmq'
    static_configs:
      - targets: ['broker:5557']
```

**关键告警规则**：
```yaml
# alerting_rules.yml
groups:
  - name: rocketmq
    rules:
      - alert: RocketMQMessageBacklog
        expr: rocketmq_broker_offset - rocketmq_consumer_offset > 10000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "RocketMQ 消息堆积超过 10000"

      - alert: RocketMQDeadLetterQueue
        expr: rocketmq_dlq_messages > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "RocketMQ 死信队列有新消息"
```

---

## 附录 A：RocketMQ vs RabbitMQ vs Kafka 快速选型

```
需要事务消息？
├── 是 → RocketMQ ✅
└── 否 → 继续判断
    ├── 海量日志/流计算（百万 QPS）→ Kafka ✅
    ├── 小团队/快速上手 → RabbitMQ ✅
    └── Java 技术栈/阿里云 → RocketMQ ✅
```

## 附录 B：版本选择建议

| 版本 | 状态 | 建议 |
|------|------|------|
| 4.x | 经典版，广泛使用 | 生产稳定，但新项目不推荐 |
| 5.x | 当前主推 | **新项目首选**，支持 gRPC、Proxy、Prometheus |

---

> **最后总结**：RocketMQ 是阿里双十一验证过的消息中间件，最大优势是**事务消息**和**丰富的消息类型**。学完 RocketMQ，再学 Kafka（偏流处理）和 RabbitMQ（偏通用异步）原理相通。三条 MQ 都掌握后，分布式系统的"通信三剑客"就齐了。
