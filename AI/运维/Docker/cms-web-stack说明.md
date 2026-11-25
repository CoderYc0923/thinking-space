# cms-web-stack（lucky + SnSn + Nginx）

源码与 Compose 在：`D:\code-self\cms-web-stack\`（详见该目录 `README.md`）。

## 结构怎么理解

```text
cms-web-stack/docker-compose.yml     ← 顶层统一编排（多服务）
        │
        ├── lucky-lucky/Dockerfile       → 镜像 → lucky / lucky-cron
        ├── SnSn/backend/Dockerfile      → 镜像 → snsn-api
        └── cms-web-stack/nginx/Dockerfile → 镜像 → nginx（含 SnSn 前端）
```

| 角色 | 文件 |
|------|------|
| **总管** | 一份 `docker-compose.yml` 管理所有服务 |
| **各服务打包** | 各自一份 `Dockerfile` 打镜像 |

日常在 `cms-web-stack` 下：`docker compose up -d --build`。

## 和 K8s / k3s 怎么接

- 真实 K8s **不是** 一份 compose，而是 **多份 YAML**（Deployment / Service 等）。  
- 当前拆法就是为迁 k3s 铺路：**镜像保留，编排换成各服务自己的 YAML**。  
- Compose 负责单机验证；上 k3s 后建议例如：

```text
k8s/
  lucky.yaml          # Deployment + Service
  lucky-cron.yaml
  snsn-api.yaml
  snsn-web.yaml       # 静态；或并入 Ingress
  ingress.yaml        # 域名入口（可替代自建 nginx 容器）
```

对应关系：Compose 里一个 `service` ≈ K8s 里一组清单；**不是**把整份 compose 丢进集群。

## 落地顺序

1. Compose + `HTTP_PORT=8080` 旁路验证  
2. 再切现网（停 pm2 / 原 nginx 站点）  
3. 有余力再迁 k3s（先练 [Kubernetes 教程](../Kubernetes/03-单机2C2G轻量机实操教程.md)）
