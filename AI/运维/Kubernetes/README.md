# Kubernetes（学习笔记）

> 面向：已会 Docker、想补运维广度的全栈。  
> 目标：先建立正确心智模型，再会常用命令与最小部署，再谈进阶。

---

## 建议阅读顺序

```text
01-介绍与核心概念.md          ← 是什么、Node/Pod/容器别搞混
02-基础用法与常用命令.md      ← kubectl、最小 YAML、排障入口
03-单机2C2G轻量机实操教程.md  ← 【动手主线】k3s 安装→部署→排障
```

## 和 Docker 的关系（先记住）

| Docker | Kubernetes |
|--------|------------|
| 单机跑容器 | **多机编排**容器（调度、重启、扩缩、服务发现） |
| `docker run` | 声明式：写 YAML，集群帮你维持期望状态 |
| 容器 | 跑在 **Pod** 里；底层运行时可以是 containerd，不一定叫 Docker |
| **一份 compose 多服务** | **多份 YAML**（每服务 Deployment/Service）；不是把 compose 原样丢进集群 |

业务栈迁移示例：[../Docker/cms-web-stack说明.md](../Docker/cms-web-stack说明.md)（compose 验证 → k3s 拆成 lucky / snsn 各自 YAML）。

## 目录

```text
Kubernetes/
├── README.md
├── 01-介绍与核心概念.md
├── 02-基础用法与常用命令.md
└── 03-单机2C2G轻量机实操教程.md   ← 2C2G 轻量机跟做
```

## 练手环境（一台机器即可）

| 方案 | 适合 |
|------|------|
| **k3s（本教程）** | **2C2G 轻量应用服务器** |
| kind / minikube | 本机已有 Docker、内存更宽裕 |
| 阿里云 ACK | 以后上云再用 |

**2C2G 注意**：内存紧，优先 k3s + 小镜像 + 1 副本；若同机有宝塔/MySQL，建议加 swap 或用干净练机。
