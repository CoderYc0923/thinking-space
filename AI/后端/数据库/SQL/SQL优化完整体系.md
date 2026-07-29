# SQL 优化完整体系

> 核心理念：**先诊断，再优化。** 盲目加索引和盲目改 SQL 都是大忌。

---

## 一、慢查询：定义与定位

### 1.1 什么是慢查询

慢查询是指**执行时间超过 `long_query_time` 阈值**的 SQL 语句，是数据库性能瓶颈的主要来源。

- 默认阈值：10 秒（生产环境建议 1~2 秒，开发环境建议 0.5~1 秒）
- 记录方式：通过 MySQL 慢查询日志（slow query log）自动捕获
- 影响：长期存在的慢查询会持续占用 CPU/IO 资源，拖慢整个数据库实例

### 1.2 慢查询日志配置

```sql
-- 查看慢查询是否开启
SHOW VARIABLES LIKE 'slow_query_log%';
SHOW VARIABLES LIKE 'long_query_time';  -- 默认 10 秒

-- 临时开启（重启 MySQL 后失效）
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;

-- 永久生效需写入 my.cnf / my.ini
-- [mysqld]
-- slow_query_log = 1
-- slow_query_log_file = /var/lib/mysql/slow.log
-- long_query_time = 1

-- 查看慢查询日志文件位置
SHOW VARIABLES LIKE 'slow_query_log_file';
```

### 1.3 mysqldumpslow 分析工具

```bash
# 按查询时间降序，显示前 10 条
mysqldumpslow -s t -t 10 /var/lib/mysql/slow.log

# 按出现次数降序，显示前 10 条（高频重复查询值得优先关注）
mysqldumpslow -s c -t 10 /var/lib/mysql/slow.log

# 按锁定时间排序
mysqldumpslow -s l -t 10 /var/lib/mysql/slow.log

# 按扫描行数排序
mysqldumpslow -s r -t 10 /var/lib/mysql/slow.log
```

### 1.4 慢查询产生的原因

| 原因 | 说明 |
|------|------|
| **缺少索引** | 全表扫描，type=ALL |
| **索引失效** | 函数操作、类型转换、前置模糊等导致不走索引 |
| **大量数据排序/分组** | Extra 出现 Using filesort / Using temporary |
| **锁等待** | 行锁/表锁竞争导致阻塞 |
| **不合理的 SQL 写法** | SELECT *、深分页、大表驱动小表 |
| **数据量过大** | 单表数据量超过千万级，需考虑分库分表 |

---

## 二、EXPLAIN 执行计划

### 2.1 基本用法

```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 100 AND status = 'paid';
```

### 2.2 关键字段速查

| 字段 | 值 | 含义 | 严重程度 |
|------|-----|------|:---:|
| **type** | `ALL` | 全表扫描，必须优化 | 🔴🔴🔴 |
|  | `index` | 全索引扫描，仍有优化空间 | 🔴🔴 |
|  | `range` | 索引范围扫描（BETWEEN、>、<、IN 等） | 🟡 |
|  | `ref` | 非唯一索引等值查找 | 🟢 |
|  | `eq_ref` | 关联查询时使用唯一索引查找 | 🟢🟢 |
|  | `const` | 主键/唯一索引等值查找，最优 | 🟢🟢🟢 |
| **rows** | 数字 | 优化器预估的扫描行数，越小越好 | — |
| **Extra** | `Using filesort` | 需要额外排序，ORDER BY 字段需优化 | 🔴🔴 |
|  | `Using temporary` | 使用了临时表（常用于 GROUP BY），重点优化 | 🔴🔴🔴 |
|  | `Using index` | 覆盖索引，无需回表查询，**最优** | 🟢🟢🟢 |
|  | `Using where` | 在存储引擎层进行数据过滤 | 🟡 |
|  | `Using index condition` | 索引下推（ICP），存储引擎层先过滤再回表 | 🟢🟢 |
| **key** | 索引名 | 实际使用的索引，NULL 表示未使用任何索引 | — |
| **key_len** | 字节数 | 索引使用的字节数，可判断复合索引用了几个列 | — |
| **filtered** | 百分比 | 经过 WHERE 过滤后剩余行数的百分比 | — |

### 2.3 理解 type 性能阶梯（从优到差）

```
const > eq_ref > ref > range > index > ALL
```

---

## 三、索引优化

### 3.1 复合索引与最左前缀原则

```sql
-- 假设常用查询
SELECT * FROM orders WHERE user_id = ? AND status = ? ORDER BY created_at DESC;

-- ✅ 复合索引设计：等值条件在前，范围/排序在后
CREATE INDEX idx_user_status_time ON orders(user_id, status, created_at);

-- ✅ 走索引（user_id + status）
SELECT * FROM orders WHERE user_id = 100 AND status = 'paid';

-- ✅ 走索引（user_id 在最左列，可利用索引部分前缀）
SELECT * FROM orders WHERE user_id = 100;

-- ❌ 不走索引（跳过了最左列 user_id）
SELECT * FROM orders WHERE status = 'paid';
```

**复合索引设计口诀：** 等值在前，范围在中，排序在末。

### 3.2 索引失效的典型场景

```sql
-- ❌ 对索引列做函数操作
SELECT * FROM users WHERE DATE(create_time) = '2025-01-01';
-- ✅ 改为范围查询
SELECT * FROM users WHERE create_time >= '2025-01-01' AND create_time < '2025-01-02';

-- ❌ 隐式类型转换（phone 是 VARCHAR，用数字查）
SELECT * FROM users WHERE phone = 13800138000;
-- ✅ 加引号
SELECT * FROM users WHERE phone = '13800138000';

-- ❌ 前置模糊查询
SELECT * FROM products WHERE name LIKE '%手机%';
-- ✅ 后置模糊才能走索引
SELECT * FROM products WHERE name LIKE '手机%';
-- ✅ 前置模糊场景使用全文索引
SELECT * FROM products WHERE MATCH(name) AGAINST('手机');

-- ❌ OR 连接非索引列（需要所有列都有索引才能走 index_merge）
SELECT * FROM orders WHERE user_id = 100 OR amount > 500;  -- amount 无索引
-- ✅ 改为 UNION ALL
SELECT * FROM orders WHERE user_id = 100
UNION ALL
SELECT * FROM orders WHERE amount > 500;
```

### 3.3 覆盖索引：避免回表

```sql
-- ❌ SELECT * 需要回表取所有字段
SELECT * FROM orders WHERE user_id = 100 AND status = 'paid';

-- ✅ 只查询索引中已包含的列，Extra 显示 Using index
SELECT user_id, status, created_at FROM orders 
WHERE user_id = 100 AND status = 'paid';
```

**覆盖索引优势：** 数据直接从索引树获取，不需要再回聚簇索引查完整行数据，减少磁盘随机 I/O。

### 3.4 索引下推（ICP, Index Condition Pushdown）

> MySQL 5.6+ 特性。存储引擎在索引遍历过程中，**先判断 WHERE 条件中索引可覆盖的部分**，不符合的直接跳过，减少回表次数。

```sql
-- 假设有复合索引 idx(name, age)
SELECT * FROM users WHERE name LIKE '张%' AND age > 20;
-- 无 ICP：根据 name 查出所有匹配行 → 全部回表 → Server 层过滤 age
-- 有 ICP：索引中同时判断 name 和 age → age 不满足的跳过不回表 → 大幅减少回表
-- Extra 显示 Using index condition
```

---

## 四、SQL 写法优化

### 4.1 SELECT * 的代价

| 问题 | 说明 |
|------|------|
| 无法利用覆盖索引 | 必须回表取全部列 |
| 网络开销增大 | 传输不必要的数据 |
| 表结构耦合 | 加列/删列可能影响调用方 |
| 内存占用 | 结果集缓冲区更大 |

```sql
-- ❌ 坏习惯
SELECT * FROM users WHERE id = 1;

-- ✅ 按需取列
SELECT id, username, avatar FROM users WHERE id = 1;
```

### 4.2 分页优化：深分页问题

```sql
-- ❌ 深分页：offset 过大时，MySQL 需要扫描前 N 行再丢弃
-- 执行过程：扫描 1,000,000 行 → 丢弃前 999,990 行 → 返回最后 10 行
SELECT * FROM orders ORDER BY id LIMIT 1000000, 10;

-- ✅ 方案 A：覆盖索引定位起始 ID（延迟关联）
-- 第一步：只取 ID（覆盖索引，快）
SELECT id FROM orders ORDER BY id LIMIT 1000000, 10;
-- 第二步：根据 ID 批量取数据
SELECT * FROM orders WHERE id IN (上面查到的 id 列表);

-- ✅ 方案 B：游标分页（推荐给前端无限滚动场景）
SELECT * FROM orders WHERE id > 1000000 ORDER BY id LIMIT 10;
```

### 4.3 JOIN 优化：小表驱动大表

```sql
-- ✅ 用小结果集驱动大表（InnoDB Nested-Loop Join）
-- user 表过滤后仅数百条，orders 表数百万条
SELECT o.* FROM users u 
JOIN orders o ON u.id = o.user_id 
WHERE u.level = 'vip';

-- 核心原则：被驱动表（内层表）的关联字段必须有索引
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

### 4.4 IN vs EXISTS

```sql
-- ✅ IN：子查询结果集小时更优（子查询只需执行一次）
SELECT * FROM orders WHERE user_id IN (
    SELECT id FROM users WHERE level = 'vip'
);

-- ✅ EXISTS：外表小、子查询大时更优（逐行检查是否存在，用到外层表的索引）
SELECT * FROM orders o WHERE EXISTS (
    SELECT 1 FROM users u WHERE u.id = o.user_id AND u.level = 'vip'
);
```

### 4.5 COUNT 优化

```sql
-- COUNT(*) 和 COUNT(1)：MySQL 优化器会选最优索引，两者性能相同
-- COUNT(列名)：忽略 NULL 值，除非明确需要，否则用 COUNT(*)

-- 大表行数快速估算（不精确但极快，读取的是统计信息）
SELECT TABLE_ROWS FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'mydb' AND TABLE_NAME = 'orders';
```

### 4.6 批量操作

```sql
-- ❌ 逐条插入：每条都是一次独立事务
INSERT INTO logs (message) VALUES ('msg1');
INSERT INTO logs (message) VALUES ('msg2');
INSERT INTO logs (message) VALUES ('msg3');

-- ✅ 批量插入：单次事务提交
INSERT INTO logs (message) VALUES ('msg1'), ('msg2'), ('msg3');
```

---

## 五、表结构优化

### 5.1 合理选择字段类型

```sql
-- ❌ 用 VARCHAR 存状态
status VARCHAR(20);
-- ✅ 用 TINYINT 或 ENUM
status TINYINT UNSIGNED;  -- 0=待支付, 1=已支付, 2=已取消

-- ❌ IP 用 VARCHAR(15)
ip VARCHAR(15);
-- ✅ 用 INT UNSIGNED + INET_ATON/INET_NTOA 转换（节省空间+加速查找）
ip INT UNSIGNED;

-- 查询时转换
SELECT INET_NTOA(ip) AS ip_str FROM access_log WHERE ip = INET_ATON('192.168.1.1');
```

### 5.2 垂直拆分：大字段分离

```sql
-- 原始表：content 是 TEXT 类型，很少查询但严重拖慢主表扫描
CREATE TABLE articles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200),
    content TEXT,            -- 大字段
    created_at DATETIME
);

-- ✅ 拆分为主表和详情表
CREATE TABLE articles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200),
    created_at DATETIME
);

CREATE TABLE article_contents (
    article_id BIGINT PRIMARY KEY,
    content TEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);

-- 列表查询只查主表，详情页才 JOIN 详情表
SELECT id, title, created_at FROM articles WHERE ...
```

### 5.3 避免过多的索引

```sql
-- 每个索引都需要额外的存储空间和写操作维护成本
-- 经验建议：单表索引数量控制在 5~8 个以内

-- 定期检查无用索引
SELECT * FROM sys.schema_unused_indexes;
```

---

## 六、诊断流程总结

遇到慢查询时，按以下顺序依次排查：

```
1. 开启慢查询日志，定位具体慢 SQL
        ↓
2. EXPLAIN 分析
   ├── type 是不是 ALL/index？ → 缺少索引
   ├── Extra 有没有 Using filesort？ → ORDER BY 未使用索引排序
   ├── Extra 有没有 Using temporary？ → GROUP BY/DISTINCT 导致临时表
   └── rows 是不是远大于实际返回行数？ → 索引过滤性不够
        ↓
3. 检查索引是否失效
   ├── 索引列上有函数操作？
   ├── 存在隐式类型转换？
   └── 前置模糊 LIKE？
        ↓
4. 检查 SQL 写法
   ├── 是否 SELECT *？
   ├── 是否存在深分页？
   ├── JOIN 方向是否小表驱动大表？
   └── 是否有 N+1 查询？
        ↓
5. 检查表结构
   ├── 字段类型是否合理？
   ├── 大字段是否该拆分？
   └── 是否有冗余索引？
        ↓
6. 数据量级评估
   └── 单表超千万级？ → 考虑分库分表、读写分离
```

---

## 七、框架层面的注意点

### 7.1 Java（MyBatis / MyBatis-Plus）

```yaml
# application.yml：开启 SQL 日志
mybatis-plus:
  configuration:
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl
```

```java
// 批量操作：使用 saveBatch 而不是循环 save
List<User> users = new ArrayList<>();
// ... 构建数据
userService.saveBatch(users);  // 底层合并为单条 batch insert

// 避免 N+1：关联查询用 leftJoin 而非循环子查询
List<Order> orders = orderMapper.selectOrdersWithUsers();  // 一次 JOIN 返回
```

### 7.2 Node.js（Sequelize / TypeORM / Prisma）

```javascript
// Sequelize：include 容易产生 N+1，注意使用 separate: true 或改用 JOIN
const orders = await Order.findAll({
  include: [{ model: User }],  // 默认逐条查 User → N+1
});

// ✅ 必要时用原生 SQL 或 JOIN 查询
const [results] = await sequelize.query(`
  SELECT o.*, u.name FROM orders o 
  JOIN users u ON o.user_id = u.id
`);

// Prisma：可以用 fluent API 控制关联查询
const orders = await prisma.order.findMany({
  include: { user: true },
});
// 注意：include 始终是额外查询，必要场景下可用 raw query
```

### 7.3 Docker 环境下的 MySQL

```yaml
# docker-compose.yml：限制数据库容器内存
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root123
    deploy:
      resources:
        limits:
          memory: 512M   # 避免 InnoDB Buffer Pool 太小导致大量磁盘 IO
    volumes:
      - mysql_data:/var/lib/mysql
```

**Buffer Pool 经验值：** 设为可用内存的 50%~70%。可以通过 `SHOW VARIABLES LIKE 'innodb_buffer_pool_size';` 查看当前值。

---

## 八、快速参考卡片

| 场景 | 快速诊断 | 典型修复 |
|------|----------|----------|
| 单表查询极慢 | `EXPLAIN` 看 type 是否为 ALL | 加合适的索引 |
| ORDER BY 慢 | Extra 有 `Using filesort` | 排序列加入索引 |
| GROUP BY 慢 | Extra 有 `Using temporary` | 分组列加索引 |
| 分页越翻越慢 | LIMIT offset 很大 | 游标分页 / 覆盖索引+延迟关联 |
| JOIN 慢 | 被驱动表无索引 | 被驱动表关联列加索引 |
| 索引不生效 | type=ALL 但明明有索引 | 检查函数/类型转换/前置模糊 |
| COUNT 慢 | 大表 COUNT(*) | 用估算值或缓存计数 |

---

> **记住：** SQL 优化不是一劳永逸的。业务数据量在增长，查询模式在变化，定期审查慢查询日志，持续迭代索引设计，才是数据库运维的日常。
