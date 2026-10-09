# Step 2：JWT 登录（生产向手敲）

> 承接：[Step1_配置与数据库骨架（Docker_MySQL手敲）](./Step1_配置与数据库骨架（Docker_MySQL手敲）.md)  
> 原理精读：[主教程 · 第三章 JWT](./FastAPI%20后台管理实战教程（登录JWT_用户CRUD_秒杀Redis_MySQL）.md)  
> 项目：`fastApiDemo`  
> 本步目标：**登录签发 JWT → 受保护接口验签取当前用户 → 密码只存 bcrypt → 禁用/软删用户不可登录**  
> 用户完整 CRUD 留给 Step 3；本步只做到「能登录、能拿身份」

---

## 0. 本步交付物与生产约定

### 0.1 做完应有

| 项 | 说明 |
|---|---|
| `username` 唯一索引 | 登录按用户名查，必须唯一 |
| `core/security.py` | 密码哈希 / 验密 / JWT 签发与解析 |
| `core/deps.py` | `get_current_user`（对标过滤器） |
| `schemas/auth.py`、`schemas/user.py` | 请求/响应模型（**不含 password**） |
| `services/auth_service.py` | 登录业务 |
| `routers/auth.py` | `POST /auth/login`、`GET /auth/me` |
| `scripts/seed_admin.py` | 种子管理员（bcrypt 写入，不存明文） |
| `main.py` | 挂载 `auth` 路由 |

### 0.2 生产级硬规则（本 Demo 起就遵守）

1. **密码**：只存 bcrypt 哈希；接口永不回传 `password`  
2. **登录失败**：用户名不存在 / 密码错误 / 已禁用，对外统一文案（防账号枚举）  
3. **JWT Payload**：可放 `sub`（用户 id）、`username`；**禁止**放密码、密钥  
4. **鉴权**：受保护接口统一 `Depends(get_current_user)`，不要在每个函数里手写验签  
5. **密钥**：`JWT_SECRET_KEY` 足够长、只放 `.env`，不进公开仓库  
6. **软删 / 状态**：`deleted_at IS NOT NULL` 或 `status != 1` → 视为不可用  

### 0.3 和 Spring Security 对照

| Spring Security | 本步 FastAPI |
|---|---|
| `BCryptPasswordEncoder` | `passlib` + bcrypt |
| `JwtService` / jjwt | `core/security.py` |
| `AuthenticationManager` | `auth_service.login` |
| `OncePerRequestFilter` + `SecurityContext` | `OAuth2PasswordBearer` + `get_current_user` |
| `/login` + 返回 token | `POST /auth/login` |

### 0.4 和你当前仓库的衔接

你已有：

- `.env` 里的 `JWT_SECRET_KEY` / `JWT_ALGORITHM` / `JWT_EXPIRE_MINUTES`  
- `models/user.py` 里的 `UserEntity`（表映射）  
- `sys_user` 表  

本步约定目录（**DTO/VO 与 Entity 分开**，生产更清晰）：

```text
fastApiDemo/
├── core/
│   ├── config.py          # 已有
│   ├── database.py        # 已有
│   ├── security.py        # 新建
│   └── deps.py            # 新建
├── models/
│   └── user.py            # 仅 UserEntity（表映射）
├── schemas/               # 新建：Pydantic 入参/出参
│   ├── __init__.py
│   ├── auth.py
│   └── user.py
├── services/
│   └── auth_service.py    # 新建
├── routers/
│   └── auth.py            # 新建
├── scripts/
│   └── seed_admin.py      # 新建
├── sql/
│   ├── sys_user.sql       # 已有
│   └── V002__uk_username.sql  # 本步：唯一索引
└── main.py                # 挂载 auth
```

> 说明：你原来的 `routers/user.py` 若还引用不存在的 `UserDTO`/`UserVO`，本步可先不动完整 CRUD；若启动报 import 错，把 user 路由暂时从 `main.py` 拿掉，或按本文 `schemas/user.py` 最小改到能启动。Step 3 再系统重做用户 CRUD。

---

## 1. 前置检查

```powershell
cd D:\code-self\thinking-space\AI\后端\Python\fastApiDemo
docker compose ps
poetry show python-jose passlib
```

缺依赖则：

```powershell
poetry add "python-jose[cryptography]" "passlib[bcrypt]"
```

确认 `.env`（你已有可跳过，注意变量名是 **`JWT_SECRET_KEY`**）：

```env
JWT_SECRET_KEY=请使用足够长的随机串_至少32字符
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120
```

`core/config.py` 字段需与 `.env` 一致（你当前已是 `JWT_SECRET_KEY`，后续代码一律用这个名字）。

建议给引擎加上断线重连（生产常用）：

```python
# core/database.py
engine = create_engine(settings.MYSQL_URL, pool_pre_ping=True)
```

---

## 2. 补唯一索引（强烈建议）

登录按 `username` 查用户，没有唯一约束容易脏数据。手写 SQL：

`sql/V002__uk_username.sql`：

```sql
-- 若已有重复用户名，先清理再执行
ALTER TABLE sys_user
  ADD UNIQUE KEY uk_sys_user_username (username);
```

在客户端执行，或以后收进 Alembic `upgrade()`。

同步加强 Entity（可选但推荐）：

```python
username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
```

可空字段建议写成 `| None`，与表一致，例如：

```python
nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

你表注释里：`status` **1=正常，2=禁用**——下文按此约定。

---

## 3. 原理速记（动手前 2 分钟）

```text
Header.Payload.Signature
```

- Payload **Base64 可读，不是加密** → 勿放机密  
- 服务端用 `JWT_SECRET_KEY` **验签 + 查过期**，不是「解密对比」  
- 前端：`Authorization: Bearer <token>`

本步只做 **Access Token**（如 2 小时）。Refresh Token、登出黑名单可后续加，不阻塞主线。

---

## 4. 手敲 `schemas/`（接口模型）

### 4.1 `schemas/__init__.py`

空文件即可。

### 4.2 `schemas/auth.py`

```python
from pydantic import BaseModel, Field


class TokenVO(BaseModel):
    """登录成功返回给前端的令牌信息"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="过期秒数")


class LoginForm(BaseModel):
    """若你额外做 JSON 登录可用；本教程主路径用 OAuth2 表单以兼容 /docs Authorize"""

    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=64)
```

### 4.3 `schemas/user.py`

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserVO(BaseModel):
    """对外用户视图：绝对不含 password"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str | None = None
    age: int | None = None
    email: str | None = None
    phone: str | None = None
    status: int
    created_at: datetime | None = None
```

> `EmailStr` 需要 `email-validator` 时再 `poetry add email-validator`；若不想加依赖，把 `email` 写成 `str | None` 即可。

---

## 5. 手敲 `core/security.py`（安全内核）

```python
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

# bcrypt；deprecated="auto" 便于以后升级算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """明文 → 哈希。入库前必须调用。"""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文与哈希是否匹配。"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    *,
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    签发 Access Token。
    subject 建议用用户 id 的字符串；额外声明不要放敏感信息。
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        # 禁止覆盖子声明关键字段时要小心；业务字段用明确命名
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    验签并解析。失败统一抛 JWTError，由上层转成 401。
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
```

要点：

- 用 **关键字参数** `subject=`，避免位置参数搞反  
- `exp` 用 **UTC**  
- 配置项对齐你的 `settings.JWT_SECRET_KEY`

可选自测：

```powershell
poetry run python -c "from core.security import hash_password, verify_password; h=hash_password('Admin@123'); print(h); print(verify_password('Admin@123', h))"
```

---

## 6. 手敲 `services/auth_service.py`（登录业务）

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from core.config import settings
from models.user import UserEntity
from schemas.auth import TokenVO


class AuthError(Exception):
    """业务可预期的认证失败（对外统一文案）"""

    def __init__(self, message: str = "用户名或密码错误") -> None:
        self.message = message
        super().__init__(message)


class AuthService:
    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> UserEntity:
        stmt = select(UserEntity).where(
            UserEntity.username == username,
            UserEntity.deleted_at.is_(None),
        )
        user = db.scalar(stmt)

        # 即使用户不存在，也走一次假校验节奏的思维：对外文案相同
        if user is None or not verify_password(password, user.password):
            raise AuthError("用户名或密码错误")

        # 你的表约定：1 正常，2 禁用
        if user.status != 1:
            raise AuthError("用户名或密码错误")

        return user

    @staticmethod
    def issue_token(user: UserEntity) -> TokenVO:
        token = create_access_token(
            subject=str(user.id),
            extra_claims={"username": user.username},
        )
        return TokenVO(
            access_token=token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    def login(db: Session, username: str, password: str) -> TokenVO:
        user = AuthService.authenticate(db, username, password)
        return AuthService.issue_token(user)


auth_service = AuthService()
```

> `hash_password` 在本文件 import 是为了种子脚本/后续注册复用同一套；登录主路径主要用 `verify_password`。若你嫌未使用，可从本文件去掉 `hash_password` import，只在 `seed_admin` 里引用。

生产小细节：

- 查用户带上 `deleted_at.is_(None)`  
- 禁用用户不要提示「账号已禁用」（可被探测）；统一「用户名或密码错误」  
- 需要给运营后台单独错误码时再细分，且仅限内网管理端  

---

## 7. 手敲 `core/deps.py`（当前用户依赖）

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import decode_access_token
from models.user import UserEntity

# tokenUrl 必须指向「能换 token 的登录地址」，供 /docs Authorize 使用
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserEntity:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或登录已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception from None

    user = db.scalar(
        select(UserEntity).where(
            UserEntity.id == user_id,
            UserEntity.deleted_at.is_(None),
        )
    )
    if user is None or user.status != 1:
        raise credentials_exception

    return user
```

对照：每个受保护接口加 `current_user: UserEntity = Depends(get_current_user)`，类似过滤器解析完后放入「当前登录用户」。

---

## 8. 手敲 `routers/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from models.user import UserEntity
from schemas.auth import TokenVO
from schemas.user import UserVO
from services.auth_service import AuthError, auth_service
from utils.response import Result

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=Result)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Result:
    """
    OAuth2 密码模式表单：username / password。
    这样 /docs 右上角 Authorize 才能直接用。
    """
    try:
        token: TokenVO = auth_service.login(db, form_data.username, form_data.password)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return Result.success(data=token.model_dump())


@router.get("/me", response_model=Result)
def me(current_user: UserEntity = Depends(get_current_user)) -> Result:
    """已登录用户信息（脱敏 VO）"""
    return Result.success(data=UserVO.model_validate(current_user).model_dump())
```

说明：

- 登录用 **`OAuth2PasswordRequestForm`**，不是纯 JSON——为了和 Swagger Authorize 兼容（生产前端也可发 `application/x-www-form-urlencoded`）  
- 若你坚持 JSON 登录，可再加一个 `/auth/login/json`，但 `/docs` Authorize 仍依赖 `tokenUrl` 那个表单接口  
- `response_model=Result` 时，`data` 里放 `token.model_dump()`，与你现有统一响应一致  

---

## 9. 挂载路由：改 `main.py`

在现有文件上增加：

```python
from routers import auth

app.include_router(auth.router)
```

完整结构示意（按你文件合并，勿丢全局异常）：

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, user  # user 若暂时有问题可先只挂 auth
from utils.response import Result

app = FastAPI(title="demo", description="this is a demo api", version="1.0.0")

app.include_router(auth.router)
# app.include_router(user.router)  # Step 3 再系统做；import 正常再打开

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:xxxx"],  # 前端地址，Step 5 再收紧
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ……全局异常处理保持不变……
```

---

## 10. 种子管理员（禁止手写明文哈希）

`scripts/seed_admin.py`：

```python
"""创建初始管理员。用法：poetry run python scripts/seed_admin.py"""

from sqlalchemy import select

from core.database import SessionLocal
from core.security import hash_password
from models.user import UserEntity

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123"  # 仅本地种子；生产应改密或走初始化流程


def main() -> None:
    db = SessionLocal()
    try:
        exists = db.scalar(
            select(UserEntity).where(UserEntity.username == ADMIN_USERNAME)
        )
        if exists:
            print(f"用户已存在: {ADMIN_USERNAME} (id={exists.id})")
            return

        user = UserEntity(
            username=ADMIN_USERNAME,
            password=hash_password(ADMIN_PASSWORD),
            nickname="管理员",
            status=1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"已创建管理员 id={user.id} username={user.username}")
        print("请登录后尽快修改默认密码")
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

执行：

```powershell
poetry run python scripts/seed_admin.py
```

---

## 11. 启动与验收

```powershell
docker compose ps
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

打开 http://127.0.0.1:8000/docs

### 11.1 登录成功

1. 调 `POST /auth/login`，填 `admin` / `Admin@123`  
2. 应返回：

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

### 11.2 Authorize 后再调 `/auth/me`

1. 右上角 **Authorize**  
2. 输入框填入 **access_token 字符串本身**（部分 UI 不用手写 Bearer）  
3. `GET /auth/me` → 返回用户信息，且 **没有 password 字段**

### 11.3 失败用例（都应 401）

| 操作 | 期望 |
|---|---|
| 错误密码 | 401，文案统一 |
| 不存在的用户 | 401，文案与上相同 |
| 无 token 调 `/auth/me` | 401 |
| 乱改 token 字符 | 401 |
| 把用户 `status` 改为 2 后再登录或带旧 token 访问 `/me` | 401 |

可用 SQL 测禁用：

```sql
UPDATE sys_user SET status = 2 WHERE username = 'admin';
-- 测完改回
UPDATE sys_user SET status = 1 WHERE username = 'admin';
```

---

## 12. 代码结构怎么读（方便对照 Spring）

```text
POST /auth/login
  router 收表单
    → auth_service.login
        → 查库 + verify_password + status
        → create_access_token
    → Result.success(TokenVO)

GET /auth/me
  OAuth2PasswordBearer 抽 Header 里的 Bearer token
    → decode_access_token 验签
    → 按 sub 查库 + 状态/软删
    → UserVO 脱敏返回
```

分层职责：

| 层 | 职责 |
|---|---|
| `routers` | HTTP、状态码、Depends 组装 |
| `services` | 业务规则 |
| `security` | 密码与 JWT，无 HTTP 概念 |
| `deps` | 可复用的「当前用户」 |
| `schemas` | 入参出参，防泄漏 |
| `models` | 表映射 |

---

## 13. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| Authorize 后仍 401 | token 多粘了 `Bearer ` 前缀，或粘了整段 JSON | 只粘 `access_token` 值 |
| `tokenUrl` 404 | 路由未挂载或 prefix 不对 | 确认 `/auth/login` |
| `JWT_SECRET` AttributeError | 配置名不一致 | 统一 `JWT_SECRET_KEY` |
| bcrypt 相关报错 | 依赖版本问题 | `poetry add "bcrypt<4.1"` 或按报错升级 passlib 生态 |
| 登录成功但 `/me` 无用户 | `sub` 不是 id，或种子未写入 | 查库 `SELECT id,username,status FROM sys_user` |
| 导入 `UserDTO` 失败 | 旧 user 路由与新 schemas 未对齐 | 先只挂 `auth`，Step 3 再改 user |

---

## 14. 本步刻意不做（避免一次塞太多）

| 能力 | 为何留到后面 |
|---|---|
| Refresh Token | Step 可扩展；先掌握 Access Token |
| 登出黑名单 | 需 Redis；可放 Step 4 前后 |
| 角色权限 RBAC | Step 3 用户体系稳后再加 |
| 登录限流 / 验证码 | 生产要有，属加固项 |
| 用户 CRUD | **Step 3** |

生产上线前至少再确认：HTTPS、密钥轮换策略、CORS 白名单、默认管理员改密。

---

## 15. Step 2 完成检查清单

- [ ] `username` 已加唯一索引  
- [ ] `core/security.py`：哈希、验密、签发、解析  
- [ ] `services/auth_service.py`：统一失败文案 + status/软删校验  
- [ ] `core/deps.py`：`get_current_user`  
- [ ] `POST /auth/login`、`GET /auth/me`  
- [ ] 种子管理员密码为 bcrypt  
- [ ] `/me` 响应无 `password`  
- [ ] 错密 / 无 token / 坏 token / 禁用用户 均 401  
- [ ] `main.py` 未在启动时建表  

全部勾完 → 进入 **[Step 3：用户 CRUD（生产向手敲）](./Step3_用户CRUD（生产向手敲）.md)**。

---

## 16. 和主教程的关系

主教程第三章讲「为什么」；本文讲「按生产习惯怎么落代码」。  
若两处示例字段名冲突（如早期文稿写过 `JWT_SECRET`），**以你项目 `.env` + `Settings` 的 `JWT_SECRET_KEY` 为准**。
