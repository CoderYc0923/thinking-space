# Linux 运维五大主题实操练习路线

> 在你的轻量应用服务器（宝塔面板环境）上完成。
> 原则：尽量不用宝塔点按钮，用终端解决一切。

---

## 第一阶段：Shell 热身——像逛自己家一样逛服务器

SSH 登进去，完成以下任务：

```bash
# 任务 1：搞清楚你的服务器
whoami                    # 你是谁？
uname -a                  # 系统是什么？
cat /etc/os-release       # 哪个发行版？
df -h                     # 磁盘多大？还剩多少？
free -h                   # 内存多少？
lscpu                     # 几核 CPU？

# 任务 2：探索目录结构
cd / && ls -la            # 根目录下都有什么？
ls -la /var/log           # 日志都在哪？
ls -la /etc               # 配置文件在哪？

# 任务 3：管道练习——找宝塔用了哪些端口
ss -tlnp | grep -E "nginx|mysql|php|python|node"
#ss -tlnp — 列出所有 TCP 监听端口及对应进程
#grep -E 启用扩展正则表达式，让 | 能当"或"用
#nginx|mysql|php|python|node 匹配包含 nginx 或 mysql 或 php 或 python 或 node 的行


# 任务 4：看看谁在登录
last -10                  # 最近 10 次登录记录
w                         # 当前登录用户
```

**检验标准**：不看笔记，能说出 `/etc`、`/var/log`、`/home` 分别是干什么的。
/etc — 存放系统配置文件和启动脚本。比如 Nginx 配置 /etc/nginx/nginx.conf、用户密码 /etc/passwd、定时任务 /etc/crontab

/var/log — 存放系统和各类服务的日志文件。查错在这里翻：/var/log/messages（系统日志）、/var/log/nginx/（Nginx）、/var/log/mysql/

/home — 普通用户的个人主目录，存放个人文件和用户级配置。类似 Windows 的 C:\Users

ss 是现代 Linux 下的 socket 统计工具，用来替代旧命令 netstat
-t 只显示 TCP 连接
-l 只显示处于监听状态的端口
-n 数字形式显示端口和 IP，不解析域名
-p 显示使用该端口的进程信息
| grep 过滤结果，例如查 80 端口是否在监听

使用示例：
ss -tlnp 列出所有 TCP 监听端口及对应进程
ss -tlnp | grep 80 看 80/8080/3000 等端口是谁在监听
ss -tlnp | grep nginx 看 nginx 监听在哪些端口

---

## 第二阶段：写一个最简 Node 服务，用 systemd 管起来

### 步骤 1：创建测试项目

```bash
mkdir ~/hello-server && cd ~/hello-server
npm init -y
npm install express
```

创建 `index.js`：

```javascript
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3456;

app.get('/', (req, res) => {
  res.json({ status: 'ok', time: new Date().toISOString() });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

先手动跑起来验证：`node index.js`，另一个终端 `curl localhost:3456/health`。确认 OK 后 Ctrl+C 停掉。

### 步骤 2：写 systemd 服务文件

```bash
sudo vim /etc/systemd/system/hello-server.service
```

（vim 基础：按 `i` 进入编辑模式，粘贴下面内容，按 `Esc`，输入 `:wq` 保存退出）

```ini
[Unit]
Description=Hello Server - 练习服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/hello-server
ExecStart=/usr/bin/node /root/hello-server/index.js
Restart=on-failure
RestartSec=5

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 步骤 3：启动并验证

```bash
sudo systemctl daemon-reload
sudo systemctl start hello-server
sudo systemctl status hello-server     # 看状态
curl localhost:3456/health              # 验证
sudo systemctl enable hello-server      # 设置开机自启
```

### 步骤 4：故意搞坏它

```bash
# 改端口为一个被占用的（比如 nginx 的 80），看它怎么报错
sudo vim /root/hello-server/index.js  # 改 PORT 为 80
sudo systemctl restart hello-server
sudo systemctl status hello-server    # 看到了什么？
journalctl -u hello-server -n 20      # 查日志找原因
```

修好再改回 3456。

**检验标准**：能独立写出一个 `.service` 文件，并说出 `After`、`Restart`、`WantedBy` 的含义。

---

## 第三阶段：权限实验——三条命令，直观感受

在服务器上做以下实验：

```bash
# 实验 1：目录没有 x 权限就进不去
mkdir /tmp/permission-test
cd /tmp/permission-test
echo "hello" > test.txt
chmod 666 test.txt     # 文件可读写但不能执行
cat test.txt            # 能读

cd /tmp
chmod 644 permission-test   # 目录只有 rw，没有 x
ls -la permission-test/     # 能列出
cd permission-test/         # 报错！Permission denied
chmod 755 permission-test   # 加回 x
cd permission-test/         # 可以了

# 实验 2：文件所有者不对导致 403（模拟 Web 场景）
echo "<?php phpinfo(); ?>" > /tmp/test.php
sudo chown www-data:www-data /tmp/test.php
# 如果你用 Nginx，试着访问这个文件，看权限怎么影响

# 实验 3：SSH 私钥权限太宽会被拒绝
# （如果是密码登录可以跳过，但要知道这个坑）
ls -la ~/.ssh/
# 如果 id_rsa 不是 600，SSH 会拒绝连接
```

**检验标准**：能解释为什么 `chmod 755 dir` 和 `chmod 644 file` 是 Web 服务器的标准权限配置。

---

## 第四阶段：日志——学会"看日志找问题"

### 实验 1：对比 journalctl 和 tail -f

```bash
# systemd 服务日志
journalctl -u hello-server -f       # 开一个窗口实时看
# 另一个窗口
curl localhost:3456/health          # 观察日志输出

# 系统认证日志
sudo tail -f /var/log/auth.log      # 开另一个终端 SSH 登录，观察日志

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
# 浏览器访问你的网站，观察日志
```

### 实验 2：日志分析练习

```bash
# 用 Nginx 日志做数据分析
sudo cat /var/log/nginx/access.log | \
  awk '{print $1}' | \
  sort | uniq -c | sort -rn | head -10
# 输出：访问量前 10 的 IP

# 统计状态码分布
sudo cat /var/log/nginx/access.log | \
  awk '{print $9}' | \
  sort | uniq -c | sort -rn

# 找 500 错误的请求
sudo grep " 500 " /var/log/nginx/access.log
```

### 实验 3：Docker 日志对比

如果你已经跑了 Docker 容器：

```bash
docker ps                           # 看有哪些容器
docker logs --tail 50 容器名
```

**检验标准**：服务挂了，你能在三分钟内通过日志定位到原因。

---

## 第五阶段：cron——让它替你干活

### 实验 1：最简单的 cron 测试

```bash
crontab -e
# 添加一行：
* * * * * echo "cron ran at $(date)" >> /tmp/cron-test.log 2>&1
```

等两分钟，然后：

```bash
cat /tmp/cron-test.log
```

确认能正常执行后，删掉这行（`crontab -e` 进去删）。

### 实验 2：写一个健康检查脚本

创建 `/opt/scripts/health-check.sh`：

```bash
#!/bin/bash
# 健康检查脚本

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3456/health)

if [ "$RESPONSE" != "200" ]; then
  echo "[$(date)] Health check FAILED (HTTP $RESPONSE), restarting..." >> /var/log/health-check.log
  systemctl restart hello-server
else
  echo "[$(date)] Health check OK" >> /var/log/health-check.log
fi
```

```bash
sudo mkdir -p /opt/scripts
sudo vim /opt/scripts/health-check.sh   # 粘贴上面内容
sudo chmod +x /opt/scripts/health-check.sh

# 手动测试
sudo /opt/scripts/health-check.sh
cat /var/log/health-check.log

# 加入 cron
sudo crontab -e
# 添加：
*/5 * * * * /opt/scripts/health-check.sh
```

### 实验 3：数据库自动备份（如果你有 MySQL）

```bash
sudo mkdir -p /backup/mysql
sudo vim /opt/scripts/backup-db.sh
```

```bash
#!/bin/bash
mysqldump -u root -p'你的密码' --all-databases | gzip > /backup/mysql/all_$(date +\%Y\%m\%d_\%H\%M).sql.gz

# 删除 7 天前的旧备份
find /backup/mysql/ -name "*.gz" -mtime +7 -delete

echo "[$(date)] Backup completed" >> /var/log/backup.log
```

```bash
sudo chmod +x /opt/scripts/backup-db.sh
sudo crontab -e
# 添加：0 3 * * * /opt/scripts/backup-db.sh
```

**检验标准**：能独立写一个定时脚本，处理 `%` 转义和日志重定向。

---

## 综合实战：模拟一次"半夜服务挂了"

让朋友或自己按顺序执行以下操作，然后你来排查：

```bash
# 1. 先让服务正常运行
sudo systemctl start hello-server

# 2. "凶手"操作（随机选 2-3 个）：

# A. 改了端口，导致冲突
# B. chmod 000 /root/hello-server/index.js （文件不可读）
# C. 用 iptables 临时封了端口
# D. 建了个死循环把 CPU 打满
# E. 把磁盘用 dd 填到 95%
# F. 改了 .env 里数据库密码为错的

# 3. 你来排查
```

**你的排查标准流程**：

```bash
# 第 1 步：服务状态
systemctl status hello-server

# 第 2 步：查日志
journalctl -u hello-server -n 50 --no-pager

# 第 3 步：端口和进程
ss -tlnp | grep 3456
ps aux | grep node

# 第 4 步：系统资源
df -h
free -h
top -bn1 | head -5

# 第 5 步：权限
ls -la /root/hello-server/
```

---

## 学习节奏建议

| 时间 | 内容 | 目标 |
|------|------|------|
| 第 1 天 | 第一阶段 Shell 热身 + 第二阶段写 service 文件 | 把 systemd 跑通 |
| 第 2 天 | 第三阶段权限实验 | 理解 rwx 和 chmod/chown |
| 第 3 天 | 第四阶段日志实验 | 熟练 journalctl 和 tail -f |
| 第 4 天 | 第五阶段 cron + 健康检查脚本 | 写出第一个生产级脚本 |
| 第 5 天 | 综合实战——故障排查演练 | 三分钟定位问题 |

---

## 如果遇到问题

1. **先看日志**——90% 的问题日志里有答案
2. **最小化复现**——去掉复杂因素，只保留核心
3. **问 AI 时带上上下文**："我在 Ubuntu 22.04 上，用 systemd 启动 Node 服务，报错 xxx，日志是 xxx"

> 五天练完，你就能自信地说"服务器我能管"了。有问题随时回来问。
