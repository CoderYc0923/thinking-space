# L3：中间件与下游

> Redis / MQ / HTTP·RPC 下游 / 注册配置中心。  
> 典型：超时、错误率飙、**CPU 不高但线程被拖死**。

---

## 1. 何时进入本模块

常见组合：用户侧 **U2/U3/U4** + 信号 **S-DEP（Redis/MQ/下游）/ S-THREAD（客户端栈）/ S-ERR（timeout）**。

- 依赖大盘红：Redis / MQ / 下游服务  
- `jstack` 堵在：Jedis/Lettuce、Kafka/RocketMQ Consumer、Feign/OkHttp/HttpClient  
- 日志：`timeout`、`CircuitBreaker`、大量重试  
- 探活还行，但业务接口全超时（依赖挂了）  

---

## 2. 子问题手册

### 2.1 Redis / 缓存

| 子问题 | 说明 | 思路 | 关键现象 | 命令 / 入口 |
|--------|------|------|----------|-------------|
| 慢查询/阻塞 | KEYS、重 Lua、错误命令 | Redis 慢日志 | 应用 Redis RT 尖刺 | `SLOWLOG GET 20`；云 Redis 慢日志 |
| 大 key | 巨 Value / 大 Hash | 扫描大 key | 网络与反序列化尖刺 | 云「大 key 分析」；`MEMORY USAGE` |
| 连接池耗尽 | 客户端池打满 | 同 DB 池思路 | 等 Redis 连接 | 池指标；jstack |
| 击穿/穿透/雪崩 | 瞬时打到 DB | 命中率 + DB QPS | DB 突然被打满 | 缓存命中率；空值缓存；互斥重建；TTL 打散 |
| 持久化抖动 | AOF/RDB fork | 对齐 Redis 指标 | 周期性延迟 | 云监控 CPU/网络 |

```bash
redis-cli -h <host> SLOWLOG GET 20
redis-cli INFO clients
redis-cli INFO commandstats
```

### 2.2 MQ

| 子问题 | 说明 | 思路 | 关键现象 | 命令 / 入口 |
|--------|------|------|----------|-------------|
| 消费阻塞 | 处理慢/死等、ack 不住 | 消费者 jstack | 堆积涨 | 控制台堆积；`jstack` |
| 发送失败 | broker/网络/限流 | 发送错误率 | 生产失败 | Broker 监控 |
| 堆积反压 | 消费能力不足 | 扩容/降级/丢弃策略 | 堆积持续升 | 堆积曲线 + 消费 RT |

### 2.3 下游 HTTP / RPC

| 子问题 | 说明 | 思路 | 关键现象 | 命令 / 入口 |
|--------|------|------|----------|-------------|
| 下游慢/挂 | 依赖故障 | 依赖 RT、可用性 | 本服务线程堵在读 | jstack 搜 HttpClient/Feign；下游大盘 |
| 超时不合理 | 无超时或过长 | 核对客户端超时 | 线程缓慢占满 | 配置审计 |
| 重试风暴 | 失败狂重试 | 限流 + 退避 | 错误与出站 QPS 齐飞 | 重试次数指标；熔断是否打开 |
| 雪崩 | 依赖全挂拖死本机 | 熔断/降级/隔离舱 | 大面积超时 | 熔断器状态 |

```bash
# 线程栈快速搜下游
grep -nE 'okhttp|httpclient|feign|netty.channel|WebClient' jstack.txt | head
```

### 2.4 注册 / 配置中心

| 子问题 | 现象 | 思路 |
|--------|------|------|
| 连不上 Nacos/ZK 等 | 启动失败或误摘流 | 查网络/鉴权/地址；对齐变更 |
| 错误配置推送 | 推送后错误率台阶 | 配置中心历史回滚 |

---

## 3. 推荐顺序

```text
1. 依赖大盘是否红（比先 dump 有用）
2. 本服务：超时异常 TOP、jstack 堵在哪个客户端
3. 中间件控制台：慢日志 / 堆积 / 连接数 / 大 key
4. 核对：超时、重试、熔断、连接池
5. 临时：降级、断重试、扩容；根因在依赖或调用方式
```

---

## 4. 和「卡死」的关系

```text
下游无超时 → 本机线程占满 → CPU 低 → 像应用卡死
Redis 大 key → 偶发尖刺 → 像网络抖
MQ 消费卡住 → 堆积 → 业务延迟（不一定拖垮 HTTP 池，看架构）
```

---

## 5. 环境

| 环境 | 入口 |
|------|------|
| 自建 Redis/Kafka | CLI + Exporter |
| 阿里云 Redis / RocketMQ | 云监控、慢日志、堆积 |
| K8s | 除中间件本身外，查 CoreDNS / NetworkPolicy 是否导致「假超时」 |

详见 [L4](../../L4-环境/部署环境差异.md)。
