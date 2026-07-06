# Linux 运维核心指南：Shell、权限、systemd、日志、cron

> 配套你的轻量应用服务器（宝塔面板）和 Docker 全栈工作流。

---

## 一、Shell 命令——你的服务器母语

### 1.1 Shell 是什么？

Shell 是你和 Linux 内核之间的**翻译官**。你在终端输入命令，Shell 解释后交给内核执行。

```
你 → 终端 → Shell (bash/zsh) → Linux 内核 → 硬件
```

最常见的 Shell 是 **bash**（Bourne Again SHell），你的服务器 99% 用的就是它。

### 1.2 命令基本结构

```bash
命令 [选项] [参数]
ls   -la    /home
```

- **命令**：做什么（ls=列出文件）
- **选项**：怎么执行（-l=详细格式，-a=显示隐藏文件）
- **参数**：操作对象（/home 目录）

### 1.3 三大输入输出流

每个 Linux 程序启动时都打开三个"通道"：

| 编号 | 名称 | 默认指向 | 用途 |
|------|------|----------|------|
| 0 | stdin | 键盘 | 标准输入 |
| 1 | stdout | 屏幕 | 标准输出（正常信息） |
| 2 | stderr | 屏幕 | 标准错误（报错信息） |

### 1.4 重定向——控制输出流向

```bash
# 把正常输出写入文件（覆盖）
ls > files.txt

# 追加模式（不覆盖）
echo "新的一行" >> files.txt

# 把错误信息也重定向
npm install 2> errors.log          # 只重定向错误
npm install > all.log 2>&1         # 正常和错误都进同一个文件
npm install &> all.log             # 同上，bash 简写

# /dev/null——黑洞，丢弃不需要的输出
npm install > /dev/null 2>&1       # 静默执行
```

### 1.5 管道——命令间的"流水线"

管道 `|` 把左边命令的 stdout 送给右边命令的 stdin：

```bash
# 列出文件，只找 .js 的
ls -la | grep ".js"

# 找占用 3000 端口的进程并杀掉
lsof -i :3000 | awk 'NR>1{print $2}' | xargs kill

# 查日志中 ERROR 数量
grep "ERROR" app.log | wc -l

# 看磁盘使用，按大小排序
ps aux | sort -nrk 4 | head -10    # 内存占用前10
```

### 1.6 通配符

```bash
*       # 匹配任意多个字符    *.log → app.log, error.log
?       # 匹配单个字符       file?.txt → file1.txt, fileA.txt
[abc]   # 匹配括号内任一字符  file[123].txt → file1.txt, file2.txt
```

### 1.7 环境变量

```bash
# 查看
echo $PATH
echo $HOME
printenv              # 列出所有

# 临时设置
export MY_VAR="hello"

# 永久设置：写入 ~/.bashrc
# 修改后执行 source ~/.bashrc 使其生效
```

### 1.8 命令历史和快捷键

```bash
history              # 查看历史命令
!123                 # 重新执行第 123 条命令
!!                   # 重新执行上一条命令
!$                   # 引用上一条命令的最后一个参数
Ctrl+R               # 反向搜索历史命令（最实用的快捷键）
Ctrl+C               # 终止当前程序
Ctrl+Z               # 挂起当前程序（用 fg 恢复）
Ctrl+D               # 发送 EOF（退出终端）
Ctrl+L               # 清屏
```

### 1.9 编辑命令
```bash
# 用nano 编辑完按Ctrl+X -> Y Enter保存退出
nano ~/.bashrc

# 用 vim, i进入编辑模式，编辑完按Esc -> 
#:wq -> Enter 保存退出
#:w -> Enter 保存
#:q -> Enter 退出
#:x -> Enter 保存并退出
#:q! -> Enter 不保存强制退出
#:wq! -> Enter 强制保存并退出

#命令模式（非编辑模式）直接按，不用先按冒号
#dd 删除当前行
#yy 复制当前行
#p 粘贴到下一行
#u 撤销（undo）
#Ctrl + r 重做（redo）
#/关键词 搜索，按 n 跳下一个
#gg 跳到文件开头
#G 跳到文件末尾
#0 跳到行首
#$ 跳到行尾

#示例
#按 G → 跳到文件末尾
#按 o → 在下一行插入（自动进入编辑模式）
#粘贴或输入你的别名
#按 Esc → 退回命令模式
#按 :wq → 保存并退出
#source ~/.bashrc → 立即生效
vim ~/.bashrc

```

### 1.10 查看命令
echo 输出文本到屏幕或文件 写脚本、看变量、追加配置文件
print awk/python 等语言的打印函数 写 awk 一行脚本时
ls 列出目录内容（简洁版） 快速看一眼有哪些文件
ll 列出目录内容（详细版） 想看文件权限、大小、修改时间

---

## 二、权限——一切问题的隐形杀手

### 2.1 权限模型

```
-rwxr-xr-x  1 ey669 docker  4096 Jul  2 10:00 app.js
│├─┤├─┤├─┤    │     │
│ │  │  │     │     └── 所属组
│ │  │  │     └── 所有者
│ │  │  └── 其他人权限 (r-x)
│ │  └── 所属组权限 (r-x)
│ └── 所有者权限 (rwx)
└── 文件类型
```

**文件类型**：`-` 普通文件，`d` 目录，`l` 软链接

### 2.2 权限含义

| 权限 | 文件 | 目录 |
|------|------|------|
| r (读/4) | 可读取内容 | 可列出目录内容 (ls) |
| w (写/2) | 可修改内容 | 可创建/删除文件 |
| x (执行/1) | 可作为程序执行 | 可进入目录 (cd) |

**关键认知**：目录的 `x` 权限决定能否 `cd` 进去，没有 `x` 就算有 `r` 也进不去。

### 2.3 数字权限速查

```bash
chmod 777 file   # rwxrwxrwx  所有人都能读写执行（危险！）
chmod 755 file   # rwxr-xr-x  所有者全权限，其他人读+执行
chmod 644 file   # rw-r--r--  所有者读写，其他人只读（配置文件常用）
chmod 600 file   # rw-------  仅所有者读写（密钥文件必备）
chmod 400 file   # r--------  仅所有者读（只读密钥）

# 目录常用
chmod 755 dir    # 目录默认权限，所有人都能进入和列出
chmod 700 dir    # 仅所有者能进入（私密目录）
```

### 2.4 chmod 和 chown

```bash
# 改权限
chmod +x script.sh              # 给所有人加执行权限
chmod -R 755 /var/www           # 递归设置目录及所有子文件

# 改所有者
chown ey669:ey669 file.txt      # 同时改所有者和组
chown -R www-data:www-data /var/www/html
```

### 2.5 常见问题排查

```bash
# 网站 403 → 文件所有者是不是 www-data 能读？
ls -la /var/www/html

# npm install 报 EACCES → node_modules 目录权限
ls -la node_modules
chown -R $USER:$USER node_modules

# SSH 连不上 → 私钥权限太宽
chmod 600 ~/.ssh/id_rsa
chmod 700 ~/.ssh

# Docker 的 socket 权限
groups $USER        # 当前用户在 docker 组里吗？
sudo usermod -aG docker $USER  # 没在就加进去
```

### 2.6 umask——默认权限掩码

```bash
umask            # 查看当前值，通常是 0022
# 文件默认权限 = 666 - umask = 644
# 目录默认权限 = 777 - umask = 755
```

---

## 三、systemd——让你的服务"正规化"

### 3.1 为什么需要 systemd？

| 对比 | nohup / screen / 宝塔按钮 | systemd |
|------|---------------------------|---------|
| 开机自启 | ❌ 手动 | ✅ 一条命令 |
| 崩溃重启 | ❌ 没人管 | ✅ 自动拉起 |
| 日志管理 | ❌ 自己重定向 | ✅ journald 自动收集 |
| 依赖管理 | ❌ 手动保证顺序 | ✅ After/Requires |
| 资源限制 | ❌ 无 | ✅ CPU/内存限制 |

### 3.2 写一个服务单元文件

创建 `/etc/systemd/system/my-node-app.service`：

```ini
[Unit]
Description=My Node.js Application
Documentation=https://github.com/me/myapp
After=network.target mysql.service docker.service
Requires=mysql.service

[Service]
Type=simple
User=ey669
Group=ey669
WorkingDirectory=/home/ey669/app
ExecStart=/usr/bin/node dist/main.js
Restart=on-failure
RestartSec=5

# 环境变量
Environment=NODE_ENV=production
Environment=DB_HOST=mysql
EnvironmentFile=-/etc/myapp/.env

# 安全加固
NoNewPrivileges=yes
PrivateTmp=yes

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=my-node-app

# 资源限制
MemoryMax=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

### 3.3 Java 服务示例

```ini
[Service]
Type=simple
User=ey669
WorkingDirectory=/opt/my-java-app
ExecStart=/usr/bin/java -Xmx512m -jar /opt/my-java-app/target/app.jar
Restart=on-failure
RestartSec=10
Environment=SPRING_PROFILES_ACTIVE=production
```

### 3.4 管理命令

```bash
systemctl daemon-reload        # 改了 service 文件后必做
systemctl start my-node-app    # 启动
systemctl stop my-node-app     # 停止
systemctl restart my-node-app  # 重启
systemctl reload my-node-app   # 重载配置（如果服务支持）
systemctl enable my-node-app   # 开机自启
systemctl disable my-node-app  # 取消自启
systemctl status my-node-app   # 看状态+最近日志
systemctl is-active my-node-app
systemctl is-enabled my-node-app
systemctl list-units --type=service   # 列出所有服务
systemctl list-unit-files --type=service  # 列出所有服务文件
```

### 3.5 systemd 定时器（替代 cron 的新选择）

```ini
# /etc/systemd/system/backup.timer
[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl list-timers   # 查看所有定时器
```

---

## 四、日志——出问题时的时间机器

### 4.1 两条日志体系

| 体系 | 工具 | 存放位置 | 适用对象 |
|------|------|----------|----------|
| journald | journalctl | 二进制日志 (/var/log/journal/) | systemd 管理的服务 |
| rsyslog | tail/cat/less | 文本文件 (/var/log/) | 传统应用、系统 |

### 4.2 journalctl 常用命令

```bash
# 查看所有日志（从新到旧）
journalctl

# 查看特定服务的日志
journalctl -u my-node-app
journalctl -u my-node-app -f          # -f 实时追踪（= tail -f）
journalctl -u my-node-app -n 50       # 最近 50 行
journalctl -u my-node-app --no-pager  # 不用分页器，直接打印

# 时间过滤
journalctl --since "2026-07-02 10:00:00"
journalctl --since "1 hour ago"
journalctl --since "today"
journalctl --since "yesterday" --until "today"

# 按优先级过滤
journalctl -p err                     # 只看 error 及以上
journalctl -p warning                 # warning 及以上
# 优先级：emerg > alert > crit > err > warning > notice > info > debug

# 查看本次启动的日志
journalctl -b

# 查看内核日志
journalctl -k

# 磁盘占用
journalctl --disk-usage
sudo journalctl --vacuum-time=7d      # 只保留 7 天
sudo journalctl --vacuum-size=500M    # 最大 500MB
```

### 4.3 文本日志文件

```bash
# 系统日志
/var/log/syslog          # Debian/Ubuntu 系统主日志
/var/log/messages        # CentOS/RHEL 系统主日志
/var/log/auth.log        # 认证日志（SSH 登录记录）

# 应用日志
/var/log/nginx/access.log  # Nginx 访问日志
/var/log/nginx/error.log   # Nginx 错误日志
/var/log/mysql/error.log   # MySQL 错误日志

# 查看命令
cat file.log              # 全部打印（小文件用）
less file.log             # 分页浏览（/ 搜索，n 下一个）
tail -f file.log          # 实时追踪末尾
tail -n 100 file.log      # 最后 100 行
head -n 20 file.log       # 前 20 行
```

### 4.4 日志分析速查

```bash
# 统计各状态码数量
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# 访问量前 10 的接口
awk '{print $7}' access.log | sort | uniq -c | sort -rn | head -10

# 响应时间 > 1 秒的慢请求
awk '$NF > 1' access.log

# 统计每个 IP 的访问次数
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# 搜索包含 ERROR 的行及其前后各 3 行上下文
grep -C 3 "ERROR" app.log
```

### 4.5 Docker 日志

```bash
docker logs container-name
docker logs -f container-name           # 实时
docker logs --tail 100 container-name   # 最近 100 行
docker logs --since 30m container-name  # 最近 30 分钟

# docker-compose
docker compose logs -f backend
docker compose logs -f --tail=50
```

---

## 五、cron——你的自动化调度员

### 5.1 语法

```
# ┌──── 分钟 (0-59)
# │ ┌──── 小时 (0-23)
# │ │ ┌──── 日 (1-31)
# │ │ │ ┌──── 月 (1-12)
# │ │ │ │ ┌──── 星期 (0-7, 0和7都是周日)
# │ │ │ │ │
# * * * * * 要执行的命令
```

### 5.2 时间表达式

```bash
* * * * *          # 每分钟
0 * * * *          # 每小时整点
0 2 * * *          # 每天凌晨 2 点
0 2 * * 0          # 每周日凌晨 2 点
0 2 1 * *          # 每月 1 号凌晨 2 点
*/5 * * * *        # 每 5 分钟
0 */6 * * *        # 每 6 小时
0 9-17 * * *       # 每天 9 点到 17 点，每小时一次
0 9-17 * * 1-5     # 工作日 9-17 点，每小时一次
```

### 5.3 管理命令

```bash
crontab -e          # 编辑当前用户的 cron 表
crontab -l          # 列出当前用户的所有任务
crontab -r          # 删除所有任务（危险！）
crontab -u ey669 -e # 编辑指定用户的 cron

# cron 本身也有日志
grep CRON /var/log/syslog
```

### 5.4 实战示例

```bash
# 每天凌晨 3 点备份数据库
0 3 * * * mysqldump -u root -p'password' mydb | gzip > /backup/db_$(date +\%Y\%m\%d).sql.gz

# 每 10 分钟健康检查
*/10 * * * * curl -f http://localhost:3000/health || systemctl restart my-node-app

# 每周日凌晨清理旧备份（超过 30 天）
0 4 * * 0 find /backup/ -name "*.gz" -mtime +30 -delete

# 每小时清理 Docker 无用的镜像和容器
0 * * * * docker system prune -f

# 每天同步时间
0 1 * * * ntpdate -u ntp.aliyun.com

# 日志切割（防止日志文件撑爆磁盘）
0 0 * * * mv /var/log/app.log /var/log/app.log.$(date +\%Y\%m\%d) && touch /var/log/app.log
```

### 5.5 常见坑

1. **环境变量不同**：cron 的环境极简，`PATH` 可能只有 `/usr/bin:/bin`。解决：脚本开头 `source ~/.bashrc` 或使用绝对路径。
2. **`%` 要转义**：`%` 在 cron 中是特殊字符，表示换行。`date +\%Y\%m\%d` 必须转义。
3. **输出去哪了**：cron 的输出会尝试发邮件给用户。不想发邮件就重定向：`> /dev/null 2>&1`。
4. **权限问题**：cron 以当前用户身份执行，注意文件读写权限。
5. **调试方法**：先写一个每分钟执行的测试任务 `* * * * * echo "test" >> /tmp/cron.log 2>&1`，确认 cron 正常工作。

### 5.6 推荐做法

```bash
# 不要直接在 crontab 里写复杂命令，调用脚本
0 3 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
```

---

## 六、Linux Shell 命令速查表

### 6.1 文件和目录操作（10条）

| 命令 | 说明 | 常用示例 |
|------|------|----------|
| `ls` | 列出目录内容 | `ls -la`, `ls -lh`(人类可读大小), `ls -lt`(按时间排序) |
| `cd` | 切换目录 | `cd ~`, `cd -`(回上一个目录), `cd ..` |
| `pwd` | 显示当前路径 | `pwd` |
| `mkdir` | 创建目录 | `mkdir -p a/b/c`(递归创建) |
| `touch` | 创建空文件/更新时戳 | `touch file.txt` |
| `cp` | 复制 | `cp -r src dest`(递归), `cp -p`(保留属性) |
| `mv` | 移动/重命名 | `mv old new` |
| `rm` | 删除 | `rm -rf dir/`(⚠️危险！), `rm -i`(确认) |
| `find` | 查找文件 | `find . -name "*.log" -mtime +7 -delete` |
| `ln` | 创建链接 | `ln -s /target linkname`(软链接) |

### 6.2 文件内容查看（8条）

| 命令 | 说明 | 常用示例 |
|------|------|----------|
| `cat` | 输出全部内容 | `cat file.txt`, `cat a.txt b.txt > c.txt`(合并) |
| `less` | 分页浏览 | `less file.log`，`/`搜索，`n`下一个，`q`退出 |
| `head` | 查看前 N 行 | `head -20 file.txt` |
| `tail` | 查看后 N 行 | `tail -f app.log`(追踪), `tail -n 50` |
| `grep` | 文本搜索 | `grep -r "error" .`, `grep -v "debug"`(排除), `grep -i`(忽略大小写) |
| `wc` | 统计 | `wc -l file`(行数), `wc -c`(字节数) |
| `sort` | 排序 | `sort -n`(数字), `sort -r`(倒序), `sort -u`(去重) |
| `uniq` | 去重 | `sort file | uniq -c`(计数) |

### 6.3 权限和用户（6条）

| 命令 | 说明 | 常用示例 |
|------|------|----------|
| `chmod` | 修改权限 | `chmod 755 file`, `chmod +x script.sh` |
| `chown` | 修改所有者 | `chown -R user:group dir/` |
| `sudo` | 以 root 执行 | `sudo systemctl restart nginx` |
| `whoami` | 我是谁 | `whoami` |
| `id` | 用户信息 | `id ey669` |
| `passwd` | 修改密码 | `passwd` |

### 6.4 进程管理（7条）

| 命令 | 说明 | 常用示例 |
|------|------|----------|
| `ps` | 查看进程 | `ps aux`, `ps aux \| grep java` |
| `top` / `htop` | 实时进程监控 | `top`，按 `M` 按内存排序，`P` 按 CPU 排序 |
| `kill` | 发信号给进程 | `kill -9 PID`(强制杀), `kill -15 PID`(优雅退出) |
| `pkill` | 按名称杀进程 | `pkill -f "node"` |
| `nohup` | 后台运行 | `nohup npm start &` |
| `jobs` / `bg` / `fg` | 作业管理 | `jobs` 列出, `fg %1` 调到前台 |
| `lsof` | 列出打开的文件 | `lsof -i :3000`(谁占用端口) |

### 6.5 网络（6条）

| 命令 | 说明 | 常用示例 |
|------|------|----------|
| `curl` | 发 HTTP 请求 | `curl -X POST http://localhost/api`, `curl -I`(只看头) |
| `ping` | 测试连通性 | `ping -c 4 8.8.8.8` |
| `ss` | 查看网络连接 | `ss -tlnp`(监听端口), `ss -an`(所有连接) |
| `netstat` | 传统网络工具 | `netstat -tlnp` |
| `wget` | 下载文件 | `wget https://example.com/file.tar.gz` |
| `scp` | 远程拷贝 | `scp file.txt user@host:/path/` |

### 6.6 磁盘和空间（5条）

| 命令 | 说明 | 常用示例 |
|------|------|----------|
| `df` | 磁盘空间 | `df -h`(人类可读) |
| `du` | 目录大小 | `du -sh *`, `du -h --max-depth=1` |
| `ncdu` | 交互式磁盘分析 | `ncdu /` (需安装) |
| `free` | 内存使用 | `free -h` |
| `mount` / `umount` | 挂载 | `mount /dev/sdb1 /mnt/data` |

### 6.7 压缩打包（4条）

| 命令 | 说明 | 常用示例 |
|------|------|----------|
| `tar` | 打包/解包 | `tar -czf archive.tar.gz dir/`(打包压缩), `tar -xzf file.tar.gz`(解压) |
| `gzip` / `gunzip` | 压缩/解压 | `gzip file`, `gunzip file.gz` |
| `zip` / `unzip` | zip 格式 | `zip -r archive.zip dir/`, `unzip file.zip` |

### 6.8 文本处理三剑客（3条）

| 命令 | 说明 | 擅长 |
|------|------|------|
| `grep` | 文本搜索过滤 | 找内容 |
| `sed` | 流编辑器 | 替换/删除 |
| `awk` | 文本分析工具 | 取列/计算 |

```bash
# grep — 找包含 ERROR 的行
grep "ERROR" app.log

# sed — 把所有 "foo" 替换为 "bar"
sed 's/foo/bar/g' file.txt

# awk — 取第 1 和第 7 列（IP 和 URL）
awk '{print $1, $7}' access.log
```

### 6.9 包管理（Debian/Ubuntu）

```bash
apt update              # 更新软件源
apt upgrade             # 升级所有包
apt install nginx       # 安装
apt remove nginx        # 卸载
apt search keyword      # 搜索
apt list --installed    # 列出已安装
```

### 6.10 其他实用命令

```bash
which node              # 查看命令的完整路径
type ls                 # 查看命令类型
alias ll='ls -la'       # 创建别名（写入 ~/.bashrc 永久保存）
watch -n 1 'df -h'      # 每秒执行一次命令
tee                     # 同时输出到屏幕和文件
                        # npm install 2>&1 | tee install.log
xargs                   # 将标准输入转为命令参数
                        # cat ids.txt | xargs kill
```

---

## 七、综合实战：出故障了怎么办？

```bash
# 1. 先看服务状态
systemctl status my-node-app

# 2. 看日志找线索
journalctl -u my-node-app -n 50 --no-pager

# 3. 端口被占了吗？
ss -tlnp | grep 3000

# 4. 磁盘满了吗？
df -h
du -sh /var/log/*

# 5. 内存够吗？
free -h
ps aux --sort=-%mem | head -10

# 6. 重启试试
systemctl restart my-node-app && journalctl -u my-node-app -f

# 7. 如果是权限问题
ls -la /path/to/problem
chown -R www-data:www-data /var/www/html

# 8. 加监控 cron
*/10 * * * * curl -f http://localhost:3000/health || systemctl restart my-node-app
```

---

> **学习建议**：不要试图记住所有命令。用 `man 命令名` 或 `命令 --help` 随时查。真正的功力在于**管道组合**和**排查思路**，而不是背诵参数。
