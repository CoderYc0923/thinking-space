# Linux 系统下 MySQL 常用命令速查

> 适用环境：Ubuntu/Debian/CentOS + 宝塔面板
> 提示：带 `$` 的是 Shell 命令，带 `mysql>` 的是数据库内命令。

---

## 一、服务管理（启停/重启/状态）

### 1.1 systemd 命令（Ubuntu 16.04+ / CentOS 7+ 通用）

| 操作 | 命令 |
|------|------|
| 启动 MySQL | `sudo systemctl start mysql` 或 `mysqld` |
| 停止 MySQL | `sudo systemctl stop mysql` |
| 重启 MySQL | `sudo systemctl restart mysql` |
| 查看状态 | `sudo systemctl status mysql` |
| 开机自启 | `sudo systemctl enable mysql` |
| 禁止自启 | `sudo systemctl disable mysql` |

### 1.2 service 命令（老版本兼容）

```bash
sudo service mysql start
sudo service mysql stop
sudo service mysql restart
sudo service mysql status
```

### 1.3 宝塔面板操作

直接在面板「软件商店」→「MySQL」→ 点击「设置」→「服务」选项卡即可管理。

---

## 二、终端连接 MySQL

### 2.1 本地连接

```bash
# 最常用：指定用户名密码连接
mysql -u root -p

# 连接指定数据库
mysql -u root -p database_name

# 指定主机和端口
mysql -h 127.0.0.1 -P 3306 -u root -p

# 不交互输入密码（不安全，脚本中慎用）
mysql -u root -pYourPassword
```

### 2.2 执行 SQL 语句/文件

```bash
# 直接执行单条 SQL
mysql -u root -p -e "SHOW DATABASES;"

# 执行 SQL 文件（导入）
mysql -u root -p database_name < backup.sql

# 进入数据库后使用 source 执行
mysql> source /path/to/file.sql;

# 将查询结果输出到文件
mysql -u root -p -e "SELECT * FROM users" database_name > result.txt
```

---

## 三、数据库操作命令

### 3.1 库级别操作

```sql
-- 查看所有数据库
SHOW DATABASES;

-- 创建数据库（指定字符集）
CREATE DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 删除数据库
DROP DATABASE mydb;

-- 切换数据库
USE mydb;

-- 查看当前使用的数据库
SELECT DATABASE();
```

### 3.2 表操作

```sql
-- 查看当前库所有表
SHOW TABLES;

-- 查看表结构
DESC table_name;
SHOW COLUMNS FROM table_name;
SHOW CREATE TABLE table_name;   -- 查看建表语句

-- 创建表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 重命名表
RENAME TABLE old_name TO new_name;

-- 删除表
DROP TABLE table_name;

-- 清空表数据（保留结构）
TRUNCATE TABLE table_name;
```

### 3.3 数据操作（CRUD）

```sql
-- 插入
INSERT INTO users (name, email) VALUES ('张三', 'zhang@example.com');
-- 批量插入
INSERT INTO users (name, email) VALUES ('李四', 'li@example.com'), ('王五', 'wang@example.com');

-- 查询
SELECT * FROM users;
SELECT id, name FROM users WHERE email LIKE '%@example.com';

-- 更新
UPDATE users SET email = 'new@example.com' WHERE id = 1;

-- 删除
DELETE FROM users WHERE id = 1;
```

---

## 四、用户与权限管理

```sql
-- 查看所有用户
SELECT user, host FROM mysql.user;

-- 创建用户（仅本地登录）
CREATE USER 'username'@'localhost' IDENTIFIED BY 'password';

-- 创建远程用户
CREATE USER 'username'@'%' IDENTIFIED BY 'password';

-- 授权指定库的所有权限
GRANT ALL PRIVILEGES ON database_name.* TO 'username'@'%';

-- 授权只读权限
GRANT SELECT ON database_name.* TO 'username'@'%';

-- 刷新权限（使授权生效）
FLUSH PRIVILEGES;

-- 查看用户权限
SHOW GRANTS FOR 'username'@'%';

-- 删除用户
DROP USER 'username'@'%';

-- 修改密码（MySQL 5.7+）
ALTER USER 'username'@'localhost' IDENTIFIED BY 'new_password';
-- 或老版本
SET PASSWORD FOR 'username'@'localhost' = PASSWORD('new_password');
```

---

## 五、备份与恢复

### 5.1 mysqldump 导出

```bash
# 导出单个数据库
mysqldump -u root -p database_name > backup.sql

# 导出所有数据库
mysqldump -u root -p --all-databases > all_backup.sql

# 只导出表结构（不含数据）
mysqldump -u root -p --no-data database_name > schema.sql

# 只导出数据（不含建表语句）
mysqldump -u root -p --no-create-info database_name > data.sql

# 导出指定表
mysqldump -u root -p database_name table1 table2 > tables.sql

# 带压缩的导出
mysqldump -u root -p database_name | gzip > backup.sql.gz
```

### 5.2 恢复

```bash
# 恢复 SQL 文件
mysql -u root -p database_name < backup.sql

# 恢复压缩备份
gunzip < backup.sql.gz | mysql -u root -p database_name

# 进入数据库后恢复
mysql> USE database_name;
mysql> source /path/to/backup.sql;
```

---

## 六、日志查看与诊断

### 6.1 慢查询日志

```bash
# 查看慢查询日志是否开启
mysql -u root -p -e "SHOW VARIABLES LIKE 'slow_query_log%';"

# 查看慢查询阈值
mysql -u root -p -e "SHOW VARIABLES LIKE 'long_query_time';"

# 实时查看慢查询日志（tail -f 持续监控）
tail -f /var/lib/mysql/slow.log

# 使用 mysqldumpslow 分析
mysqldumpslow -s t -t 10 /var/lib/mysql/slow.log   # 最慢的10条
mysqldumpslow -s c -t 10 /var/lib/mysql/slow.log   # 出现最频繁的10条
```

### 6.2 其他诊断命令

```bash
# 查看当前连接数
mysql -u root -p -e "SHOW PROCESSLIST;"

# 查看数据库状态（关注连接数、QPS等）
mysql -u root -p -e "SHOW STATUS;"

# 查看 InnoDB 状态
mysql -u root -p -e "SHOW ENGINE INNODB STATUS\G"

# 查看表大小
mysql -u root -p -e "
SELECT 
    table_schema AS '数据库',
    table_name AS '表名',
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS '大小(MB)'
FROM information_schema.tables 
WHERE table_schema NOT IN ('information_schema', 'mysql', 'performance_schema')
ORDER BY (data_length + index_length) DESC;
"
```

### 6.3 宝塔面板中查看日志

宝塔面板 →「软件商店」→ MySQL →「设置」→「日志」选项卡，可直接查看错误日志和慢查询日志。

---

## 七、实用技巧

### 7.1 命令行执行 SQL（不进入交互模式）

```bash
# 单条查询
mysql -u root -p -e "SELECT COUNT(*) FROM mydb.users;"

# 循环执行（监控脚本）
for i in {1..10}; do
  mysql -u root -pYourPass -e "SELECT NOW(), COUNT(*) FROM mydb.orders;"
  sleep 2
done
```

### 7.2 查看连接详情

```bash
# 查看当前所有活跃连接
mysql -u root -p -e "SHOW FULL PROCESSLIST;"

# 杀掉指定连接
mysql -u root -p -e "KILL 123;"   # 123 为连接 ID
```

### 7.3 在输出中垂直显示（方便阅读）

```sql
SELECT * FROM users LIMIT 1\G
-- 注意：结尾是 \G 而不是 ;
```

### 7.4 不记录操作历史的登录

```bash
# 退出后不留 .mysql_history 记录
MYSQL_HISTFILE=/dev/null mysql -u root -p
```

---

## 快速参考卡片

```
# 服务管理
systemctl start/stop/restart/status mysql

# 连接
mysql -u root -p
mysql -h 主机 -P 端口 -u 用户 -p

# 导入导出
mysqldump -u root -p 库名 > 文件.sql    # 导出
mysql -u root -p 库名 < 文件.sql        # 导入

# 慢查询分析
mysqldumpslow -s t -t 10 slow.log

# 查看操作
SHOW DATABASES;
SHOW TABLES;
DESC 表名;
SHOW CREATE TABLE 表名;
SHOW PROCESSLIST;
```

---

> **宝塔提示**：宝塔面板中修改 MySQL 配置后，记得在面板重启 MySQL 使配置生效。如果面板无法启动，可通过 SSH 用 `systemctl restart mysql` 手动重启。
