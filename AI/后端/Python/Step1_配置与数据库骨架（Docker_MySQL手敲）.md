# Step 1：配置与数据库骨架（手敲版）

> 承接主教程：[FastAPI 后台管理实战教程（登录JWT_用户CRUD_秒杀Redis_MySQL）](./FastAPI%20后台管理实战教程（登录JWT_用户CRUD_秒杀Redis_MySQL）.md)  
> 项目目录：`fastApiDemo`  
> 本步目标：**Docker Compose 起 MySQL → 配置/连接 → 手写 SQL 建表 → ORM 只做映射 → Alembic 按版本执行 SQL**  
> 教学标准：**生产向 Demo**（DDL 人写人审，应用启动不改表）  
> JWT、登录、用户 CRUD **先不做**（留给 Step 2 / 3）

---

## 0. 本步要交付什么

完成后你应有：

| 项 | 说明 |
|---|---|
| `docker-compose.yml` | 本地 MySQL |
| `.env` + `core/config.py` + `core/database.py` | 配置与连接（不含建表） |
| `sql/*.sql` | **手写 DDL**（表结构真相来源之一） |
| ORM Entity | **只做映射**，对齐手写 SQL，不做自动建表 |
| Alembic | 把 SQL **按版本执行**（对标 Flyway），已 `upgrade head` |
| `main.py` | 不建表、不做库连通健康检查（连通在 Step 2/3 业务接口里自然验证） |

### 0.1 职责怎么拆（先建立正确心智）

| 层级 | 干什么 | 不干什么 |
|---|---|---|
| 手写 SQL（`sql/` + 迁移里的 SQL） | 建表、改表、索引 | 不管业务增删改查 |
| SQLAlchemy Entity | 对象 ↔ 表字段映射，供 Session 读写 | **不**在启动时自动改库 |
| Alembic | 记录「执行过哪些 SQL」、按序 upgrade/downgrade | 不替代你写 DDL；**本教程默认不用 autogenerate** |

和 Java 对照：

| Java | 本教程 |
|---|---|
| MyBatis / JPA 映射 | SQLAlchemy `UserEntity` |
| 手写 `V1__xxx.sql` + Flyway 执行 | 手写 SQL + **Alembic 执行** |
| `ddl-auto` / 运行时建表 | **禁止**（含 `create_all`） |

### 0.2 为什么不用「自动生成表」当主路径

| 做法 | 评价 |
|---|---|
| `create_all` 启动建表 | 无版本、难改表、多实例危险 → **禁用** |
| `alembic revision --autogenerate` 盲跑 | 像「工具猜 DDL」，漏审会误伤 → **本教程不作默认** |
| **手写 SQL → 塞进 Alembic → upgrade** | 你可控 + 有版本历史 → **推荐（生产向）** |

**硬性约定：**

1. DDL 先自己写清楚，再让 Alembic 执行（可先写在 `sql/`，再贴进迁移）  
2. 改 Entity 时 **同步改 SQL/迁移**，两边字段对齐  
3. `main.py` 禁止 `create_all`  
4. 发布顺序：`alembic upgrade head` → 再启应用  

> 以后若用 autogenerate，也只能当「草稿」，必须人工改完再 upgrade——和本教程精神一致，但不作为入门主流程。

---

## 1. 前置检查

在 `fastApiDemo` 目录确认：

```bash
cd D:\code-self\thinking-space\AI\后端\Python\fastApiDemo
poetry --version
poetry show sqlalchemy pymysql pydantic-settings
```

若缺依赖，再装一次：

```bash
poetry add sqlalchemy pymysql cryptography pydantic-settings alembic
```

本机已安装并打开 **Docker Desktop**（托盘图标为 Running）。

---

## 2. 用 Docker Compose 启动 MySQL

比单条 `docker run` 更适合项目：配置写在文件里、可复现、以后加 Redis 只需再加一个 service。

Docker Desktop 自带 Compose V2，命令是 **`docker compose`**（中间有空格）。

### 2.1 手敲 `docker-compose.yml`

路径：`fastApiDemo/docker-compose.yml`

```yaml
services:
  mysql:
    image: mysql:8.0
    container_name: fastapi-mysql
    restart: unless-stopped
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: root123456
      MYSQL_DATABASE: fastapi_demo
    volumes:
      # 数据落盘，容器删了库还在（开发环境省心）
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "127.0.0.1", "-uroot", "-proot123456"]
      interval: 5s
      timeout: 5s
      retries: 20

volumes:
  mysql_data:
```

字段对照：

| Compose 配置 | 含义 |
|---|---|
| `services.mysql` | 一个服务，名字叫 `mysql` |
| `image: mysql:8.0` | 用官方 MySQL 8 镜像 |
| `container_name` | 固定容器名，方便 `docker exec` |
| `ports: "3306:3306"` | 本机 3306 → 容器 3306 |
| `MYSQL_ROOT_PASSWORD` | root 密码（后面 `.env` 要一致） |
| `MYSQL_DATABASE` | 首次启动自动建库 |
| `volumes` | 数据持久化 |
| `healthcheck` | 探测 MySQL 是否就绪 |

若本机 3306 已被占用，改成 `"3307:3306"`，则应用连接写成 `127.0.0.1:3307`。

> 密码仅用于本地 Demo。以后可改成读写 `.env` / Compose 变量，避免明文进仓库。

### 2.2 启动与常用命令

在 `fastApiDemo` 目录执行：

```powershell
cd D:\code-self\thinking-space\AI\后端\Python\fastApiDemo

# 后台启动（首次会拉镜像）
docker compose up -d

# 看状态（mysql 的 STATE 应为 running，健康检查通过后 HEALTHY）
docker compose ps

# 看日志（首次初始化约 20～60 秒）
docker compose logs -f mysql
```

看到类似 `ready for connections` 后按 `Ctrl+C` 退出跟随（容器继续在跑）。

常用命令：

```powershell
docker compose up -d          # 启动
docker compose stop           # 停止（数据还在 volume 里）
docker compose start          # 再次启动
docker compose down           # 停掉并删除容器（默认保留 named volume）
docker compose down -v        # 连数据卷一起删（慎用，库会清空）
docker compose ps             # 当前 compose 服务状态
```

进库（两种写法等价）：

```powershell
# 按容器名
docker exec -it fastapi-mysql mysql -uroot -proot123456

# 或按 compose 服务名
docker compose exec mysql mysql -uroot -proot123456
```

### 2.3 确认库已创建

```powershell
docker compose exec mysql mysql -uroot -proot123456 -e "SHOW DATABASES;"
```

应能看到 `fastapi_demo`。若没有（极少情况），手动建：

```sql
CREATE DATABASE fastapi_demo DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2.4（可选）以前用过 `docker run`？

若本机已有同名容器 `fastapi-mysql`，先清掉再走 Compose，避免名字冲突：

```powershell
docker rm -f fastapi-mysql
```

---

## 3. 本步文件清单（先建空目录/空文件）

在 `fastApiDemo` 下最终应类似：

```text
fastApiDemo/
├── docker-compose.yml
├── .env
├── .gitignore
├── sql/                      # 手写 DDL（便于阅读/评审）
│   └── V001__create_sys_user.sql
├── alembic.ini
├── alembic/
│   ├── env.py                # 注入 MYSQL_URL
│   └── versions/             # 迁移：里面贴你手写的 SQL（要提交）
├── main.py                   # 只健康检查，不建表
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── database.py
└── db_models/                # ORM 映射（与 Pydantic DTO 分开更佳）
    ├── __init__.py
    └── user.py
```

> Entity 若暂放 `models/user.py` 也可以；建议尽快与接口 DTO 分目录。

PowerShell：

```powershell
cd D:\code-self\thinking-space\AI\后端\Python\fastApiDemo
New-Item -ItemType Directory -Force -Path core, db_models, sql | Out-Null
New-Item -ItemType File -Force -Path core\__init__.py, db_models\__init__.py, docker-compose.yml, sql\V001__create_sys_user.sql | Out-Null
```

`.gitignore`：

```gitignore
.env
.venv/
__pycache__/
*.pyc
.idea/
.vscode/
```

> `sql/` 与 `alembic/versions/*.py` **都要提交**。

---

## 4. 手敲 `.env`

路径：`fastApiDemo/.env`

```env
APP_NAME=fastApiDemo

# Docker MySQL：用户 root，密码与 docker run 时一致
MYSQL_URL=mysql+pymysql://root:root123456@127.0.0.1:3306/fastapi_demo?charset=utf8mb4

# Step 4 才用到 Redis，先占位
REDIS_URL=redis://127.0.0.1:6379/0

# Step 2 才用到 JWT，先写好
JWT_SECRET=dev-only-change-me-to-a-long-random-string-32+
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120
```

注意：

1. URL 里是 **`mysql+pymysql://`**，不是 `jdbc:mysql://`
2. 密码若含特殊字符（如 `@ #`），要做 URL 编码，本教程示例用简单密码避免踩坑
3. 端口若改成 3307，这里同步改

---

## 5. 手敲 `core/config.py`

对标 Spring 的 `@ConfigurationProperties`。

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从 .env 读取配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "fastApiDemo"
    MYSQL_URL: str
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120


settings = Settings()
```

自测（可选）：

```powershell
poetry run python -c "from core.config import settings; print(settings.APP_NAME, settings.MYSQL_URL)"
```

能打印出配置即成功。

---

## 6. 手敲 `core/database.py`

对标 DataSource + 每请求一个 Session。

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings

# pool_pre_ping：连接被 MySQL 断开后自动探测重连（开发环境很有用）
engine = create_engine(
    settings.MYSQL_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """所有 ORM Entity 的基类"""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Depends 用：请求进来拿 Session，结束关闭。
    类似：try { SqlSession } finally { close }
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 7. 先手写 SQL（DDL 真相）

路径示例：`sql/V001__create_sys_user.sql`  
（命名风格对标 Flyway：`V序号__说明.sql`，方便以后对照。）

```sql
CREATE TABLE IF NOT EXISTS sys_user (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  username     VARCHAR(50)  NOT NULL,
  password     VARCHAR(255) NOT NULL COMMENT 'bcrypt哈希，禁止明文',
  nickname     VARCHAR(50)  NULL,
  age          INT          NULL,
  email        VARCHAR(100) NULL,
  phone        VARCHAR(20)  NULL,
  status       TINYINT      NOT NULL DEFAULT 1 COMMENT '1启用 0禁用',
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at   DATETIME     NULL,
  UNIQUE KEY uk_sys_user_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
```

字段按你业务增减，但 **SQL 与下一节 Entity 必须一致**。

> 可以临时用客户端执行验证 SQL，但正式流程仍应走第 9 节 Alembic，避免「只在自己电脑建过表」。

---

## 8. 再写 ORM Entity（只映射，不建表）

Entity = 映射层（类似 MyBatis/JPA 映射），**不负责执行上面的 DDL**。

推荐：`db_models/user.py`（与接口 DTO 分开）。你若已写在 `models/user.py`，保持字段与 SQL 对齐即可。

```python
from datetime import datetime

from sqlalchemy import DateTime, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class UserEntity(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

CRUD 放到 Step 3；本步 Entity 只要和 SQL 对得上。

---

## 9. 用 Alembic「执行」你手写的 SQL（不是自动生成表）

Alembic ≈ Flyway：**版本化地执行你审过的 DDL**。  
本教程默认流程：

```text
手写 sql/V001__....sql
  → alembic revision -m "..."（生成空脚本，不要加 --autogenerate）
  → 把 SQL 贴进 upgrade()/downgrade()
  → alembic upgrade head
```

### 9.1 安装并初始化

```powershell
cd D:\code-self\thinking-space\AI\后端\Python\fastApiDemo
poetry add alembic
poetry run alembic init alembic
```

### 9.2 改 `alembic/env.py`：只注入数据库 URL

手写迁移不依赖 autogenerate，**不必**为了建表去 import Entity / 设置 `Base.metadata`（可保持 `target_metadata = None`）。

在 `env.py` 合适位置加上：

```python
from core.config import settings

# 覆盖 ini 里的 url，密码只放 .env
config.set_main_option("sqlalchemy.url", settings.MYSQL_URL)
```

`alembic.ini` 里的 `sqlalchemy.url` 不要提交真实密码。

### 9.3 生成「空」迁移，再手填 SQL

```powershell
# 注意：不要加 --autogenerate
poetry run alembic revision -m "create sys_user"
```

会在 `alembic/versions/` 生成类似 `xxxx_create_sys_user.py`。编辑为：

```python
"""create sys_user

Revision ID: xxxx
...
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "xxxx"          # 保持生成值
down_revision = None       # 首个迁移通常是 None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 与 sql/V001__create_sys_user.sql 保持一致（可复制粘贴）
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sys_user (
          id           BIGINT PRIMARY KEY AUTO_INCREMENT,
          username     VARCHAR(50)  NOT NULL,
          password     VARCHAR(255) NOT NULL COMMENT 'bcrypt哈希，禁止明文',
          nickname     VARCHAR(50)  NULL,
          age          INT          NULL,
          email        VARCHAR(100) NULL,
          phone        VARCHAR(20)  NULL,
          status       TINYINT      NOT NULL DEFAULT 1 COMMENT '1启用 0禁用',
          created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          deleted_at   DATETIME     NULL,
          UNIQUE KEY uk_sys_user_username (username)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sys_user")
```

然后执行：

```powershell
poetry run alembic upgrade head
```

常用命令：

```powershell
poetry run alembic current
poetry run alembic history
poetry run alembic upgrade head
poetry run alembic downgrade -1    # 回退一步，生产慎用
```

发布习惯：

```text
合并代码 → 发布机 alembic upgrade head → 再启动应用
```

### 9.4 以后改表怎么做

1. 先改 `sql/` 里新文件或变更说明（如 `V002__add_xxx.sql`）  
2. `alembic revision -m "add xxx"`，在 `upgrade()` 里贴 `ALTER TABLE ...`  
3. **同步改 Entity 字段**  
4. `alembic upgrade head`  

`sql/` 方便人读；**线上以 `alembic/versions` 实际执行过的为准**。两处 SQL 保持同内容，避免漂移。

### 9.5（了解即可）为何不把 autogenerate 当主路径

`--autogenerate` 会对比 ORM 与数据库「猜」DDL，容易在重命名、删列、索引上出错。  
本教程坚持：**SQL 你写，Alembic 只负责按版本跑**。

---

## 10. 改 `main.py`：不建表、不加健康检查

删掉 `create_all` 以及为空的 startup 建表逻辑即可。  
本教程**不要求**写 `/health/db`；库连通到 Step 2/3 做登录、CRUD 时自然验证。

保留原有路由、CORS、全局异常即可，例如：

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from routers import user
from utils.response import Result

app = FastAPI(title="demo", description="this is a demo api", version="1.0.0")
app.include_router(user.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:xxxx"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ……全局异常处理保持不变……
```

---

## 11. 启动与验收

```powershell
cd D:\code-self\thinking-space\AI\后端\Python\fastApiDemo
docker compose ps
poetry run alembic upgrade head
poetry run alembic current
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

验收以**库表**为准（不必写健康检查接口）：

```powershell
# 库名/密码按你的 compose 修改
docker compose exec mysql mysql -uroot -proot123456 -e "SHOW TABLES; DESC sys_user;"
```

应能看到 `sys_user`（若走了 Alembic，还应有 `alembic_version`）。应用能正常打开 `/docs` 即可。

---

## 12. 常见报错速查

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 连不上 MySQL | 容器未就绪 | `docker compose up -d` + 看 logs |
| 无 `sys_user` | 没 upgrade / 迁移里 SQL 有误 | 查 versions 脚本后重新 `upgrade head` |
| Entity 报错列不存在 | SQL 与映射字段不一致 | 对齐两边字段后再迁 |
| `No module named 'core'` | 目录不对 | 在 `fastApiDemo` 根目录执行 |
| 误用 `--autogenerate` | 与本教程主路径不符 | 改用手写 `revision` + 贴 SQL |
| 启动时改表 | 写了 `create_all` | 删掉 |

---

## 13. Step 1 完成检查清单

- [ ] MySQL 已用 Compose 跑起来  
- [ ] `.env` / `config` / `database` 就绪  
- [ ] 已手写 `sql/` 下的建表脚本  
- [ ] Entity 字段与 SQL 一致（只映射）  
- [ ] （推荐）Alembic 里贴入同一份 SQL 并 `upgrade head`；或已手动执行 SQL 且表存在  
- [ ] 库中有 `sys_user`  
- [ ] `main.py` 无 `create_all`  

→ 进入 **[Step 2：JWT 登录（生产向手敲）](./Step2_JWT登录（生产向手敲）.md)**。

---

## 14. 和主教程的关系

本步交付：「配置 + 连接 + **手写 DDL + ORM 映射 + Alembic 版本执行**」。  
以后改表：先写 SQL → 新 migration 粘贴 → 同步 Entity → `upgrade head`。