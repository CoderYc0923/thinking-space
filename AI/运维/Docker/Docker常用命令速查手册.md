# Docker 常用命令速查手册

> 适用环境：Linux 轻量应用服务器 + 宝塔面板  
> 编排方式：Docker Compose（三服务：Java / Node.js / 前端）

---

## 目录

1. [镜像管理](#一镜像管理)
2. [容器生命周期](#二容器生命周期)
3. [Docker Compose](#三docker-compose)
4. [数据卷管理](#四数据卷管理)
5. [网络排查](#五网络排查)
6. [日志与调试](#六日志与调试)
7. [清理与维护](#七清理与维护)
8. [实用组合技](#八实用组合技)
9. [工作流对应关系](#九工作流对应关系)
10. [常见问题排查清单](#十常见问题排查清单)

---

## 一、镜像管理

```bash
# 构建镜像（-t 打标签，. 指当前目录的 Dockerfile）
docker build -t my-app:v1 .
docker build --no-cache -t my-app:v2 .   # 不使用缓存，全新构建

# 列出本地镜像
docker images
docker images -a                          # 含中间层镜像

# 拉取 / 推送镜像
docker pull node:22-alpine
docker pull mysql:8.0
docker push my-app:v1

# 查看镜像历史（每层大小和命令）
docker history node:22-alpine

# 给镜像重新打标签
docker tag my-app:v1 my-app:latest
docker tag my-app:v1 registry.example.com/my-app:v1

# 删除镜像（需先删除使用它的容器）
docker rmi my-app:v1
docker rmi -f my-app:v1                   # 强制删除

# 清理无标签的悬空镜像
docker image prune
docker image prune -a                     # 清理所有未使用的镜像

# 导出 / 导入镜像（离线迁移）
docker save -o my-app.tar my-app:v1
docker load -i my-app.tar

# 查看镜像详细信息
docker inspect node:22-alpine
```

---

## 二、容器生命周期

```bash
# ========== 创建与启动 ==========

# 创建并启动容器（-d 后台，--name 命名，-p 端口映射，-v 挂载）
docker run -d --name my-app \
  -p 3000:3000 \
  -v $(pwd)/src:/app/src \
  -e NODE_ENV=production \
  --restart unless-stopped \
  my-app:v1

# 常用 run 参数速查：
# -d              后台运行
# --name          容器名称
# -p 宿主机:容器   端口映射
# -v 宿主机:容器   目录挂载
# -e              设置环境变量
# --restart       重启策略（no/always/on-failure/unless-stopped）
# --network       指定网络
# --memory="512m" 内存限制
# --cpus="1.0"    CPU 限制

# ========== 查看容器 ==========

docker ps                                # 运行中的容器
docker ps -a                             # 所有容器（含已停止）
docker ps -q                             # 只显示容器 ID
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ========== 启停控制 ==========

docker stop my-app                       # 优雅停止（SIGTERM，10秒超时后 SIGKILL）
docker stop -t 30 my-app                 # 30 秒超时
docker start my-app                      # 启动已停止的容器
docker restart my-app                    # 重启
docker pause my-app                      # 暂停进程（不释放内存）
docker unpause my-app                    # 恢复

# ========== 删除容器 ==========

docker rm my-app                         # 删除已停止的容器
docker rm -f my-app                      # 强制删除运行中的容器
docker rm $(docker ps -aq)               # 删除所有容器（危险）

# ========== 进入容器 ==========

docker exec -it my-app sh               # Alpine 用 sh
docker exec -it my-app bash             # Debian/Ubuntu 用 bash
docker exec -it my-app /bin/sh          # 通用写法
docker exec my-app ls /app              # 执行单条命令不进入

# 以 root 用户进入（当镜像默认非 root 时）
docker exec -it -u root my-app sh

# ========== 文件操作 ==========

docker cp my-app:/app/logs ./logs       # 容器 → 宿主机
docker cp ./config.json my-app:/app/    # 宿主机 → 容器

# ========== 查看容器详情 ==========

docker inspect my-app                   # JSON 格式完整信息
docker inspect my-app | grep IPAddress  # 查容器 IP
docker inspect -f '{{.State.Status}}' my-app  # 格式化提取字段
docker port my-app                      # 查看端口映射
docker stats my-app                     # 实时资源使用（CPU/内存/网络）
docker top my-app                       # 容器内进程列表

# ========== 提交容器为镜像 ==========

docker commit my-app my-app:v2          # 保存容器当前状态为新镜像
docker commit -m "描述" my-app my-app:v2
```

---

## 三、Docker Compose

```bash
# ========== 启动与构建 ==========

docker compose up -d                    # 后台启动所有服务
docker compose up -d --build            # 重新构建并启动
docker compose up -d --build --force-recreate  # 强制重建容器

# ========== 停止与删除 ==========

docker compose down                     # 停止并删除容器/网络
docker compose down -v                  # 同时删除数据卷（注意数据丢失！）
docker compose down --rmi all           # 同时删除镜像
docker compose stop                     # 仅停止（保留容器）

# ========== 查看状态 ==========

docker compose ps                       # 项目中的容器列表
docker compose ps -a                    # 含已停止
docker compose top                      # 各容器进程

# ========== 日志 ==========

docker compose logs -f                  # 所有服务日志（实时跟踪）
docker compose logs -f backend          # 只看 backend 服务
docker compose logs --tail=100 backend  # 末尾 100 行

# ========== 服务控制 ==========

docker compose restart backend          # 重启单个服务
docker compose stop backend             # 停止单个服务
docker compose start backend            # 启动单个服务
docker compose exec backend sh          # 进入服务容器
docker compose run --rm backend npm test  # 临时运行命令（用完即删）

# ========== 构建相关 ==========

docker compose build                    # 构建所有服务镜像
docker compose build --no-cache         # 无缓存构建
docker compose build backend            # 只构建指定服务

# ========== 查看配置 ==========

docker compose config                   # 验证并显示最终配置
docker compose config --services        # 列出所有服务名
docker compose images                   # 项目使用的镜像列表
```

### Compose 文件示例（docker-compose.yml）

```yaml
version: "3.8"
services:
  backend:
    build: ./backend
    container_name: my-backend
    ports:
      - "8080:8080"
    volumes:
      - ./backend/src:/app/src          # 开发时挂载源码，热重载
      - backend_data:/app/data          # named volume 持久化
    environment:
      - DB_HOST=mysql                   # 用服务名通信，非 localhost
      - DB_PORT=3306
    depends_on:
      mysql:
        condition: service_healthy
    networks:
      - app-network

  mysql:
    image: mysql:8.0
    container_name: my-mysql
    volumes:
      - mysql_data:/var/lib/mysql       # 数据库数据持久化
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
    healthcheck:                         # 健康检查
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

volumes:
  mysql_data:
  backend_data:

networks:
  app-network:
    driver: bridge
```

---

## 四、数据卷管理

### Volume vs Bind Mount 对比

| 特性 | Named Volume | Bind Mount |
|------|-------------|------------|
| 命令 | `-v volume_name:/path` | `-v /host/path:/container/path` |
| 管理 | Docker 管理 | 宿主机管理 |
| 路径 | `/var/lib/docker/volumes/` | 任意宿主机路径 |
| 场景 | 数据库持久化、生产环境 | 开发时挂载源码 |

### Volume 命令

```bash
# ========== 创建与查看 ==========

docker volume create mysql_data          # 创建 named volume
docker volume ls                         # 列出所有 volume
docker volume inspect mysql_data         # 查看 volume 详情（含挂载点路径）

# ========== 使用 Volume ==========

# 创建容器时指定
docker run -d -v mysql_data:/var/lib/mysql mysql:8.0

# 只读挂载
docker run -d -v mysql_data:/var/lib/mysql:ro mysql:8.0

# 使用 --mount 语法（更明确）
docker run -d \
  --mount source=mysql_data,target=/var/lib/mysql \
  mysql:8.0

# ========== 备份与迁移 ==========

# 备份 volume 数据
docker run --rm \
  -v mysql_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/mysql_backup.tar.gz -C /data .

# 恢复 volume 数据
docker run --rm \
  -v mysql_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/mysql_backup.tar.gz -C /data

# 克隆 volume（从旧 volume 创建新 volume）
docker volume create mysql_data_new
docker run --rm \
  -v mysql_data:/from \
  -v mysql_data_new:/to \
  alpine cp -a /from/. /to/

# ========== 清理 ==========

docker volume rm mysql_data              # 删除指定 volume
docker volume rm $(docker volume ls -q)  # 删除所有 volume（危险！）
docker volume prune                      # 删除未使用的 volume
docker volume prune -a                   # 删除所有未使用的 volume
```

### 在 Compose 中使用 Volume

```yaml
# 声明顶层 volume（可多个服务共用）
volumes:
  mysql_data:
    driver: local
  shared_logs:
    driver: local

services:
  mysql:
    volumes:
      - mysql_data:/var/lib/mysql        # named volume
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql  # bind mount
```

---

## 五、网络排查

### 网络基础命令

```bash
# ========== 查看网络 ==========

docker network ls                        # 列出所有网络
docker network inspect bridge            # 查看网络详情（含连接的容器）
docker network inspect app-network | grep -A 5 "Containers"

# ========== 创建与删除网络 ==========

docker network create my-network         # 创建 bridge 网络
docker network create --driver overlay my-overlay  # Swarm 用 overlay
docker network rm my-network             # 删除网络
docker network prune                     # 清理未使用的网络

# ========== 连接与断开 ==========

docker network connect my-network my-app      # 将运行中的容器加入网络
docker network disconnect my-network my-app   # 断开连接

# ========== 容器 DNS 排查 ==========

# 进入容器测试网络连通性
docker exec -it backend sh
ping mysql                                # 直接用 Compose 服务名 ping
nslookup mysql                            # DNS 解析测试
wget -O- http://mysql:3306                # 端口连通测试

# 在宿主机上运行临时容器做网络诊断
docker run --rm -it --network app-network alpine sh
# 然后在这个容器里 ping、curl、nslookup 等

# 查看容器 DNS 配置
docker exec backend cat /etc/resolv.conf

# ========== 端口与连通性排查 ==========

# 宿主机上看端口占用
netstat -tlnp | grep 8080
ss -tlnp | grep 8080

# 测试宿主机到容器的端口
telnet localhost 8080
curl localhost:8080/api/health

# 查看容器端口映射
docker port backend
docker inspect backend | grep -A 10 Ports

# ========== iptables 规则查看 ==========

# Docker 自动管理 iptables，一般不用手动改
iptables -t nat -L -n | grep DOCKER
```

### 常见网络问题排查流程

```
容器 A 无法连接容器 B：
1. docker network inspect <网络名> → 确认两个容器都在同一网络
2. docker exec -it A ping B → 测试 DNS 解析和 ICMP 通断
3. docker exec -it A nslookup B → 检查 DNS 是否正常解析
4. docker exec -it A wget -O- http://B:端口 → 测试 TCP 端口连通
5. docker logs B → 查看 B 是否正常启动监听

外部无法访问容器：
1. docker ps → 确认端口映射是否正确
2. netstat -tlnp → 确认宿主机端口是否被监听
3. 检查云服务器安全组/防火墙规则
4. curl localhost:端口 → 先从本机测试
```

### Compose 网络说明

- Compose 默认创建一个 `项目名_default` 的 bridge 网络
- 所有服务自动加入该网络，可用 **服务名** 互相通信
- **不能用 localhost / 127.0.0.1**，因为它们指向各自容器内部
- 数据库连接字符串示例：`mysql://root:pass@mysql:3306/dbname`

---

## 六、日志与调试

```bash
# ========== 日志查看 ==========

docker logs my-app                       # 查看全部日志
docker logs -f my-app                    # 实时跟踪（Ctrl+C 退出）
docker logs --tail 50 my-app             # 末尾 50 行
docker logs --since 10m my-app           # 最近 10 分钟
docker logs --since 2026-01-01T00:00:00 my-app  # 从指定时间开始
docker logs -t my-app                    # 带时间戳
docker logs my-app 2>&1 | grep ERROR    # 过滤错误日志

# ========== 容器诊断 ==========

docker stats                             # 所有容器实时资源使用
docker stats --no-stream                 # 一次性输出（不持续刷新）
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

docker top my-app                        # 容器内进程列表
docker exec my-app ps aux               # 同上，更详细

# 查看容器文件系统变化
docker diff my-app

# 实时查看容器内文件
docker exec my-app tail -f /app/logs/app.log

# 导出容器文件系统（排查用）
docker export my-app -o my-app.tar      # 导出为 tar（不含卷数据）
```

---

## 七、清理与维护

```bash
# ========== 一键清理 ==========

# 查看 Docker 磁盘使用情况
docker system df
docker system df -v                       # 详细（每个对象的大小）

# 清理：停止的容器 + 无用网络 + 悬空镜像 + 构建缓存
docker system prune
docker system prune -a                    # 更彻底（含所有未使用的镜像）
docker system prune -a --volumes          # 连未使用的 volume 一起清

# ========== 分类清理 ==========

docker container prune                    # 删除所有停止的容器
docker image prune                        # 删除悬空镜像
docker image prune -a                     # 删除所有未使用的镜像
docker volume prune                       # 删除未使用的 volume
docker network prune                      # 删除未使用的网络
docker builder prune                      # 清理构建缓存

# ========== 危险操作（慎用） ==========

# 删除所有容器
docker rm -f $(docker ps -aq)

# 删除所有镜像
docker rmi -f $(docker images -q)

# 停止所有容器
docker stop $(docker ps -q)
```

---

## 八、实用组合技

```bash
# ========== 容器批量操作 ==========

# 一键停止并删除所有容器
docker stop $(docker ps -q) && docker rm $(docker ps -aq)

# 按名称过滤进入容器
docker exec -it $(docker ps -q --filter name=backend) sh

# 查看所有容器的实时资源
docker stats --no-stream $(docker ps -q)

# ========== 日志批量查看 ==========

# 查看所有容器的错误日志（最后 20 行）
docker ps -q | xargs -I {} docker logs --tail 20 {} 2>&1 | grep -i error

# ========== 开发快速迭代 ==========

# 仅重建并重启单个服务
docker compose up -d --build --force-recreate backend

# 进入后端容器跑测试
docker compose exec backend npm test

# ========== 数据库操作 ==========

# 快速导出数据库
docker exec mysql mysqldump -uroot -prootpass dbname > backup.sql

# 快速导入数据库
docker exec -i mysql mysql -uroot -prootpass dbname < backup.sql

# ========== 磁盘空间分析 ==========

# 找出占用空间最大的镜像
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | sort -k3 -h

# 查看某个容器的实时日志+资源
watch -n 1 'docker stats --no-stream backend && docker logs --tail 5 backend'

# ========== 容器信息快速查看 ==========

# 自定义格式化查看
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}"

# 查看容器的 IP 和端口
docker inspect --format='{{.Name}} - {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps -q)
```

---

## 九、工作流对应关系

| Docker 工作流步骤 | 涉及的关键命令 |
|---|---|
| 1. 整理现有数据库容器 | `docker ps -a`、`docker inspect`、`docker volume ls` |
| 2. 创建 docker-compose.yml | `docker compose config`（验证配置） |
| 3. 写 Dockerfile | `docker build`、`docker history` |
| 4. 迁移旧数据 | `docker cp`、`docker volume` 备份恢复、`mysqldump` |
| 5. 启动验证 | `docker compose up -d --build`、`docker compose logs -f` |
| 6. 日常开发 | `docker compose restart`、`docker compose exec`、`docker compose logs` |

### 关键原则回顾

- **容器间通信**：用 Compose 服务名，不用 `localhost`
- **数据持久化**：数据库用 named volume，开发源码用 bind mount
- **镜像选择**：Node 用 `node:22-alpine`（主版本号），前端生产用 `nginx:alpine`
- **构建加速**：先 COPY `package*.json` → `npm ci` → 再 COPY 源码
- **开发体验**：挂载源码目录 + nodemon 热重载，避免反复构建

---

## 十、常见问题排查清单

| 问题现象 | 排查命令 | 可能原因 |
|---|---|---|
| 容器无法启动 | `docker logs my-app` | 环境变量缺失、端口冲突、启动脚本报错 |
| 容器间无法通信 | `docker network inspect`、`ping 服务名` | 不在同一网络、用了 localhost |
| 端口被占用 | `netstat -tlnp \| grep 端口` | 宿主机端口冲突 |
| 数据库数据丢失 | `docker volume ls` | 未挂载 volume，容器删除后数据消失 |
| 磁盘空间不足 | `docker system df` | 大量旧镜像/容器/构建缓存 |
| 容器反复重启 | `docker logs --tail 20 my-app` | 健康检查失败、应用崩溃 |
| 修改代码未生效 | `docker compose ps` | 源码未挂载、容器未重启 |

---

> **最后更新**：2026-07-07  
> **适用环境**：Linux 轻量应用服务器 + Docker + Docker Compose + 宝塔面板
