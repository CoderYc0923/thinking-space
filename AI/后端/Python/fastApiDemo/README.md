# 启动
```bash
# 开发启动（热更新）
uvicorn main:app --reload --port 8000

# 生产启动（正式环境）
# `--workers 4`：多进程提升并发，类似前面再挂一层多实例，**不是** SpringBoot 集群本身
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

