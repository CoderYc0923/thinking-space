# Linux 运维与 Shell 实操学习手册

> 适用对象：具备前端/后端开发基础，需要补齐 Linux 运维实操能力（部署、排查、监控、代理、负载均衡）
> 实验环境：Ubuntu 22.04 LTS / CentOS Stream 9（本文以 Ubuntu 为主线，CentOS 差异单独标注）
> 学习方式：**所有命令必须在真实服务器或云主机上敲一遍，禁止只看不练**
> 总周期：约 3 周，每天 40～60 分钟

---

## 一、学习目标与阶段总览

| 阶段 | 主题 | 核心能力 | 建议时长 | 验收标准 |
|---|---|---|---|---|
| 阶段 0 | 环境准备 | ssh 登录、目录规划、安全习惯 | 30 min | 能用普通用户登录并 `sudo` 提权 |
| 阶段 1 | 文件与目录 | 增删改查、权限、软硬链接 | 1～2 天 | 能独立完成站点目录搭建与权限设定 |
| 阶段 2 | 文本处理 | grep/awk/sed/管道、日志过滤 | 1～2 天 | 能从访问日志中统计 IP 访问量与错误码分布 |
| 阶段 3 | 进程与网络 | ps/top/ss、资源查看、端口排障 | 2 天 | 能定位「端口被占用」「服务假死」类问题 |
| 阶段 4 | 服务管理 | 包管理、systemd、journalctl | 2 天 | 能用 systemd 托管服务并排查启动失败 |
| 阶段 5 | Shell 脚本 | 变量、判断、循环、函数、日志 | 2～3 天 | 能写出可用的巡检/备份脚本 |
| 阶段 6 | 综合实战 | Nginx 反代 + 巡检 + 定时任务 | 3 天 | 完整部署一套站点并完成故障演练 |
| 阶段 7（预告） | 代理与负载均衡 | upstream / HAProxy / Keepalived | 后续进阶 | 双后端负载均衡 + 故障转移 |

### 能力递进关系

```mermaid
graph LR
    A[阶段0 环境准备] --> B[阶段1 文件权限]
    B --> C[阶段2 文本处理]
    C --> D[阶段3 进程网络]
    D --> E[阶段4 服务管理]
    E --> F[阶段5 Shell脚本]
    F --> G[阶段6 综合实战]
    G --> H[阶段7 负载均衡/高可用]
```

---

## 二、阶段 0：环境准备

### 2.1 登录与安全习惯

```bash
# 首次登录（推荐普通用户 + sudo，不要长期 root 操作）
ssh your_user@<服务器IP> -p 22

# 配置免密登录（本地机器执行）
ssh-keygen -t ed25519 -C "lab"
ssh-copy-id your_user@<服务器IP>
```

| 习惯 | 说明 |
|---|---|
| 不用 root 直接操作 | 贴近真实运维，避免误操作放大 |
| 高危命令先 `echo` 预览 | 例如删目录前先确认变量展开 |
| 改配置前先备份 | `cp nginx.conf nginx.conf.bak-$(date +%F)` |
| 生产与实验隔离 | 本文全部操作请在专用练习机上执行 |

### 2.2 建立实验目录

```bash
sudo mkdir -p /opt/lab
sudo chown -R $USER:$USER /opt/lab
cd /opt/lab
```

### 2.3 五个「救命」命令

```bash
pwd        # 当前路径
ls -al     # 当前目录内容（含隐藏文件与权限）
cd ~       # 回家目录
cd -       # 回上一个目录（比 cd .. 更实用）
history    # 历史命令，配合 Ctrl+R 反向搜索
```

> 排错技巧：命令执行异常时，用 `echo $?` 看返回码，0 为成功，非 0 为失败。

---

## 三、阶段 1：文件与目录操作

### 3.1 基础命令清单

```bash
# 查看
ls -lht              # 按时间倒序 + 人类可读大小
ls -a                # 显示隐藏文件
stat file.txt        # 查看文件详细元信息（inode、权限、时间）

# 创建
mkdir -p /opt/lab/site/web1   # 递归创建
touch empty.txt               # 创建空文件

# 复制与移动
cp a.txt b.txt
cp -r srcdir dstdir
mv a.txt newname.txt          # 重命名 == 移动

# 删除（高危，务必二次确认）
rm file.txt
rm -r dirname
# 危险操作前先预览：把 rm 换成 echo
# echo rm -rf /opt/lab/old
```

### 3.2 查看文件内容

```bash
cat file.txt          # 全量输出，小文件用
less file.txt         # 分页查看，q 退出，/ 搜索
head -n 20 file.txt   # 前 20 行
tail -n 50 file.txt   # 末 50 行
tail -f app.log       # 实时跟踪，看日志核心命令
tail -F app.log       # 日志轮转后仍能跟踪（生产环境用 -F）
```

### 3.3 权限与归属

```bash
chmod 755 start.sh      # 所有者 rwx，同组 rx，其他 rx
chmod +x start.sh       # 追加执行权限
chmod -R 755 /opt/lab/site
chown -R www-data:www-data /var/www/html   # 属主:属组
umask                   # 默认权限掩码，通常 0022
```

| 数字 | 权限 | 含义 |
|---|---|---|
| 7 | rwx | 读 + 写 + 执行 |
| 6 | rw- | 读 + 写 |
| 5 | r-x | 读 + 执行 |
| 4 | r-- | 只读 |

常见约定：**目录 755，普通文件 644，脚本 755，敏感配置 600**。

### 3.4 软链接（部署高频）

```bash
ln -s /opt/lab/site/web1 /opt/lab/current   # 软链接，类似快捷方式
ls -l /opt/lab/current                      # 会显示 -> 指向
readlink -f /opt/lab/current                # 解析真实路径

# 典型场景：蓝绿/版本切换
# 新版本目录 /opt/lab/releases/v2，上线时只切换链接
ln -sfn /opt/lab/releases/v2 /opt/lab/current
```

### 3.5 打包与压缩

```bash
tar -zcvf backup.tar.gz /opt/lab/site      # 打包压缩
tar -zxvf backup.tar.gz -C /tmp            # 解压到指定目录
tar -tf backup.tar.gz | head               # 只看内容不解压
du -sh /opt/lab/*                          # 查看各目录占用
```

### 3.6 实操任务

1. 创建 `/opt/lab/site/web1`、`/opt/lab/site/web2`
2. 各写一个 `index.html`，内容分别为 `<h1>web1 ok</h1>`、`<h1>web2 ok</h1>`
3. 目录权限设为 755，文件权限设为 644
4. 创建软链接 `/opt/lab/current` 指向 `web1`
5. 打包 `/opt/lab/site` 到 `/opt/lab/backup/site-$(date +%F).tar.gz`

---

## 四、阶段 2：文本处理与日志分析

这是运维排障的**分水岭**，掌握后日志分析效率提升数倍。

### 4.1 核心三件套

```bash
grep "ERROR" app.log              # 精确匹配
grep -i "error" app.log           # 忽略大小写
grep -v "health" access.log       # 反向过滤
grep -n "timeout" app.log         # 显示行号
grep -c "500" access.log          # 统计命中行数
grep -r "listen 80" /etc/nginx    # 递归搜索目录
grep -E "ERROR|FATAL" app.log     # 扩展正则，多关键词
```

```bash
awk '{print $1}' access.log            # 按空白分列，取第 1 列
awk '{print $7, $9}' access.log        # 取 URL 与状态码
awk '$9 >= 500 {print $0}' access.log  # 条件过滤：5xx 请求
awk -F: '{print $1}' /etc/passwd       # 指定分隔符
```

```bash
sed -n '10,20p' file.txt            # 打印 10～20 行
sed 's/http/https/g' file.txt       # 全局替换（不落盘）
sed -i 's/8080/80/g' nginx.conf     # 直接修改文件（改配置前先备份！）
```

### 4.2 管道与统计组合

```bash
# 统计 Top10 访问 IP
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# 统计状态码分布
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# 找出访问量最大的 URL
awk '{print $7}' access.log | sort | uniq -c | sort -rn | head -5

# 统计行数 / 去重
wc -l access.log
sort access.log | uniq | wc -l
```

### 4.3 实操案例：模拟日志分析

```bash
cd /opt/lab
cat > access.log <<'EOF'
10.0.0.1 - - [13/Nov/2026:09:00:01] "GET /index.html" 200 1024
10.0.0.2 - - [13/Nov/2026:09:00:02] "GET /api/user" 500 512
10.0.0.1 - - [13/Nov/2026:09:00:03] "GET /api/order" 404 128
10.0.0.3 - - [13/Nov/2026:09:00:04] "POST /api/user" 200 2048
10.0.0.2 - - [13/Nov/2026:09:00:05] "GET /api/user" 500 512
EOF

grep " 500 " access.log                          # 找 5xx 请求
awk '{print $1}' access.log | sort | uniq -c     # IP 访问计数
awk '{print $9}' access.log | sort | uniq -c     # 状态码分布
```

> 验收：在不看答案的情况下，写出「统计 4xx 请求来自哪些 IP」的一行命令。
> 参考：`awk '$9 ~ /^4/ {print $1}' access.log | sort | uniq -c`

---

## 五、阶段 3：进程、端口与系统资源

### 5.1 进程查看

```bash
ps aux                    # 全部进程
ps -ef | grep nginx       # 传统风格查看
ps aux --sort=-%cpu | head -5   # CPU 占用 Top5
pgrep -a nginx            # 按名字找 PID
pstree -p                 # 进程树
top                       # 实时监控（q 退出，P 按 CPU 排序，M 按内存）
htop                      # 更友好，需安装：sudo apt install htop
```

### 5.2 系统资源

```bash
uptime          # 开机时长 + 1/5/15 分钟平均负载
free -h         # 内存与 swap
df -h           # 磁盘挂载点使用率
df -i           # inode 使用率（小文件过多会爆这个）
du -sh /* 2>/dev/null | sort -rh | head -10   # 找大目录
lsblk           # 块设备与挂载关系
vmstat 1 5      # 每秒采样 5 次：CPU、内存、IO
iostat -x 1 5   # 磁盘 IO 详情（需 sysstat）
```

> **负载判断口诀**：`load average` 对比 CPU 核数（`nproc`）。1 分钟负载持续 > 核数，说明存在排队。

### 5.3 端口与网络

```bash
ss -tulpn                   # 所有监听端口 + 进程（现代替代 netstat）
ss -tulpn | grep :80        # 查 80 端口占用
ss -tnp | grep ESTAB        # 查看已建立的连接
ss -s                       # 连接状态汇总
lsof -i :8080               # 按端口反查进程（需安装 lsof）
ip addr                     # 查看 IP
ip route                    # 查看路由
ping -c 4 baidu.com         # 连通性
curl -I http://127.0.0.1    # 只看响应头
curl -v http://127.0.0.1    # 详细过程，排查连接问题
curl -o /dev/null -s -w "%{http_code} %{time_total}\n" http://127.0.0.1   # 状态码与耗时
```

### 5.4 实操案例：端口冲突排查（部署高频错误）

```bash
cd /opt/lab/site/web1
python3 -m http.server 8080 &        # 后台起一个简易 web 服务
ss -tulpn | grep 8080                # 查看监听情况
curl -I http://127.0.0.1:8080        # 验证可访问

# 再起一个同端口服务，观察报错
python3 -m http.server 8080          # 报错：Address already in use

# 定位并释放
ps aux | grep http.server
kill <PID>                           # 优雅停止
kill -9 <PID>                        # 强制杀，仅在无响应时使用
```

> 生产对应场景：Nginx / Java 应用启动失败报 `Address already in use`，就是这套排查流程。

---

## 六、阶段 4：包管理与 systemd 服务管理

### 6.1 包管理对照

| 操作 | Ubuntu / Debian | CentOS / RHEL |
|---|---|---|
| 更新索引 | `sudo apt update` | `sudo yum makecache`（或 `dnf makecache`） |
| 安装 | `sudo apt install nginx` | `sudo yum install nginx` |
| 卸载 | `sudo apt remove nginx` | `sudo yum remove nginx` |
| 搜索 | `apt search nginx` | `yum search nginx` |
| 查已装包 | `dpkg -l \| grep nginx` | `rpm -qa \| grep nginx` |
| 查看占用文件的包 | `dpkg -S /usr/sbin/nginx` | `rpm -qf /usr/sbin/nginx` |

### 6.2 systemd 命令（必须背熟）

```bash
sudo systemctl start nginx       # 启动
sudo systemctl stop nginx        # 停止
sudo systemctl restart nginx     # 重启（有短暂中断）
sudo systemctl reload nginx      # 平滑重载配置（Nginx 优先用这个）
sudo systemctl status nginx      # 状态 + 最近日志
sudo systemctl enable nginx      # 开机自启
sudo systemctl disable nginx     # 关闭自启
systemctl list-units --type=service --state=running   # 正在运行的服务
```

### 6.3 日志排查

```bash
journalctl -u nginx -f                  # 实时跟踪服务日志
journalctl -u nginx --since "10 min ago"
journalctl -u nginx -p err              # 只看错误级别
journalctl -xe                          # 最近系统异常
journalctl --disk-usage                 # 日志占用
```

### 6.4 托管一个自研服务（systemd 单元）

后端/脚本上线标准做法。以 Python 服务为例：

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Demo App
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/lab/app
ExecStart=/usr/bin/python3 -m http.server 9000
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload      # 改完单元文件必须执行
sudo systemctl enable --now myapp # 设开机自启并立即启动
sudo systemctl status myapp
journalctl -u myapp -f
```

### 6.5 防火墙

```bash
# Ubuntu (ufw)
sudo ufw status
sudo ufw allow 22/tcp
sudo ufw allow 80,443/tcp
sudo ufw enable

# CentOS (firewalld)
sudo firewall-cmd --state
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --reload
```

### 6.6 实操任务：部署 Nginx 静态站点

```bash
sudo apt update && sudo apt install -y nginx
sudo cp /opt/lab/site/web1/index.html /var/www/html/
curl -I http://127.0.0.1
sudo systemctl status nginx
sudo nginx -t                     # 配置校验，上线前必敲
```

**故障演练**：故意把 `/etc/nginx/nginx.conf` 里某个 `}` 删掉，依次执行：

```bash
sudo nginx -t                     # 1. 校验报错，定位文件与行号
sudo systemctl restart nginx      # 2. 启动失败
sudo systemctl status nginx       # 3. 看失败原因
sudo journalctl -u nginx -n 50    # 4. 看详细日志
# 5. 修复后重新 nginx -t，再 restart
```

---

## 七、阶段 5：Shell 脚本基础

### 7.1 脚本骨架与规范

```bash
#!/bin/bash
set -euo pipefail     # 出错即停 + 未定义变量报错 + 管道错误捕获，生产脚本建议开启

LOG_DIR=/opt/lab/logs
mkdir -p "$LOG_DIR"
log() { echo "[$(date '+%F %T')] $*"; }
```

```bash
chmod +x script.sh
./script.sh                 # 相对路径执行
bash script.sh              # 显式用 bash 解释
shellcheck script.sh        # 静态检查（强烈推荐安装）
```

### 7.2 变量与字符串

```bash
name="web1"
echo "$name"                 # 双引号会展开变量
echo '$name'                 # 单引号原样输出
echo "${name}_backup"        # 花括号界定变量边界

port=${1:-8080}              # 取第一个参数，无参则默认 8080
len=${#name}                 # 长度
echo "${name^^}"             # 转大写
```

### 7.3 条件判断

```bash
if [ -f /etc/nginx/nginx.conf ]; then
    echo "配置文件存在"
elif [ -d /opt/lab ]; then
    echo "目录存在"
else
    echo "都不存在"
fi

# 常用测试
[ -e path ]   # 存在
[ -f path ]   # 是文件
[ -d path ]   # 是目录
[ -x path ]   # 可执行
[ -z "$str" ] # 字符串为空
[ "$a" -gt "$b" ]  # 数值比较：-eq -ne -gt -ge -lt -le
[[ "$str" == *error* ]]  # 双中括号支持模式匹配
```

### 7.4 循环与函数

```bash
for ip in 10.0.0.1 10.0.0.2 10.0.0.3; do
    if ping -c 1 -W 1 "$ip" >/dev/null 2>&1; then
        echo "$ip 可达"
    else
        echo "$ip 不可达"
    fi
done

check_service() {
    local svc=$1
    if systemctl is-active --quiet "$svc"; then
        echo "$svc 运行中"
        return 0
    fi
    echo "$svc 已停止"
    return 1
}
```

### 7.5 返回值与错误处理

```bash
command >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "成功"
fi

# 更简洁写法
command && echo "成功" || echo "失败"

# 捕获错误退出
trap 'echo "第 $LINENO 行出错，退出"; exit 1' ERR
```

### 7.6 实操任务

编写 `check.sh`：检查 Nginx 状态、磁盘使用率、内存余量，输出到日志文件；Nginx 异常时自动重启。

```bash
#!/bin/bash
set -uo pipefail

LOG=/opt/lab/logs/check.log
mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

# 1. Nginx 状态
if systemctl is-active --quiet nginx; then
    log "OK  nginx 运行中"
else
    log "ERR nginx 未运行，尝试重启"
    systemctl start nginx && log "nginx 重启成功" || log "nginx 重启失败"
fi

# 2. 磁盘使用率（根分区）
used=$(df / | awk 'NR==2 {gsub("%","",$5); print $5}')
if [ "$used" -ge 80 ]; then
    log "WARN 根分区使用率 ${used}%"
else
    log "OK   根分区使用率 ${used}%"
fi

# 3. 内存余量
avail=$(free -m | awk '/Mem:/ {print $7}')
if [ "$avail" -lt 200 ]; then
    log "WARN 可用内存仅 ${avail}MB"
else
    log "OK   可用内存 ${avail}MB"
fi
```

```bash
chmod +x check.sh
./check.sh
cat /opt/lab/logs/check.log
```

---

## 八、阶段 6：综合实战项目

### 8.1 项目需求

| 编号 | 需求 | 涉及能力 |
|---|---|---|
| R1 | 部署 2 个静态站点 web1 / web2 | 目录、权限、Nginx |
| R2 | Nginx 通过 `/web1`、`/web2` 分别对外提供访问 | location、root、reload |
| R3 | 编写巡检脚本，服务异常自动拉起 | systemd、Shell |
| R4 | 巡检脚本每 5 分钟自动执行并记录日志 | crontab |
| R5 | 完成 5 个故障演练并记录排查路径 | journalctl、ss、nginx -t |

### 8.2 部署拓扑

```mermaid
graph TB
    U[浏览器 / curl] -->|80 端口| N[Nginx :80]
    N -->|/web1| W1[/opt/lab/site/web1]
    N -->|/web2| W2[/opt/lab/site/web2]
    C[crontab 每5分钟] --> S[check.sh 巡检]
    S -->|异常时| N
    S --> LOG[(/opt/lab/logs/check.log)]
```

### 8.3 目录与文件准备

```bash
mkdir -p /opt/lab/site/web1 /opt/lab/site/web2 /opt/lab/logs /opt/lab/backup
echo '<h1>web1 ok</h1>' > /opt/lab/site/web1/index.html
echo '<h1>web2 ok</h1>' > /opt/lab/site/web2/index.html
chmod -R 755 /opt/lab/site
chmod 644 /opt/lab/site/web*/index.html
```

### 8.4 Nginx 站点配置

Ubuntu 建议放在 `sites-available` 并软链到 `sites-enabled`：

```bash
sudo tee /etc/nginx/sites-available/lab.conf >/dev/null <<'EOF'
server {
    listen 80 default_server;
    server_name _;

    location /web1/ {
        root /opt/lab/site;
        index index.html;
    }

    location /web2/ {
        root /opt/lab/site;
        index index.html;
    }

    location = / {
        return 302 /web1/;
    }
}
EOF

sudo ln -sfn /etc/nginx/sites-available/lab.conf /etc/nginx/sites-enabled/lab.conf
sudo rm -f /etc/nginx/sites-enabled/default      # 避免冲突
sudo nginx -t                                    # 必须先校验
sudo systemctl reload nginx                      # 平滑生效
```

CentOS 用 `/etc/nginx/conf.d/lab.conf`，无需软链接，改完直接 `nginx -t && systemctl reload nginx`。

> 路径映射说明：`root /opt/lab/site` + `location /web1/` ⇒ 请求 `/web1/index.html` 映射到 `/opt/lab/site/web1/index.html`。

### 8.5 验证

```bash
curl -I http://127.0.0.1/web1/
curl -s http://127.0.0.1/web1/ | head -1
curl -s http://127.0.0.1/web2/ | head -1
ss -tulpn | grep :80
```

### 8.6 定时巡检

```bash
crontab -e
# 加入以下行（每 5 分钟执行，日志追加）
*/5 * * * * /opt/lab/check.sh >> /opt/lab/logs/cron.log 2>&1
```

```bash
crontab -l                 # 查看当前任务
sudo systemctl status cron # Ubuntu；CentOS 为 crond
```

> crontab 五大坑：① 用绝对路径 ② 环境变量少，脚本内显式设置 ③ 需要 `2>&1` 捕获错误 ④ 注意末尾换行 ⑤ 分钟字段不是秒。

### 8.7 故障演练清单

| 编号 | 演练动作 | 排查命令序列 | 预期结论 |
|---|---|---|---|
| F1 | 删掉 nginx.conf 一个 `}` | `nginx -t` → `status` → `journalctl -u nginx` | 语法错误，含行号 |
| F2 | 改错站点目录路径 | `curl -I` 返回 404 → `nginx -t` → 查 `error.log` | 404，路径未命中 |
| F3 | `chmod 700` 站点目录 | 访问返回 403 → `ls -ld` → 查 `error.log` | 403，Nginx worker 无读权限 |
| F4 | `systemctl stop nginx` | 访问失败 → `ss -tulpn` 无 80 → `status` | 端口未监听，执行巡检脚本验证自动拉起 |
| F5 | 占用 80 端口 | `ss -tulpn \| grep :80` → `kill` | Address already in use |

```bash
# F3 场景权限修复
sudo chmod 755 /opt/lab/site /opt/lab/site/web1
sudo chown -R www-data:www-data /opt/lab/site/web1
```

---

## 九、排障速查表（症状 → 定位）

| 症状 | 首查命令 | 常见原因 |
|---|---|---|
| 服务访问不通 | `systemctl status <svc>` | 服务未启动、启动失败 |
| 启动即失败 | `journalctl -u <svc> -n 100` | 配置错误、端口冲突、权限不足 |
| `Address already in use` | `ss -tulpn \| grep :<port>` | 旧进程残留、端口被占 |
| 403 Forbidden | `ls -ld <dir>` / `namei -l <path>` | 目录权限不足、SELinux |
| 404 Not Found | `nginx -t`、检查 `root`/`alias` | 路径映射错误、文件不存在 |
| 502 Bad Gateway | `curl -I 后端地址`、`ss -tulpn` | 后端未启动、端口不对 |
| 504 Gateway Timeout | 后端日志、`curl -w %{time_total}` | 后端处理慢、超时配置过短 |
| 磁盘写不进去 | `df -h`、`df -i` | 空间或 inode 耗尽 |
| 系统卡顿 | `uptime`、`top`、`vmstat 1` | 负载高、内存不足、IO 瓶颈 |
| 内存溢出 OOM | `dmesg -T \| grep -i oom` | 进程内存超限、无 swap |
| 日志丢失 | `journalctl --disk-usage`、`logrotate` 配置 | 日志轮转、磁盘满 |

### 通用排障四步法

```mermaid
graph LR
    A[1 现象确认<br/>curl/浏览器] --> B[2 进程与端口<br/>status + ss]
    B --> C[3 日志定位<br/>journalctl + 应用日志]
    C --> D[4 配置与资源<br/>nginx -t + df/top]
```

---

## 十、常用命令速查

| 场景 | 命令 |
|---|---|
| 查端口占用 | `ss -tulpn \| grep :80` |
| 实时看日志 | `tail -F app.log` |
| 看服务日志 | `journalctl -u nginx -f` |
| 校验 Nginx 配置 | `nginx -t` |
| 找大文件 | `du -sh /* \| sort -rh \| head` |
| 找大目录 | `du -h --max-depth=1 /var \| sort -rh` |
| 找进程 | `ps aux \| grep <name>` |
| 杀进程 | `kill <PID>` / `kill -9 <PID>` |
| 看负载 | `uptime` / `nproc` |
| 看内存 | `free -h` |
| 看磁盘 | `df -h` / `df -i` |
| 统计日志 IP | `awk '{print $1}' log \| sort \| uniq -c \| sort -rn` |
| 统计状态码 | `awk '{print $9}' log \| sort \| uniq -c` |
| 测试接口 | `curl -o /dev/null -s -w "%{http_code}\n" URL` |
| 打包备份 | `tar -zcvf xxx.tar.gz /path` |
| 定时任务 | `crontab -e` / `crontab -l` |

---

## 十一、进阶预告：代理与负载均衡

完成阶段 6 后，可直接在同一套环境上叠加：

```nginx
# Nginx 七层负载均衡（配置片段）
upstream backend {
    server 127.0.0.1:8001 weight=1;
    server 127.0.0.1:8002 weight=1;
    # keepalive 32;
}

server {
    listen 8080;
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

| 主题 | 关键点 | 验证方式 |
|---|---|---|
| Nginx 反向代理 | `proxy_pass`、请求头透传 | `curl -I` 看响应头与后端日志 |
| Nginx 负载均衡 | upstream 轮询/权重/ip_hash | 连续 `curl` 观察后端轮换 |
| HAProxy | `balance roundrobin`、健康检查 | 停一个后端观察摘除 |
| Keepalived | VRRP、VIP 漂移、双机高可用 | 停主节点验证 VIP 转移 |
| HTTPS | 证书、`ssl_protocols`、强制跳转 | `curl -vI https://` |

---

## 十二、学习打卡清单

- [ ] 阶段 1：完成站点目录搭建、权限设定、打包备份
- [ ] 阶段 2：能独立完成日志 IP/状态码统计
- [ ] 阶段 3：完成端口冲突定位与进程释放
- [ ] 阶段 4：完成 Nginx 安装、配置校验、故障演练
- [ ] 阶段 4：用 systemd 托管一个自研服务并实现自动重启
- [ ] 阶段 5：写出巡检脚本并通过 shellcheck
- [ ] 阶段 6：完成 web1/web2 双站点部署并对外可访问
- [ ] 阶段 6：完成 F1～F5 五个故障演练，记录排查路径
- [ ] 阶段 6：crontab 定时巡检生效并产生日志
- [ ] 阶段 7：完成 Nginx upstream 双后端负载均衡实验

---

## 附录 A：新手高频坑

| 坑 | 说明 | 正确做法 |
|---|---|---|
| 改配置不校验 | Nginx/Apache 改完直接 reload | 先 `nginx -t` 再 reload |
| reload 与 restart 混用 | restart 会中断连接 | 优先 `reload` |
| 权限一刀切 777 | 安全隐患大 | 目录 755、文件 644 |
| `>` 与 `>>` 搞混 | `>` 会清空文件 | 追加用 `>>` |
| crontab 用相对路径 | 定时任务找不到文件 | 全用绝对路径 |
| `rm -rf $DIR` 变量为空 | 退化为 `rm -rf /` | 加 `set -u` 或用 `${DIR:?}` |
| 只看 `systemctl status` | 信息不全 | 配合 `journalctl -u` |
| 防火墙忘记放行 | 本机 curl 通、外部不通 | 检查 ufw/firewalld/安全组 |

## 附录 B：推荐练习环境

| 类型 | 方案 | 特点 | 适合阶段 |
|---|---|---|---|
| 在线沙箱 | Killercoda / LabEx | 浏览器即开即用，免装环境 | 阶段 1～5 |
| 云主机 | 轻量应用服务器（2C2G 起） | 最贴近真实，可长期保存 | 全阶段 |
| 本地容器 | docker-compose 多节点栈 | 模拟多机内网互通 | 阶段 6～7 |
| K8s 实验 | kind / k3d / minikube | 云原生运维进阶 | 阶段 7 之后 |
| 网络仿真 | EVE-NG | 练 LVS、VRRP、路由 | 负载均衡深入 |

---

> 文档版本：2026-11-13 ｜ 适用系统：Ubuntu 22.04 LTS / CentOS Stream 9
> 使用建议：将本文作为实操对照表，边做边勾选打卡清单，每个报错都记录到自己的排障笔记。

> （注：部分内容由豆包 AI 生成）