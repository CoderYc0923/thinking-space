# cms-web-stack（lucky + SnSn + Nginx）

源码与 Compose：`D:\code-self\cms-web-stack\`（详见该目录 `README.md`）。

## 现网业务模型（以你实际为准）

| 项目 | 是什么 | 现网怎么跑 |
|------|--------|------------|
| **SnSn** | **纯前端静态** | Nginx 直接托管，**无后端服务** |
| **Lucky** | **Node 站点** + **定时脚本** | pm2 跑网站 + cron；不是纯静态 |

> 仓库里 SnSn 虽有 `backend/`，但你当前部署不用它；Compose 已按「无 API」简化。

## 结构怎么理解

```text
cms-web-stack/docker-compose.yml     ← 顶层统一编排
        │
        ├── lucky-lucky/Dockerfile       → lucky（网站）+ lucky-cron（定时）
        └── cms-web-stack/nginx/Dockerfile → nginx（托管 SnSn 静态 + 反代 Lucky）
```

| 角色 | 文件 |
|------|------|
| **总管** | 一份 `docker-compose.yml` |
| **打包** | Lucky 一份 Dockerfile；Nginx 镜像内构建 SnSn 前端 |

## 和 K8s / k3s

```text
k8s/
  lucky.yaml          # Node 网站 Deployment + Service
  lucky-cron.yaml     # 定时
  snsn-web.yaml       # 纯静态（或 Ingress 直接挂静态）
  ingress.yaml        # 域名入口
```

不必再为 SnSn 写 api 的 Deployment（除非以后启用 backend）。

## 落地顺序

1. Compose + `HTTP_PORT=8080` 旁路验证（**先不停** 现网 pm2 / 宝塔站）  
2. 再切流量：停 Lucky 的 pm2；SnSn 只改 Nginx 静态站点  
3. 再迁 k3s（先练 [Kubernetes 教程](../Kubernetes/03-单机2C2G轻量机实操教程.md)）
