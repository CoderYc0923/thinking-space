| 命令              | 作用                   |      |
| ----------------- | ---------------------- | ---- |
| `nginx -t`        | 检查配置               |      |
| `nginx -T`        | 打印实际加载的完整配置 |      |
| `nginx -s reload` | 平滑重载配置           |      |
| `nginx -s stop`   | 快速停止               |      |
| `nginx -s quit`   | 优雅退出               |      |
| `nginx -v`        | 版本                   |      |
| `nginx -V`        | 版本+编译参数          |      |



- systemd常见

  - ```bash
    systemctl status nginx # 查看状态
    systemctl reload nginx # 重载
    systemctl restart nginx # 重启
    ```

- 改配置顺序

  - ```bash
    # 改完conf后，先检查配置再平滑重载
    nginx -t && nginx -s reload
    ```



- 整体结构

  - ```bash
    # 全局（main）
    worker_processes auto;
    
    events {
        worker_connections 1024;
    }
    
    http {
        # 全站共用：日志、限流、map、upstream …
    
        server {                 # 一个站点（一个域名/端口）
            listen 443 ssl;
            server_name api.xxx.com;
    
            location /v1/ {      # 路径规则
                proxy_pass http://后端;
            }
        }
    }
    ```

  - `main`：进程数、用户、错误日志路径等

  - `events`：连接相关

  - `http`：Web/反代总开关；限流区、`map`、`upstream`，多个`server`

  - `server`：一个虚拟主机（域名+端口）

  - `location`：某个路径怎么处理（反代、静态、返回码）

- 常用指令含义

  - 站点 / 监听
    - `listen 80 / 443 ssl`：监听端口；`ssl`代表https
    - `server_name a.com`：这个`server`匹配哪些域名
    - `ssl_certificate / ssl_certificate_key`：证书和私钥
    - `return 301 https://...`：直接跳转
  - 路径
    - `location /`：匹配路径（还有 `=` 精确、`^~` 优先前缀、`~` 正则）
    - `root / alias`：静态文件目录
    - `try_files`：依次试文件，常用于前端 SPA
    - `return 404`：直接返回状态码
  - 反向代理
    - `proxy_pass http://host:port`：转发到上游
    - `proxy_set_header Host $host`：把浏览器 Host 传给后端
    - `proxy_set_header X-Real-IP` / `X-Forwarded-For`：传递真实客户端 IP
    - `proxy_set_header X-Forwarded-Proto`：告诉后端原来是 http 还是 https
    - `proxy_http_version 1.1`：用 HTTP/1.1（长连接/部分流式需要）
    - `proxy_read_timeout`：等上游响应多久
    - `proxy_buffering on/off`：是否缓冲上游响应（流式常 off）
  - 上游池（蓝绿 / 负载）
    - `upstream 名字 { server a:3100; }`：定义后端池
    - `proxy_pass http://名字`：转到这个池
  - 变量 / 映射
    - `map $a $b { ... }`：根据 `$a` 算出新变量 `$b`（做路由、CORS、脱敏等）
    - `set $x value`：设一个变量
  - 限流 / 安全
    - `limit_req_zone` / `limit_req`：按 IP 等限请求速率
    - `limit_conn`：限制并发连接
    - `auth_basic` / `auth_basic_user_file`：HTTP Basic 认证
    - `add_header`：加响应头（如 HSTS）
  - 日志
    - `log_format`：自定义日志格式
    - `access_log` / `error_log`：访问日志 / 错误日志