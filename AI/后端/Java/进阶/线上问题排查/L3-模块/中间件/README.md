# L3：中间件与下游（仅服务器排查版）

> 前提：**阿里云 ECS 上跑应用**，没有 ARMS / 依赖大盘 / 中间件控制台可用。  
> 手段就这些：SSH 登机器 → **应用日志 + jstack + 本机连依赖的命令行（redis-cli / curl / ss）**。  
> 典型用户表象：U2/U3/U4（超时、变慢、大量失败）；CPU 往往不高，线程被依赖拖死。

---

## 1. 何时进入本模块

登服务器后若出现：

- 日志大量：`timeout`、`RedisConnectionFailure`、`MQ` 发送/消费失败、Feign/OkHttp 报错  
- `jstack` 堵在：Jedis/Lettuce、RocketMQ/Kafka 客户端、OkHttp/HttpClient/Feign  
- 本机探活还行，但业务接口大面积超时  

先别 dump 堆；按下面顺序在**应用机器上**查。

---

## 2. 服务器上的固定三板斧（每次都做）

假设已 SSH 到出问题的那台 ECS。

### 2.1 日志：先确认「依赖是谁、什么错」

```bash
# 日志路径按你们实际改
cd /path/to/logs   # 或 journalctl -u 你的服务

# 超时 / Redis / MQ / HTTP 下游
grep -E 'timeout|timed out|Redis|Jedis|Lettuce|RocketMQ|Kafka|Feign|OkHttp|UnknownHost|Connection refused' app.log \
  | tail -80

# 粗看哪类异常最多
grep -oE '[A-Za-z0-9_.]+(Exception|Error)' app.log | sort | uniq -c | sort -rn | head -20
```

记下：时间点、异常类名、目标 host:port（日志里常有）。

### 2.2 jstack：先看状态，再瞄几眼栈（短版）

中间件拖死时，多数线程会停在 **WAITING / TIMED_WAITING**（少数在 `socketRead` 上显示 RUNNABLE）。不必一上来搜一堆关键字。

```bash
PID=$(pgrep -f '你的jar或主类' | head -1)
jstack "$PID" > /tmp/jstack.txt

# ① 状态分布（一眼看是不是「大家都在等」）
grep 'java.lang.Thread.State' /tmp/jstack.txt | sort | uniq -c | sort -rn

# ② 抽几段 WAITING / TIMED_WAITING 的栈（看卡在谁家里）
grep -A 20 'TIMED_WAITING\|WAITING' /tmp/jstack.txt | head -80
```

在抽出来的栈里扫一眼关键字即可：

| 栈里带什么 | 方向 |
|------------|------|
| `lettuce` / `jedis` / `redis` | Redis |
| `rocketmq` / `kafka` | MQ |
| `okhttp` / `feign` / `httpclient` / `socketRead` | 下游 HTTP |
| `HikariPool` / `getConnection` | 转去查数据库模块 |

不确定时再精确搜一行：

```bash
grep -nE 'lettuce|jedis|feign|okhttp|rocketmq|getConnection' /tmp/jstack.txt | head
```

隔 15s 再 `jstack` 一次，若同一批线程还在同一栈 → 真卡住，不是路过。

### 2.3 本机到依赖通不通（网络层）

从**应用 ECS**测（安全组/DNS 问题很常见）：

```bash
# 配置里抄出 host、port（application.yml / Nacos 本地缓存 / env）
grep -rE 'redis|rocketmq|feign|url' /path/to/config --include='*.yml' --include='*.properties' | head

# TCP 通不通（有 nc 或 bash）
nc -vz <redis-host> 6379
nc -vz <下游host> <port>
# 或
timeout 3 bash -c 'echo > /dev/tcp/<host>/<port>' && echo OK || echo FAIL

# DNS
getent hosts <域名>
ping -c 2 <host>   # 仅参考；有的环境禁 ICMP
```

通不了 → 先查安全组、白名单、域名、依赖是否挂，再查业务代码。

---

## 3. Redis（从 ECS 用 redis-cli）

机器上若无客户端，可临时装或用你们镜像自带的：

```bash
# 连接（密码、TLS 按实际；阿里云 Redis 常要密码且只允许 VPC 内访问）
redis-cli -h <host> -p 6379 -a '<password>' --no-auth-warning

# 进 cli 后：
PING
INFO clients          # 连接数是否异常高
INFO commandstats     # 哪类命令多
SLOWLOG GET 20        # 慢命令（防 KEYS、重 Lua）
INFO memory
```

大 key（谨慎，别在高峰对全库乱扫）：

```bash
# 对已知可疑 key
MEMORY USAGE <key名>
TYPE <key名>
STRLEN <key名>          # string
HLEN / LLEN / SCARD / ZCARD <key名>
```

和 jstack 对照：

| 现象 | 含义 |
|------|------|
| 栈在 lettuce/jedis + SLOWLOG 有大命令 | Redis 侧慢 |
| 栈在借连接 / 池相关 + INFO clients 很高 | 客户端连接/池问题 |
| nc 都不通 | 网络/白名单，不是业务慢 |

连接池（应用侧）：看日志是否有 pool exhausted；配置里 `max-active` / lettuce pool；代码是否用完归还（Lettuce 多数自动，Jedis 池化要还）。

---

## 4. MQ（无控制台时怎么在服务器上判断）

没有堆积曲线时，只能靠**日志 + 消费线程栈**：

```bash
# 发送失败
grep -E 'send.*fail|SendResult|TIMEOUT|System busy' app.log | tail -50

# 消费侧：一直在处理、报错、重试
grep -E 'Consume|message.*fail|Reconsume|ack' app.log | tail -50

jstack "$PID" > /tmp/jstack-mq.txt
grep -nE 'RocketMQ|KafkaConsumer|MessageListener|consumeMessage' /tmp/jstack-mq.txt | head -40
```

| 服务器上看到的 | 可能原因 |
|----------------|----------|
| 发送日志超时 + nc broker 端口不通 | 网络 / broker 地址错 |
| 消费线程长时间 RUNNABLE/WAITING 在业务代码 | 消费逻辑慢或下游又卡了（看该线程完整栈） |
| 疯狂重试日志 | 消费失败未处理好，可能拖垮自己 |

堆积数量若完全没处看：至少用日志里的「延迟处理、重试次数」和线程是否被消费占满来定性；有权限再让有控制台的人补一眼。

---

## 5. 下游 HTTP / RPC（纯服务器）

```bash
# 1）日志里的目标 URL / 错误
grep -E 'feign|http://|https://|SocketTimeout|ConnectTimeout|504|502' app.log | tail -40

# 2）jstack 确认堵在读
grep -nE 'okhttp|httpclient|feign|socketRead' /tmp/jstack-*.txt | head

# 3）从本机模拟调用（把日志里的 URL 换上）
curl -m 3 -v 'http://<下游host>:<port>/path'
# -m 3 = 最多等 3 秒；卡住或很慢 → 下游或网络问题
```

超时配置在**本机配置文件**核对（无运维平台也要翻文件）：

```bash
grep -rE 'timeout|readTimeout|connectTimeout|ribbon|feign' /path/to/config \
  --include='*.yml' --include='*.properties' | head -40
```

| 情况 | 处理方向 |
|------|----------|
| curl 就慢/超时 | 下游或网络 |
| curl 快，应用仍超时 | 看线程是否打满、重试是否放大、配置是否没生效 |
| 无超时或超时很长 | 改短 connect/read timeout，避免线程被拖死 |

重试风暴（只在服务器上也能看）：

```bash
# 同一错误短时间暴增
grep 'SocketTimeout' app.log | awk '{print $1,$2}' | uniq -c | tail
```

---

## 6. 注册 / 配置中心（Nacos 等）

仍在应用 ECS 上：

```bash
# 启动失败 / 连不上
grep -E 'Nacos|config.*fail|Connection refused' app.log | tail -40

nc -vz <nacos-host> 8848

# 本地是否还有旧配置缓存（路径按组件改）
ls -la ~/.nacos/ /tmp/nacos/ 2>/dev/null
```

错误配置：看本机当前生效的 yml/env，以及最近是否重启拉过新配置；无控制台历史时，只能对比发布记录/Git。

---

## 7. 推荐顺序（无大盘版）

```text
1. 应用日志：timeout / Redis / MQ / Feign 异常 TOP（比 dump 优先）
2. jstack ×2：堵在 redis / mq / http 哪一类
3. 本机 nc/curl：到依赖 host:port 通不通、慢不慢
4. Redis：redis-cli PING / SLOWLOG / INFO（若通）
5. 翻本机配置：超时、重试、池大小
6. 仍像内存问题再考虑 jstat / dump（多数中间件超时用不上 dump）
```

---

## 8. 和「卡死」的关系

```text
下游无超时 → 本机线程占满 → CPU 低 → 用户侧像卡死
  → 服务器证据：jstack 在 socketRead/feign，curl 下游慢或配置超时过大

Redis 慢/大 key → 尖刺超时
  → 服务器证据：栈在 lettuce + SLOWLOG / MEMORY USAGE

MQ 消费卡住 → 消费延迟（HTTP 是否被拖看线程是否共享池）
  → 服务器证据：消费线程栈 + 消费失败/重试日志
```

---

## 9. 和 L4 的关系

本页默认：**一台阿里云 ECS + SSH**。  
多机时：先对「出错多的那台」做上述步骤（用 `jps`/端口/日志时间对齐选机）。  
详见 [L4 部署环境差异](../../L4-环境/部署环境差异.md)（可忽略其中的 ARMS/大盘段落，只保留 SSH 部分）。
