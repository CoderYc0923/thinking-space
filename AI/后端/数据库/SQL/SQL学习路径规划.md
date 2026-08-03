# 第一阶段：SQL 基础语法（7 天，重中之重，DQL 占 80% 工作场景）

## 第 1～3 天：单表查询（所有 SQL 的根基）

### 必学知识点

1. 基础查询：`SELECT * / 字段名 FROM 表名`

2. 别名：字段别名 `AS`、表别名

3. 过滤条件 

   ```
   WHERE
   ```

   ：

   - 运算符：`> < >= <= = !=`
   - 逻辑符：`AND OR NOT`
   - 模糊匹配：`LIKE % _`
   - 范围匹配：`BETWEEN AND`、`IN (值列表)`
   - 空值判断：`IS NULL / IS NOT NULL`（重点坑：不能用 = NULL）

4. 排序 `ORDER BY`：升序 ASC、降序 DESC、多字段排序

5. 分页 `LIMIT offset,size`（MySQL 专属，区分其他数据库分页语法）

### 配套练习

自建学生表、成绩表、商品表，完成单表筛选、模糊搜索、分页需求。

## 第 4～5 天：聚合函数 + 分组统计（数据分析核心）

### 必学知识点

1. 5 大聚合函数：

   ```
   COUNT() SUM() AVG() MAX() MIN()
   ```

   - 区分 `COUNT(*)`、`COUNT(字段)`、`COUNT(DISTINCT 字段)`

2. 分组 `GROUP BY`：按单个 / 多个字段分组

3. 分组过滤 `HAVING`（重点区分 WHERE 和 HAVING：WHERE 过滤原始行，HAVING 过滤分组后结果）

4. 去重 `DISTINCT`

### 实战场景

统计每个班级平均分、商品分类销量、用户月度订单数。

## 第 6～7 天：多表联查（业务开发高频难点）

### 必学知识点

1. 表关系：一对多、多对多（中间关联表）
2. 4 种连接查询（必须手写对比结果）
   - 内连接 `INNER JOIN`：两张表匹配数据
   - 左连接 `LEFT JOIN`：左表全部数据，匹配右表，无匹配填充 NULL
   - 右连接 `RIGHT JOIN`（日常极少用，了解即可）
   - 全连接 `FULL JOIN`（MySQL 不支持，PostgreSQL 支持）
3. 笛卡尔积（重点避坑：不加关联条件会产生海量无效数据）
4. 多表连续 JOIN（3 张、4 张表关联查询）

### 练习场景

用户表 + 订单表 + 商品表三表联查；学生表 + 成绩表 + 班级表统计。

## 阶段一验收标准

随便给一张 / 多张业务表，能快速写出筛选、统计、联表查询语句，分清 WHERE/HAVING、LEFT JOIN 和 INNER JOIN 区别。

------

# 第二阶段：数据库操作 & 结构定义（5 天，DDL+DML，建库建表改结构）

## 第 8～9 天：DML 数据操作语言（增删改）

1. 新增 `INSERT`：单行插入、批量插入、指定字段插入

2. 修改 

   ```
   UPDATE
   ```

   ：单字段更新、多字段更新

   - 致命坑：不加 WHERE 会更新整张表，生产禁止裸 UPDATE

3. 删除 

   ```
   DELETE
   ```

   ：按条件删除数据

   - 区分 `DELETE` 和 `TRUNCATE`（DELETE 可回滚，TRUNCATE 清空表、重置自增、速度更快）

## 第 10～11 天：DDL 库、表、字段结构管理

1. 库操作：`CREATE DATABASE` / `DROP DATABASE` / `ALTER DATABASE`

2. 数据类型（MySQL 重点）

   - 数值：int、bigint、decimal（小数必用，避免 float 精度丢失）
   - 字符串：varchar、char、text
   - 时间：date、datetime、timestamp（时区坑）

3. 表操作

   - 建表 

     ```
     CREATE TABLE
     ```

     ，约束同步学习

     - 主键 `PRIMARY KEY`、自增 `AUTO_INCREMENT`
     - 唯一约束 `UNIQUE`、非空 `NOT NULL`、默认值 `DEFAULT`
     - 外键约束 `FOREIGN KEY`（企业极少用，了解原理即可）

   - 修改表 `ALTER TABLE`：新增字段、删除字段、修改字段类型、添加 / 删除索引

   - 删除表 `DROP TABLE`

## 第 12 天：TCL 事务控制（生产核心，保证数据一致性）

1. 事务四大特性 ACID
2. 事务语法：`BEGIN / START TRANSACTION`、`COMMIT`提交、`ROLLBACK`回滚
3. 事务隔离级别（读未提交、读已提交、可重复读、串行化，MySQL 默认可重复读）
4. 脏读、不可重复读、幻读概念

### 阶段二验收

能从零创建业务表，合理选择字段类型与约束；掌握增删改规范，会用事务解决转账、库存扣减场景。

------

# 第三阶段：SQL 进阶难点（10 天，面试高频、复杂业务必备）

## 第 13～14 天：子查询 & 相关子查询

1. 标量子查询、列子查询、表子查询

2. 运算符：

   ```
   IN / EXISTS / NOT EXISTS / ANY / ALL
   ```

   - 重点：EXISTS 性能远高于 IN（数据量大场景）

3. 子查询嵌套、子查询放在 SELECT/FROM/WHERE/HAVING 不同位置

4. 派生表（FROM 后套子查询，必须加别名）

## 第 15～16 天：公用表表达式 CTE、窗口函数（数据分析天花板）

1. CTE：`WITH AS` 简化复杂嵌套子查询，递归 CTE（树形结构：部门层级、分类树）
2. 窗口函数（重点，面试必考）
   - 基础窗口函数：`ROW_NUMBER() RANK() DENSE_RANK()` 分组排名
   - 聚合窗口函数：`SUM() OVER() AVG() OVER()` 分组累加、滑动窗口
   - 语法：`OVER(PARTITION BY 分组字段 ORDER BY 排序字段)`

## 第 17～18 天：索引基础 + SQL 性能优化入门

1. 索引分类：主键索引、唯一索引、普通索引、联合索引
2. 联合索引最左匹配原则（面试高频考点）
3. 索引失效场景（避坑核心）
   - 字段隐式转换、模糊查询 % 前置、or 无索引、not in !=
4. 执行计划 `EXPLAIN` 使用：看懂 type、key、rows、Extra 字段，定位慢查询

## 第 19～20 天：DCL 权限管理 + 视图、存储过程（了解即可）

1. DCL：创建用户 `CREATE USER`、授权 `GRANT`、回收权限 `REVOKE`、修改密码
2. 视图 `VIEW`：简化复杂查询，优缺点
3. 存储过程、函数：封装 SQL 逻辑（现代后端开发很少用，看懂语法即可）

### 阶段三验收

独立完成复杂报表（多维度排名、累计求和）；会用 EXPLAIN 分析慢 SQL，说出索引失效场景；能写递归 CTE 处理树形数据。

------

# MySQL 进阶路线【方案 A】完整规划

承接前面 20 天 SQL 基础，接下来进入 **MySQL 运维 + 底层原理 + 工程实战（后端面试重中之重）**

整体分为 5 个阶段，我按天拆分，你可以循序渐进学习：

> 前置基础：SQL、索引、事务隔离级别、锁机制、Explain 调优你已经学完
>
> 环境：MySQL 8.0 InnoDB

## 整体学习大纲预览

第 21～22 天：慢查询日志 + 全方位 SQL 调优实战（工程落地）

第 23～24 天：Binlog 详细原理、三大格式、数据恢复、Canal 同步

第 25～26 天：主从复制原理、搭建、延迟问题、读写分离

第 27～28 天：分库分表（Sharding-JDBC 核心）、分片策略、痛点

第 29～30 天：InnoDB 底层深度：Buffer Pool、Undo Log、Redo Log、崩溃恢复

第 31 天：MySQL 常见线上故障汇总 + 面试高频真题复盘

# 第 21～22 天：慢查询日志 + 线上 SQL 深度调优实战

## 第 21 天：慢查询日志、性能监控工具

### 1. 慢查询核心参数

ini







```
slow_query_log = ON                # 开启慢日志
slow_query_log_file = slow.log     # 日志文件路径
long_query_time = 1                # 阈值，超过1s判定为慢SQL
log_queries_not_using_indexes = ON # 记录没有走索引的SQL
```

在线动态开启（无需重启数据库）

sql







```
SET GLOBAL slow_query_log = 1;
SET GLOBAL long_query_time = 1;
```

> 注意：global 参数新开会话生效，当前会话不生效。

### 2. 日志分析工具

1. **mysqldumpslow**（MySQL 自带）

bash







```
# 统计耗时最多的10条SQL
mysqldumpslow -s t -t 10 slow.log
```

参数：

- -s t：按执行时间排序
- -s c：按执行次数排序

1. 第三方：pt-query-digest（Percona Toolkit，生产主流）

### 3. Performance Schema / show profile

定位 SQL 内部耗时，查看 CPU、IO、锁等待

sql







```
SET profiling = 1;
-- 执行你的SQL
SHOW PROFILE;
```

### 4. Show Processlist

实时查看连接、正在执行 SQL、锁阻塞

sql







```
SHOW FULL PROCESSLIST;
```

重点字段：`STATE`

`Waiting for table metadata lock` 元数据锁阻塞

`Waiting for row lock` 等待行锁

## 第 22 天：线上综合调优实战（结合前面 Explain、索引）

### 1. 元数据锁 MDL（高频线上坑）

✅核心知识点：

MySQL5.7/8.0，**DML/SELECT 也会申请 MDL 读锁；DDL 申请 MDL 写锁**

MDL 锁：事务结束才释放，不是语句结束！

经典事故场景：

sql







```
#会话1：开启事务执行一条select，不提交（持有MDL读锁）
BEGIN;
SELECT * FROM student WHERE id=1;

#会话2：执行ALTER TABLE 阻塞！等待MDL写锁

#会话3：后续所有查询本表SQL全部排队阻塞 → 雪崩
```

解决方案：

\1. 业务低峰执行 DDL

\2. 使用 pt-online-schema-change /gh-ost **在线无锁改表**

### 2. 大事务风险

危害：

- 锁持有时间变长，容易死锁、阻塞

- Undo 日志膨胀

- Binlog 过大，主从延迟飙升

  

  优化原则：事务尽量小，避免一次性大批量更新

### 3. 批量 SQL 优化

❌循环逐条 insert（Java 循环 insert）

✅改成批量 INSERT INTO VALUES (),(),();

✅大量数据使用 LOAD DATA

### 4. IN 查询优化

IN 内元素过多（>1000）性能下滑，拆分多次查询

避免 NOT IN（容易 NULL 引发诡异结果，优先 NOT EXISTS）

### 配套作业

1. 写出开启慢查询的参数，mysqldumpslow 常用命令
2. 解释 MDL 锁引发雪崩的场景，如何规避？
3. 什么情况下不建议使用`SELECT *`，写出两点理由

------

# 第 23～24 天：Binlog 原理、数据恢复、Canal 同步

## 第 23 天 Binlog 基础

### 1. Binlog 是什么

二进制日志，**Server 层日志**，与存储引擎无关；

记录所有 DML/DDL 修改数据的操作；

两大作用：

1. 主从复制
2. 数据误删恢复

> 区分：Redo Log/Undo Log 是 InnoDB 引擎层日志

### 2. Binlog 三种格式（面试必考）

1. STATEMENT

   ：记录原始 SQL 语句

   

   缺点：函数、随机语句，从库执行结果和主库不一致，

   不推荐

2. ROW（行模式，线上默认推荐）

   

   记录变更前后每行数据，精准；缺点：日志体积大

3. **MIXED**：混合模式，自动选择 statement/row

ini







```
binlog_format = ROW
```

### 3. Binlog 基础操作

sql







```
SHOW BINARY LOGS; #查看binlog文件
SHOW BINLOG EVENTS IN 'binlog.000101';
```

命令行工具解析 binlog

bash







```
mysqlbinlog binlog.000101
```

## 第 24 天：数据恢复 + Canal 原理

### 1. 误删数据恢复流程

前提：开启 binlog

\1. 找到备份基线

\2. 通过 mysqlbinlog 抓取时间段内 binlog

\3. 重放日志恢复数据

> 生产规范：定期全量备份 + binlog，实现任意时间点恢复 (PITR)

### 2. Canal 核心原理

Canal 模拟 MySQL 从库，伪装 slave，接收主库推送的 Binlog；

解析 Binlog，把数据变更投递到 MQ (RocketMQ/Kafka)。

典型场景：

- MySQL 数据同步 Elasticsearch
- 缓存更新（Redis）
- 异地多库同步
- 业务数据变更审计

### 思考题

1. Binlog 和 Redo Log 的区别？
2. ROW 格式 Binlog 相比 STATEMENT 优势是什么？

------

# 第 25～26 天：主从复制、读写分离

## 第 25 天：主从复制原理

### 三线程模型

1. Master：Binlog Dump 线程
2. Slave：IO 线程（拉取 binlog 写入 relay log）
3. Slave：SQL 线程（新版本支持并行复制，执行 relay log）

复制拓扑：

一主一从、一主多从、级联复制

### 同步模式

1. 异步复制（默认）：主写完直接返回，不等从库
2. 半同步复制：主至少等待一个从库接收 Binlog，提升数据安全

## 第 26 天：主从延迟、读写分离

### 1. 主从延迟常见原因

- 从库单线程执行 SQL（老版本）
- 大事务、大批量 DML
- 从库硬件性能弱于主库
- 网络延迟

### 2. 读写分离方案

- 应用层：Sharding-JDBC

- 中间件：MyCat、ProxySQL

  

  ⚠️经典坑：读从库读到旧数据（主从延迟）

  

  解决方案：

1. 重要一致性查询强制走主库
2. 业务容忍短暂延迟

# 第 27～28 天：分库分表（互联网必备）

## 第 27 天 分片基础

什么时候需要分表？

单表数据量 **千万级别** 开始考虑（无绝对标准，取决于查询压力）

### 两种拆分方式

1. **垂直拆分**：按字段拆分（大字段单独一张表）
2. **水平拆分**：按行拆分，多张表结构一致

### 分片策略

- 范围分片：id 1~100000 表 1，100001~200000 表 2

- Hash 分片：user_id % 分片数量（最常用）

  

  优缺点对比

## 第 28 天 分库分表痛点（面试高频）

1. **跨分片 JOIN 极其麻烦，尽量避免**
2. 分布式事务难题
3. 分页、排序、聚合复杂
4. 全局唯一 ID 方案（雪花算法、号段模式）

主流中间件：**Sharding-JDBC（首选，客户端）**、MyCat

# 第 29～30 天 InnoDB 底层三大日志深度剖析（面试压轴）

## 核心三件套：Redo Log、Undo Log、Buffer Pool

1. **Buffer Pool**：内存缓存页，减少磁盘 IO；LRU 淘汰策略

2. Redo Log（重做日志）

   

   崩溃恢复核心；先写日志，后刷盘 (WAL 机制)

3. Undo Log（回滚日志）

   

   事务回滚、MVCC 多版本快照依赖

### MVCC 完整原理串联

隔离级别、Read View、事务 ID、undo 版本链，

解释：RC 和 RR 下 MVCC 实现差异

# 第 31 天：线上故障汇总 + 全套 MySQL 面试真题复盘

整理高频线上问题：

- 死锁排查

- 大量锁等待

- 主从延迟突增

- 数据库 CPU 飙升

- IO 打满

- 分页深度慢查询

  

  配套大厂面试题 + 标准答案

# 第四阶段：实战项目 + 面试查漏补缺（15 天，学完直接落地工作）

## 模块 1：小型业务数据库项目（10 天，分 3 套场景）

### 项目 1：电商订单库（后端最通用）

表设计：用户表、商品分类、商品表、购物车、订单主表、订单详情、支付记录

需求：

1. 多条件商品筛选、分页、销量排序
2. 统计每个商品月度销售额、top10 热销商品
3. 联表查询用户完整订单信息
4. 库存扣减事务实现

### 项目 2：学生成绩管理系统

需求：班级平均分排名、学生总分排名、挂科统计、树形年级班级结构（递归 CTE）

### 项目 3：后台权限系统

多对多关系：用户 - 角色 - 菜单，关联查询权限数据

## 模块 2：题库刷题（5 天）

1. LeetCode 数据库题库（简单→中等，刷 30 题，覆盖所有语法考点）
2. 牛客 SQL 专项题库（贴合国内后端面试）

## 模块 3：高频面试考点复盘（整理成笔记）

1. 联表查询区别、WHERE/HAVING、IN/EXISTS
2. 窗口函数三种排名函数差异
3. 索引、最左前缀、索引失效、EXPLAIN
4. 事务 ACID、四大隔离级别、脏读幻读
5. DELETE/TRUNCATE/DROP 区别
6. 多对多表设计、树形数据递归查询

------

# 配套学习资源推荐

## 1. 文档（权威免费）

1. MySQL 8.0 官方文档
2. 《SQL 必知必会》（入门首选，通俗易懂）
3. 《高性能 MySQL》（优化进阶，工作必备）

## 2. 视频

1. B 站 MySQL 零基础全套教程
2. 尚硅谷 / 黑马 SQL 实战课程

## 3. 练习平台

1. 在线：SQLZoo、菜鸟 SQL
2. 刷题：LeetCode Database、牛客网 SQL 专项

# 学习避坑核心提醒

1. 不要死记语法，每一条 SQL 必须自己动手执行，观察结果差异
2. 优先掌握 DQL 查询，工作中 90% 场景都是写查询，增删改相对简单
3. 索引、事务、窗口函数是区分初级 / 中级开发的核心，务必吃透
4. 禁止裸写 UPDATE/DELETE 不加 WHERE，养成先 SELECT 验证条件的习惯
5. 学完基础立刻做项目，单纯背语法极易遗忘