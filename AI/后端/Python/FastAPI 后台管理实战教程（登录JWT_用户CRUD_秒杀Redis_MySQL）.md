# FastAPI 后台管理实战教程（登录 JWT + 用户 CRUD + 秒杀 Redis + MySQL）

> 承接：[FastAPI 完整版实战教程（适配 SpringBoot/JS 开发者）](./FastAPI%20完整版实战教程（适配%20SpringBoot_JS%20开发者）.md)  
> 项目底座：`fastApiDemo`（已有分层、`Result`、全局异常、CORS）



| 版本 | 现状 | 和本教程关系 |
|---|---|---|
| Python 2.x | 已停止维护 | **不能**用来学 FastAPI |
| Python 3.10+ | 推荐 | 本教程要求（`int \| None`、`match` 等语法） |
| 你当前 | **3.12** | 完全够用 |

后面一律按 **Python 3.12 + FastAPI + Pydantic v2** 来写。

---

## 一、本教程要做成什么

做一个**简单后台管理 Demo**，能力对齐常见 SpringBoot 管理端最小集：

| 模块 | 能力 | SpringBoot 对照 |
|---|---|---|
| 登录 | 账号密码登录，签发 JWT，鉴权访问 | Spring Security + JWT |
| 用户管理 | 用户 CRUD（MySQL） | Controller + Service + MyBatis |
| 秒杀热点 | 商品库存预热到 Redis，扣减走缓存 | Redis + 热点缓存 / 限流思路 |

目标不是上生产秒杀系统，而是把 **JWT 原理、MySQL ORM、Redis 热点读写** 三条主线打通。

### 1.1 建议目录（在现有 `fastApiDemo` 上扩展）

```text
fastApiDemo/
├── main.py
├── .env                      # 配置（对标 application.yml）
├── pyproject.toml            # 项目依赖（对标 pom.xml / package.json）
├── poetry.lock               # 锁版本（对标 package-lock.json）
├── core/                     # 横切能力
│   ├── config.py             # 读取 .env
│   ├── security.py           # JWT 签发/校验
│   ├── deps.py               # Depends：当前登录用户
│   └── database.py           # SQLAlchemy 引擎/会话
├── models/                   # Pydantic DTO/VO（请求响应）
│   ├── user.py
│   ├── auth.py
│   └── seckill.py
├── db_models/                # SQLAlchemy ORM（表结构）
│   ├── user.py
│   └── product.py
├── routers/
│   ├── auth.py               # 登录
│   ├── user.py               # 用户 CRUD
│   └── seckill.py            # 秒杀
├── services/
│   ├── auth_service.py
│   ├── user_service.py
│   └── seckill_service.py
├── utils/
│   └── response.py           # 已有 Result
└── redis_client.py           # Redis 连接
```

对照记忆：

- `models/` ≈ DTO / VO  
- `db_models/` ≈ Entity / `@Table`  
- `core/deps.py` ≈ `SecurityContextHolder` + 过滤器里取当前用户  
- `core/security.py` ≈ JWT 工具类  

---

## 二、环境依赖（Poetry）

本教程用 **Poetry** 做项目包管理（对标 Java 的 Maven、JS 的 npm）：依赖声明、版本锁定、虚拟环境一并管。

### 2.1 安装 Poetry

```bash
# 官方推荐安装方式（任选其一）
pip install poetry
# 或：https://python-poetry.org/docs/#installation
```

安装后确认：

```bash
poetry --version
```

### 2.2 在项目里初始化

在 `fastApiDemo` 目录下：

```bash
cd fastApiDemo

# 若项目还没有 pyproject.toml
poetry init -n

# 指定本教程用的 Python（你当前是 3.12）
poetry env use 3.12
```

对照记忆：

| Poetry | Maven / npm |
|---|---|
| `pyproject.toml` | `pom.xml` / `package.json` |
| `poetry.lock` | `package-lock.json` |
| `.venv`（自动创建） | 本地依赖隔离（类似 node_modules 作用） |
| `poetry add` | `npm install <pkg>` / 改 pom 依赖 |
| `poetry install` | `mvn install` / `npm install` |
| `poetry run ...` | 在项目环境里执行命令 |

### 2.3 添加本教程依赖

```bash
poetry add "fastapi[standard]" sqlalchemy pymysql cryptography
poetry add "python-jose[cryptography]" "passlib[bcrypt]" pydantic-settings
poetry add redis
```

装完后项目里会有：

- `pyproject.toml`：声明依赖（可提交 Git）
- `poetry.lock`：锁精确版本（**建议提交**，保证同事/服务器一致）

### 2.4 日常常用命令

```bash
# 按 lock 安装依赖（新机器 / 拉代码后）
poetry install

# 启动项目（在 Poetry 管理的虚拟环境中跑）
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 进入虚拟环境 shell（可选）
poetry shell

# 查看已装包
poetry show
```

### 2.5 依赖说明

| 包 | 作用 | Spring 对照 |
|---|---|---|
| fastapi[standard] | Web 框架 + 常用开发工具 | Spring Boot Web |
| sqlalchemy | ORM | MyBatis-Plus / JPA |
| pymysql | MySQL 驱动 | mysql-connector-j |
| python-jose | JWT 编解码 | jjwt / nimbus-jose |
| passlib[bcrypt] | 密码哈希 | BCryptPasswordEncoder |
| pydantic-settings | 读 `.env` | `@ConfigurationProperties` |
| redis | Redis 客户端 | Spring Data Redis |

`.env` 示例：

```env
APP_NAME=fastApiDemo
MYSQL_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/fastapi_demo?charset=utf8mb4
REDIS_URL=redis://127.0.0.1:6379/0
JWT_SECRET=请换成足够长的随机字符串_至少32位
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120
```

建库：

```sql
CREATE DATABASE fastapi_demo DEFAULT CHARACTER SET utf8mb4;
```

---

## 三、JWT 原理（必读，对标 Spring Security JWT）

### 3.1 JWT 是什么

**JWT（JSON Web Token）** 是一段可携带声明（claims）的令牌，通常长这样：

```text
xxxxx.yyyyy.zzzzz
│      │      └─ Signature（签名）
│      └─ Payload（载荷，Base64URL）
└─ Header（头，Base64URL）
```

特点：

1. **无状态**：服务端不必像 Session 那样存每个登录态（可扩展为黑名单，但基础用法无状态）  
2. **自包含**：载荷里可带 `user_id`、`username`、过期时间等  
3. **可校验**：用密钥验签，篡改后签名对不上  

Spring 里常见链路：

```text
登录成功 → 签发 JWT → 前端存 localStorage/Cookie
后续请求 Header: Authorization: Bearer <token>
过滤器解析 JWT → 放入 SecurityContext
```

FastAPI 对应：

```text
登录成功 → security.create_access_token(...)
后续请求 Header: Authorization: Bearer <token>
Depends(get_current_user) 解析并返回当前用户
```

### 3.2 三段分别是什么

**Header（头）**

```json
{ "alg": "HS256", "typ": "JWT" }
```

说明用什么算法签名（本教程用对称密钥 **HS256**）。

**Payload（载荷）**

```json
{
  "sub": "1",
  "username": "admin",
  "exp": 1735689600
}
```

常用字段：

| 字段 | 含义 |
|---|---|
| `sub` | subject，常用用户 ID |
| `exp` | 过期时间（Unix 时间戳） |
| 自定义 | `username`、`role` 等 |

注意：Payload **只是 Base64，不是加密**。谁拿到 token 都能解码看到内容，所以**不要放密码、身份证号**。保密靠 HTTPS + 签名密钥。

**Signature（签名）**

伪代码：

```text
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  JWT_SECRET
)
```

服务端用同一个 `JWT_SECRET` 重算签名，和 token 第三段比对：一致且未过期 → 合法。

### 3.3 时序图（登录到鉴权）

```text
浏览器/前端                    FastAPI                         MySQL
    │                            │                              │
    │  POST /auth/login          │                              │
    │  {username,password}       │                              │
    │───────────────────────────▶│  查用户、校验 bcrypt          │
    │                            │─────────────────────────────▶│
    │                            │◀─────────────────────────────│
    │  {token, token_type}       │  签发 JWT                    │
    │◀───────────────────────────│                              │
    │                            │                              │
    │  GET /user/list            │                              │
    │  Authorization: Bearer xxx │                              │
    │───────────────────────────▶│  验签 + 解析 sub             │
    │                            │  Depends 注入当前用户         │
    │                            │─────────────────────────────▶│
    │  Result{data:[...]}        │                              │
    │◀───────────────────────────│                              │
```

### 3.4 和 Session 的对比（Spring 开发者必知）

| | Session + Cookie | JWT |
|---|---|---|
| 服务端是否存会话 | 通常要存 | 基础用法不存 |
| 水平扩展 | 需 Session 共享（Redis） | 天然友好 |
| 注销 | 删 Session 即可 | 需黑名单/短过期+刷新令牌 |
| 信息可见性 | SessionId 无业务含义 | Payload 可读（勿放机密） |
| 典型场景 | 传统单体后台 | 前后端分离、微服务 |

本 Demo 用 **短过期 Access Token（如 2 小时）** 即可；生产可再加 Refresh Token。

### 3.5 核心代码骨架（原理落地）

`core/security.py`：

```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(subject: str, extra: dict | None = None) -> str:
    payload = {"sub": subject, "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def parse_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        raise ValueError("无效或过期的 token") from e
```

`core/deps.py`（对标过滤器 + 取当前用户）：

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from core.security import parse_token
from services.user_service import user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = parse_token(token)
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期")
    user = user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
```

受保护接口：

```python
@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return Result.success(data=current_user)
```

前端请求头：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## 四、MySQL + SQLAlchemy（用户表）

### 4.1 表设计

```sql
CREATE TABLE sys_user (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  username     VARCHAR(50)  NOT NULL UNIQUE,
  password     VARCHAR(255) NOT NULL COMMENT 'bcrypt哈希，禁止存明文',
  nickname     VARCHAR(50)  NULL,
  age          INT          NULL,
  email        VARCHAR(100) NULL,
  status       TINYINT      NOT NULL DEFAULT 1 COMMENT '1启用 0禁用',
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 初始管理员（密码请用程序 bcrypt 生成后写入，不要手写明文）
-- 示例：启动时若不存在 admin 则自动创建，密码 Admin@123
```

### 4.2 ORM 模型（`db_models/user.py`）

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, SmallInteger
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
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
```

### 4.3 会话与依赖注入

```python
# core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from core.config import settings

engine = create_engine(settings.MYSQL_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

对照：`get_db()` ≈ Spring 里每个请求一个 SqlSession / EntityManager，用完关闭。

---

## 五、登录模块

### 5.1 接口约定

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/auth/login` | 登录，返回 JWT | 否 |
| GET | `/auth/me` | 当前用户信息 | 是 |

登录请求（兼容 `/docs` 的 OAuth2 密码模式，也可用 JSON）：

```json
{ "username": "admin", "password": "Admin@123" }
```

响应：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 7200
  }
}
```

### 5.2 登录业务要点

1. 按 `username` 查库  
2. `verify_password` 比对 bcrypt  
3. 校验 `status == 1`  
4. `create_access_token(subject=str(user.id), extra={"username": user.username})`  
5. **永远不要**把密码哈希返回给前端  

### 5.3 和 Spring Security 的对应

| Spring Security | FastAPI |
|---|---|
| `AuthenticationManager.authenticate` | `auth_service.login` |
| `UsernamePasswordAuthenticationToken` | 登录 DTO |
| `JwtAuthenticationFilter` | `OAuth2PasswordBearer` + `get_current_user` |
| `@PreAuthorize` | 在 `Depends` 里查角色（本 Demo 可先省略角色） |

---

## 六、用户管理 CRUD

全部接口加 `Depends(get_current_user)`，未登录 401。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/user/list?page=1&size=10&keyword=` | 分页列表 |
| GET | `/user/{id}` | 详情 |
| POST | `/user` | 新增（密码 bcrypt） |
| PUT | `/user/{id}` | 更新（密码可选改） |
| DELETE | `/user/{id}` | 删除（或软删改 status） |

### 6.1 DTO / VO 建议

```python
# models/user.py
from pydantic import BaseModel, ConfigDict, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=32)
    nickname: str | None = None
    age: int | None = Field(default=None, ge=0, le=150)
    email: str | None = None

class UserUpdate(BaseModel):
    nickname: str | None = None
    age: int | None = Field(default=None, ge=0, le=150)
    email: str | None = None
    password: str | None = Field(default=None, min_length=6, max_length=32)
    status: int | None = Field(default=None, ge=0, le=1)

class UserVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str | None
    age: int | None
    email: str | None
    status: int
```

注意：**VO 不要包含 password 字段**。

### 6.2 Service 层伪代码

```python
def create_user(db, dto: UserCreate) -> UserVO:
    if db.query(UserEntity).filter_by(username=dto.username).first():
        raise HTTPException(400, "用户名已存在")
    entity = UserEntity(
        username=dto.username,
        password=hash_password(dto.password),
        nickname=dto.nickname,
        age=dto.age,
        email=dto.email,
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return UserVO.model_validate(entity)
```

分页可用 `offset/limit`，或后续换更规范的 count + page 结构：

```json
{ "list": [...], "total": 100, "page": 1, "size": 10 }
```

---

## 七、秒杀热点缓存（Redis）

### 7.1 要解决什么问题

秒杀时「查库存 / 扣库存」若每次打 MySQL，热点行会打爆数据库。  
常见套路（本 Demo 简化版）：

1. **活动开始前**：把库存预热进 Redis  
2. **下单瞬间**：只在 Redis 原子扣减  
3. **成功后再**：异步或同步落库订单（Demo 可同步写一条简化订单）  
4. **库存为 0**：直接失败，不再打库  

### 7.2 表设计（简化）

```sql
CREATE TABLE seckill_product (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  name          VARCHAR(100) NOT NULL,
  stock         INT NOT NULL DEFAULT 0 COMMENT 'MySQL中的库存（预热源）',
  seckill_price DECIMAL(10,2) NOT NULL,
  status        TINYINT NOT NULL DEFAULT 1,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE seckill_order (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id     BIGINT NOT NULL,
  product_id  BIGINT NOT NULL,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_user_product (user_id, product_id)  -- 一人一单（简化防刷）
);
```

### 7.3 Redis Key 设计

| Key | 类型 | 含义 |
|---|---|---|
| `seckill:stock:{product_id}` | String/Int | 热点库存 |
| `seckill:bought:{product_id}` | Set | 已购买 user_id（防重复） |

### 7.4 原子扣减（核心）

用 Lua 保证「判断库存 + 扣减 + 记录用户」原子性，避免超卖：

```lua
-- KEYS[1]=库存key  KEYS[2]=已买集合  ARGV[1]=user_id
local stock = tonumber(redis.call('GET', KEYS[1]) or '0')
if stock <= 0 then
  return -1   -- 售罄
end
if redis.call('SISMEMBER', KEYS[2], ARGV[1]) == 1 then
  return -2   -- 已买过
end
redis.call('DECR', KEYS[1])
redis.call('SADD', KEYS[2], ARGV[1])
return 1      -- 成功
```

返回值约定：`1` 成功，`-1` 售罄，`-2` 重复购买。

### 7.5 接口约定

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/seckill/product` | 创建秒杀商品（写 MySQL） | 是 |
| POST | `/seckill/warm/{product_id}` | 预热库存到 Redis | 是 |
| GET | `/seckill/stock/{product_id}` | 查 Redis 库存 | 是 |
| POST | `/seckill/buy/{product_id}` | 秒杀下单 | 是 |

流程：

```text
创建商品(stock=100)
    → 预热：SET seckill:stock:1 100
    → 用户带 JWT 调用 /seckill/buy/1
    → Lua 扣减
    → 成功则写 seckill_order
```

### 7.6 和真实秒杀的差距（学完心里有数）

本 Demo **有意简化**，真实系统通常还要：

- 网关限流 / 令牌桶  
- 独立库存服务、消息队列削峰  
- 订单异步落库、对账补偿  
- 活动时间窗、验证码、风控  

你现在掌握的是：**热点数据放 Redis + 原子操作防超卖**，这对后台与高并发入门已经够用。

---

## 八、推荐实现顺序（按这个写代码）

在 `fastApiDemo` 里按周推进即可：

### Step 1：配置与数据库骨架

1. 加 `.env`、`core/config.py`、`core/database.py`  
2. 建库建表（或 `Base.metadata.create_all`）  
3. 启动时确保能 `get_db()` 连上 MySQL  

### Step 2：JWT 登录

1. 实现 `security.py`（哈希 + 签发 + 解析）  
2. `POST /auth/login`、`GET /auth/me`  
3. 用 `/docs` 点 Authorize，粘贴 token，验证鉴权  

**验收**：错误密码 401；正确密码拿到 token；无 token 访问 `/user/list` 被拒。

### Step 3：用户 CRUD

1. 替换现在假的 `user_service`  
2. 列表分页、增删改查  
3. VO 脱敏（无 password）  

**验收**：用 admin 登录后完整走一遍 CRUD。

### Step 4：秒杀 + Redis

1. 接 `redis_client`  
2. 预热 + Lua 扣减 + 订单唯一索引  
3. 用两个用户 token 测：一人只能买一次；库存扣到 0 后失败  

**验收**：库存 5，并发/连续买 6 次，成功 ≤5，无超卖。

### Step 5：收尾

1. CORS 改成真实前端源  
2. 确认 `pyproject.toml` + `poetry.lock` 已提交（版本锁定）  
3. README 写启动步骤：MySQL / Redis / `poetry install` / `poetry run uvicorn ...`  

---

## 九、main.py 挂载示意

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, user, seckill
from core.database import Base, engine

app = FastAPI(title="后台管理 Demo", version="2.0.0")

Base.metadata.create_all(bind=engine)  # Demo 可用；正式环境改用 Alembic

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(seckill.router)
```

（全局异常处理保持你现有写法即可。）

---

## 十、SpringBoot 对照总表（本教程新增部分）

| 场景 | SpringBoot | FastAPI Demo |
|---|---|---|
| 配置 | `application.yml` | `.env` + `pydantic-settings` |
| 实体 | `@Entity` / DO | SQLAlchemy `Mapped` |
| Mapper/Repo | MyBatis / JPA | `Session` + query |
| 密码加密 | `BCryptPasswordEncoder` | `passlib` bcrypt |
| JWT 签发 | `Jjwt` / Auth0 | `python-jose` |
| 鉴权过滤器 | `OncePerRequestFilter` | `Depends(get_current_user)` |
| Redis | `StringRedisTemplate` | `redis.Redis` |
| 原子扣库存 | Lua + RedisTemplate | `eval` Lua 脚本 |

---

## 十一、学习检查清单

- [ ] 能画出 JWT 三段结构，并说明为什么 Payload 不能放密码  
- [ ] 能解释 HS256 验签过程，以及 `exp` 过期如何导致 401  
- [ ] 登录后用 `Authorization: Bearer` 访问受保护接口  
- [ ] 用户 CRUD 全部走 MySQL，密码仅存哈希  
- [ ] 秒杀预热后，扣库存以 Redis 为准，且不超卖、不重复买  
- [ ] 知道 Demo 与真实秒杀的差距  

---

## 十二、下一步

1. **先读本文第三章（JWT 原理）**，再动手 Step 1～2  
2. 代码实现时继续改 `fastApiDemo`，不要新开空项目  
3. 做完后可再补：Alembic 迁移、角色权限、Refresh Token、操作日志  

若需要，我可以在下一阶段**直接按本文 Step 顺序，把 `fastApiDemo` 代码骨架生成出来**（先登录 + 用户 CRUD，再秒杀）。
