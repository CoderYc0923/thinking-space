# L3：数据库

> 能解释大量「假 JVM 卡死」：慢 SQL、锁、连接池。  
> 应用侧借出不还 与 库侧连接打满，要一起看。

---

## 1. 何时进入本模块

常见组合：用户侧 **U2/U3/U4** + 信号 **S-DEP（DB）/ S-THREAD（getConnection）/ S-ERR（Connection is not available）**。

- `jstack` 大量：`HikariPool.getConnection` / Druid / `MysqlIO` / `socketRead`  
- 日志：`Connection is not available, request timed out after …ms`  
- 监控：DB RT 高、活跃连接≈最大值、慢查询 QPS 升  
- 「昨天快今天慢」且无发版 → 执行计划/数据量变化  

usecases 概念模拟：`ConnectionPoolExhaustion` → `jvm排查/diagnostics/pool-resource-jvm.md`

---

## 2. 子问题手册

| 子问题 | 说明 | 思路 | 关键现象 | 命令 / 入口 |
|--------|------|------|----------|-------------|
| 连接池打满 | 连接被占光，新请求等待 | 池指标 + jstack + DB 会话 | active=max，pending>0；接口超时 | 应用：Hikari `Active/Pending/Total`；`jstack`；库：会话列表 |
| 连接泄漏 | 借出未归还 | 开启泄漏检测；查未 close 路径 | 池缓慢耗尽，重启暂缓 | Hikari `leakDetectionThreshold`；代码 try-with-resources |
| 慢 SQL | 缺索引/失效/大结果 | 慢日志 + EXPLAIN | DB RT 高；应用 CPU 未必高 | 慢查询日志；`EXPLAIN`；APM SQL |
| 行锁/表锁等待 | 长事务、热点行 | 查谁持锁、等锁 | 线程在 socketRead；库 lock wait | 见下方 MySQL 段 |
| DB 死锁 | InnoDB deadlock | 看死锁日志 | 事务回滚异常 | `SHOW ENGINE INNODB STATUS\G` 或 RDS 死锁分析 |
| 长事务 | 事务内调 RPC/睡太久 | 缩事务 | 连接持有时间长 | `innodb_trx`；APM |
| 大结果集 | 无分页打爆应用内存 | 分页/流式 | 可叠应用 OOM/GC | SQL + 接口 |
| 库不可用 | 挂了、连接上限、磁盘满、切换 | 云监控/DBA | 连不上、错误暴涨 | RDS 控制台；`max_connections`；磁盘 |
| 执行计划变差 | 统计信息/数据倾斜 | 对比计划 | 同 SQL 突然慢 | `EXPLAIN`；优化器统计 |
| 主从延迟 | 读从读到旧数据 | 延迟监控 | 业务重试/补偿 | 主从延迟指标 |

---

## 3. 应用侧：确认「堵在等连接」

```bash
# 线程栈
grep -nE 'HikariPool|getConnection|DruidDataSource|HikariBaseProxy' jstack.txt | head -40

# 状态直方图：大量 WAITING 很常见
grep 'Thread.State' jstack.txt | sort | uniq -c | sort -rn
```

Hikari 常见日志：

```text
HikariPool-1 - Connection is not available, request timed out after 30000ms
HikariPool-1 - Pool stats (total=10, active=10, idle=0, waiting=25)
```

Spring 配置排查点（示例）：

```properties
spring.datasource.hikari.maximum-pool-size=10
spring.datasource.hikari.connection-timeout=30000
spring.datasource.hikari.leak-detection-threshold=60000
```

---

## 4. MySQL / RDS：谁占着连接、谁在等锁

```sql
-- 当前会话（谁在跑什么）
SHOW FULL PROCESSLIST;

-- 更干净的活跃事务（MySQL 5.7+）
SELECT * FROM information_schema.innodb_trx\G

-- 锁等待（8.0 常用 performance_schema）
SELECT * FROM sys.innodb_lock_waits\G
-- 或查 performance_schema.data_locks / data_lock_waits（版本差异大，按环境选）

-- 死锁最近一次信息
SHOW ENGINE INNODB STATUS\G
```

慢 SQL：

```bash
# 自建：慢日志文件（路径看 slow_query_log_file）
# 阿里云 RDS：控制台 → 慢日志 / SQL 洞察 / 自治服务
```

```sql
EXPLAIN SELECT ...;   -- 看 type、key、rows、Extra
```

临时止血（需权限与规范）：

- 杀掉明显失控的长查询（`KILL <id>`）  
- 短时扩 `maximum-pool-size`（治标，根因仍是慢/泄漏）  

---

## 5. 推荐顺序

```text
1. 应用连接池指标（active / idle / pending / timeout）
2. jstack：堵在 getConnection，还是已拿到连接在等 DB？
3. DB：PROCESSLIST / 慢日志 / 锁等待
4. 定凶：慢 SQL、持锁事务、还是应用泄漏
5. 修根因；扩容只作缓冲
```

---

## 6. 因果链（贴在工位）

```text
慢 SQL / 行锁 → 连接占满 → getConnection 等待 → 线程池打满 → 大面积超时 → 重试雪崩
```

---

## 7. 环境

| 环境 | 怎么查 |
|------|--------|
| 自建 MySQL | SSH + mysql 客户端 + 慢日志文件 |
| 阿里云 RDS | 控制台慢日志、会话管理、锁分析 |
| K8s 应用 + RDS | Pod 打 jstack；库在控制台；时间线对齐 |
| 只有应用权限 | APM SQL + 池指标 → 再找 DBA |

详见 [L4](../../L4-环境/部署环境差异.md)。
