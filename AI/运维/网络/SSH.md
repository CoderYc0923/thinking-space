- 本质：安全的远程登录协议，客户端登陆服务器并执行管理操作或服务器之间建立端口转发隧道。
- 能力：
  - 远程登录与命令执行：登录`shell`、执行远程命令、自动化运维
    - 风险点：弱密码、root直连、账户权限过大
  - 公钥/私钥认证：服务器存公钥，客户端持私钥
    - 风险点：私钥泄露、私钥无口令、`authorized_keys`被植入后门（攻击者拿到低权账户后可能植入自己的公钥，形成持久后门；）
  - 用户身份验证：证明正确用户，通常用密码、证书、2FA
    - 风险点：
      - 密码可能被暴力破解、撞库、弱口令
      - 证书、2FA可能配置复杂、CA私钥需要管理
  - 多路复用、跳板：复用连接、经跳板机访问内网
    - 跳板机需要强审计
  - 本地/远程/动态端口转发：`-L -R -D`，也就是常说的`SSH`隧道
    - 风险点：被滥用作跳板、绕过防火墙、暴露内网
  - `SCP/SFTP`：基于`SSH`的安全文件传输
    - 风险点：权限过宽、目录穿透、敏感文件暴露
  - `X11/Agent转发`：图形转发、代理转发
    - 风险点：`Agent`转发可被远程主机借用签名；`X11`转发扩大攻击面
- 常见风险
  - SSH默认监听22端口/TCP，公网服务器上线后，会持续被自动化扫描器探测22端口，并尝试：
    - `root`+常见弱密码暴力破解
    - 用户名字字典枚举
    - 旧版本`SSH`漏洞利用
    - 利用错误配置直接登录
  - **扫描不等于入侵成功，但它是入侵的第一步。** 海量扫描日志还会掩盖真正的攻击行为。修改默认端口能减少“噪音”，但只是辅助手段，不能替代密钥认证、禁用 root 和限制来源 IP。
- 主要风险点：
  - 密码认证+弱口令：最高风险，直接面对暴力破解
  - 允许`root`直接远程登录：最高权限入口暴露，审计差
  - 公网对`0.0.0.0/0`开放`SSH`：扫描面最大；应该限制为固定IP或VPN网段
  - 私钥/公钥管理不当：私钥泄露、无口令、权限过宽、`authorized_keys`后门
  - 端口转发被滥用：`SSH`隧道可绕过防火墙、暴露内网服务，非必要应关闭`AllowTcpForwarding`
  - `Agent`转发风险：远程主机可借用`agent`签名，恶意`root`可劫持
  - 旧版本/弱算法：老`SSH`版本漏洞、弱加密算法、允许废弃协议
  - 配置和权限问题：`.ssh`目录权限过宽、用户权限过大、日志不审计
  - 日志噪音与监控缺失：只看`22`端口扫描日志会淹没真实攻击；需集中审计登录成功/失败、密钥变更
- 措施：
  - 禁用密码登录
  - 禁止`root`直登
  - 网络层限制来源IP
  - 非必要关闭转发
  - 改端口降噪
  - `Fail2ban/日志审计`，自动封禁暴力破解源，监控成功登录和密钥变更
  - 密钥轮换和最小权限，`authorized_keys`定期审计





- 日常命令

  - ```bash
    # 新建用户
    sudo adduser xxx
    # 查看用户
    getent passwd
    # 设/修改密码
    sudo passwd xxxxx
    # 删除用户
    sudo deluser xxx / sudo userdel -r xxx
    
    # 禁止登录
    sudo usermod -s /usr/sbin/nologin xxx
    # 允许登录
    sudo usermod -s /bin/bash xxxx
    
    # 锁账号（不能用密码登录）
    sudo passwd -l xxxx
    # 解锁账号
    sudo passwd -u xxxx
    # 看账号是否锁定
    sudo passwd -S xxxx
    
    # 只允许部分人SSH
    在sshd_config中添加AllowUsers alice xxx后重启sshd
    
    # 加入sudo组（可提权）
    #centos
    sudo usermod -aG 组名 xxxx
    #ubuntu
    sudo usermod -aG sudo xxxx
    # 从组中移除
    sudo gpasswd -d xxx 组名
    # 查看用户所属组
    id xxx
    groups xxx
    
    ```

  - 禁用密码登录，只留密钥

    - ```bash
      # 修改/etc/ssh/sshd_config
      PasswordAuthentication no
      PubkeyAuthentication yes
      # 建议同时
      PermitRootLogin prohibit-password
      # 或完全禁止 root 密码/登录：
      # PermitRootLogin no
      sudo sshd -t
      sudo systemctl restart sshd
      
      # 但是需要先给要用的账号配好公钥
      mkdir -p ~/.ssh
      chmod 700 ~/.ssh
      # 把公钥写入 authorized_keys
      chmod 600 ~/.ssh/authorized_keys
      
      
      ```

    - 

- 修改ssh端口

  - ```bash
    # 在sshd_config修改端口
    sudo vim /etc/ssh/sshd_config
    
    # 修改后，若本机有防火墙，则放行该端口
    #centos
    sudo firewall-cmd --permanent --add-port=xxxx/tcp
    sudo firwall-cmd --reload
    #ubuntu
    sudo ufw allow xxxx/tcp
    sudo ufw reload
    
    # 修改云服务器安全组端口
    
    # 重启SSH
    #centos
    sudo systemctl restart sshd
    #ubuntu
    sudo systemctl restart ssh
    
    # 验证
    sudo ss -tlnp | grep ssh
    # or
    sudo netstat -tlnp | grep ssh
    ```

  - 

