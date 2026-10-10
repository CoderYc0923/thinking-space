# Step 3：用户 CRUD（生产向手敲）

> 承接：[Step2_JWT登录（生产向手敲）](./Step2_JWT登录（生产向手敲）.md)  
> 主教程对照：[FastAPI 后台管理实战教程](./FastAPI%20后台管理实战教程（登录JWT_用户CRUD_秒杀Redis_MySQL）.md) 第六章  
> 项目：`fastApiDemo`  
> 本步目标：**在已登录前提下，完成用户分页列表 / 详情 / 新增 / 更新 / 软删；密码 bcrypt；VO 永不回传 password**

---

## 0. 本步交付与生产约定

### 0.1 做完应有

| 项 | 说明 |
|---|---|
| `schemas/user.py` | Create / Update / VO / 分页结构 |
| `services/user_service.py` | 真实查改增删（接 MySQL） |
| `routers/user.py` | 受保护的 CRUD 接口 |
| 统一业务异常 | 如用户名重复、用户不存在 → 明确 HTTP 状态 |
| 软删除 | 写 `deleted_at`，列表默认不展示已删 |

### 0.2 接口一览（全部要登录）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/user/list?page=1&size=10&keyword=` | 分页列表（可按用户名/昵称模糊） |
| GET | `/user/{user_id}` | 详情 |
| POST | `/user` | 新增 |
| PUT | `/user/{user_id}` | 更新（密码可选） |
| DELETE | `/user/{user_id}` | 软删除 |
| GET | `/user/info` | 当前登录用户（Step 2 已有，可保留） |

> **路由顺序**：`/list`、`/info` 必须写在 `/{user_id}` **前面**，否则 `list` 会被当成 `user_id` 解析。

### 0.3 生产硬规则

1. 所有写接口 + 列表/详情：`Depends(get_current_user)`  
2. **VO 禁止 `password` 字段**  
3. 入库密码一律 `hash_password`；更新时「未传 password 则不改」  
4. 用户名唯一；重复 → **400**（或 409）  
5. 查/改/删默认过滤 `deleted_at IS NULL`  
6. 你的表约定：`status` **1=正常，2=禁用**（与 Step 2 一致）  
7. Service 管业务；Router 只管 HTTP / 依赖注入 / 转 Result  

### 0.4 和 Spring 对照

| Spring | 本步 |
|---|---|
| Controller + `@PreAuthorize` | `routers/user.py` + `Depends(get_current_user)` |
| Service / `@Transactional` | `user_service` + `db.commit()` / `rollback` |
| DTO / VO | `schemas/user.py` |
| Entity | `models/user.py` 的 `UserEntity` |
| Page\<T\> | 自研 `PageVO`：`list/total/page/size` |

---

## 1. 目录与衔接现状

你已有：

- `models/user.py` → `UserEntity`  
- `schemas/user.py` → 初步的 `UserDTO` / `UserVO`  
- `core/deps.py` → `get_current_user`  
- `core/security.py` → `hash_password`  
- `routers/__init__.py` → 已汇总 `user.router`  

本步把 `UserDTO` **升级/拆成**更清晰的命名（推荐）：

| 原 | 建议 |
|---|---|
| `UserDTO` | `UserCreate`（创建入参） |
| （无） | `UserUpdate`（更新入参，字段大多可选） |
| `UserVO` | 保留，继续 `from_attributes=True` |

若你想暂时保留 `UserDTO` 名字，可：`UserCreate = UserDTO`，但教程正文用 `UserCreate`。

---

## 2. 手敲 `schemas/user.py`

完整替换/对齐为：

```python
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class UserCreate(BaseModel):
    """新增用户"""

    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=64)
    nickname: str | None = None
    age: int | None = Field(default=None, ge=0, le=150)
    email: str | None = None
    phone: str | None = None


class UserUpdate(BaseModel):
    """更新用户：未传的字段不改；password 有值才改密"""

    nickname: str | None = None
    age: int | None = Field(default=None, ge=0, le=150)
    email: str | None = None
    phone: str | None = None
    password: str | None = Field(default=None, min_length=6, max_length=64)
    status: int | None = Field(default=None, description="1正常 2禁用")


class UserVO(BaseModel):
    """对外视图：绝不含 password"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str | None = None
    age: int | None = None
    email: str | None = None
    phone: str | None = None
    status: int
    created_at: datetime | None = None


class PageVO(BaseModel, Generic[T]):
    """通用分页外壳"""

    list: list[T]
    total: int
    page: int
    size: int
```

兼容旧名（可选，避免别处 import 炸掉）：

```python
UserDTO = UserCreate  # 兼容别名
```

---

## 3. 业务异常（建议单独一小文件）

`services/errors.py`（或放在 `user_service.py` 顶部）：

```python
class AppError(Exception):
    def __init__(self, message: str, code: int = 400) -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(message, code=404)


class ConflictError(AppError):
    def __init__(self, message: str = "数据冲突") -> None:
        super().__init__(message, code=409)
```

Router 里捕获后转 `HTTPException`。也可继续用 `HTTPException` 直接在 Service 抛——生产上更推荐 **Service 不依赖 FastAPI**，只抛业务异常。

---

## 4. 手敲 `services/user_service.py`

```python
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from core.security import hash_password
from models.user import UserEntity
from schemas.user import PageVO, UserCreate, UserUpdate, UserVO
from services.errors import ConflictError, NotFoundError


def _to_vo(user: UserEntity) -> UserVO:
    return UserVO.model_validate(user)


def _get_active_user(db: Session, user_id: int) -> UserEntity:
    user = db.scalar(
        select(UserEntity).where(
            UserEntity.id == user_id,
            UserEntity.deleted_at.is_(None),
        )
    )
    if user is None:
        raise NotFoundError("用户不存在")
    return user


class UserService:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> UserVO:
        return _to_vo(_get_active_user(db, user_id))

    @staticmethod
    def list_users(
        db: Session,
        *,
        page: int = 1,
        size: int = 10,
        keyword: str | None = None,
    ) -> PageVO[UserVO]:
        page = max(page, 1)
        size = min(max(size, 1), 100)  # 防止一次拉爆

        conditions = [UserEntity.deleted_at.is_(None)]
        if keyword:
            like = f"%{keyword.strip()}%"
            conditions.append(
                or_(
                    UserEntity.username.like(like),
                    UserEntity.nickname.like(like),
                )
            )

        total = db.scalar(
            select(func.count()).select_from(UserEntity).where(*conditions)
        ) or 0

        rows = db.scalars(
            select(UserEntity)
            .where(*conditions)
            .order_by(UserEntity.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()

        return PageVO(
            list=[_to_vo(u) for u in rows],
            total=total,
            page=page,
            size=size,
        )

    @staticmethod
    def create_user(db: Session, dto: UserCreate) -> UserVO:
        exists = db.scalar(
            select(UserEntity.id).where(
                UserEntity.username == dto.username,
                UserEntity.deleted_at.is_(None),
            )
        )
        if exists is not None:
            raise ConflictError("用户名已存在")

        entity = UserEntity(
            username=dto.username,
            password=hash_password(dto.password),
            nickname=dto.nickname,
            age=dto.age,
            email=dto.email,
            phone=dto.phone,
            status=1,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return _to_vo(entity)

    @staticmethod
    def update_user(db: Session, user_id: int, dto: UserUpdate) -> UserVO:
        user = _get_active_user(db, user_id)

        # exclude_unset：只更新请求里真正出现的字段
        data = dto.model_dump(exclude_unset=True)

        if "password" in data:
            plain = data.pop("password")
            if plain:
                user.password = hash_password(plain)

        if "status" in data and data["status"] is not None:
            if data["status"] not in (1, 2):
                raise ConflictError("status 仅支持 1 或 2")
            user.status = data.pop("status")

        for key, value in data.items():
            setattr(user, key, value)

        user.updated_at = datetime.now()
        db.commit()
        db.refresh(user)
        return _to_vo(user)

    @staticmethod
    def delete_user(db: Session, user_id: int, *, operator_id: int) -> None:
        if user_id == operator_id:
            raise ConflictError("不能删除当前登录用户")

        user = _get_active_user(db, user_id)
        user.deleted_at = datetime.now()
        user.updated_at = datetime.now()
        db.commit()


user_service = UserService()
```

要点：

- `func.count()` + `offset/limit` 做分页  
- `exclude_unset=True` 实现「部分更新」（类似 PATCH 语义，路径仍用 PUT 也可）  
- 软删只写 `deleted_at`，不物理 `DELETE`  
- 禁止删自己，避免把自己锁死  

出错时记得：`commit` 前若异常，Session 可能需要 `rollback`。可在 Router 的异常分支或 `get_db` 增强里统一处理；最小做法是 Service 里 `try/except` 后 `db.rollback()` 再抛出。推荐增强版 `create/update/delete`：

```python
try:
    db.add(entity)
    db.commit()
    db.refresh(entity)
except Exception:
    db.rollback()
    raise
```

（上面核心逻辑相同，你可按需补上。）

---

## 5. 手敲 `routers/user.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from models.user import UserEntity
from schemas.user import PageVO, UserCreate, UserUpdate, UserVO
from services.errors import AppError
from services.user_service import user_service
from utils.response import Result

router = APIRouter(prefix="/user", tags=["用户管理"])


def _handle_app_error(exc: AppError) -> None:
    raise HTTPException(status_code=exc.code, detail=exc.message) from exc


@router.get("/info", response_model=Result)
def my_info(current_user: UserEntity = Depends(get_current_user)) -> Result:
    return Result.success(data=UserVO.model_validate(current_user).model_dump())


@router.get("/list", response_model=Result)
def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None),
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),  # 只要登录；暂不用 current_user
) -> Result:
    page_data: PageVO[UserVO] = user_service.list_users(
        db, page=page, size=size, keyword=keyword
    )
    return Result.success(data=page_data.model_dump())


@router.get("/{user_id}", response_model=Result)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),
) -> Result:
    try:
        vo = user_service.get_by_id(db, user_id)
    except AppError as exc:
        _handle_app_error(exc)
    return Result.success(data=vo.model_dump())


@router.post("", response_model=Result)
def create_user(
    dto: UserCreate,
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),
) -> Result:
    try:
        vo = user_service.create_user(db, dto)
    except AppError as exc:
        _handle_app_error(exc)
    return Result.success(data=vo.model_dump(), msg="创建成功")


@router.put("/{user_id}", response_model=Result)
def update_user(
    user_id: int,
    dto: UserUpdate,
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),
) -> Result:
    try:
        vo = user_service.update_user(db, user_id, dto)
    except AppError as exc:
        _handle_app_error(exc)
    return Result.success(data=vo.model_dump(), msg="更新成功")


@router.delete("/{user_id}", response_model=Result)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> Result:
    try:
        user_service.delete_user(db, user_id, operator_id=current_user.id)
    except AppError as exc:
        _handle_app_error(exc)
    return Result.success(msg="删除成功")
```

说明：

- `_` 表示「依赖要执行，但不使用返回值」  
- `POST ""` 在 prefix `/user` 下即 `POST /user`（注意不要写成 `POST /` 重复斜杠困扰；也可用 `@router.post("/")`）  
- 若 `POST ""` 在你环境有问题，改成 `@router.post("/")`  

`routers/__init__.py` 已 include `user.router` 则 **main 不用改**。

---

## 6. 分页响应长什么样

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "username": "admin",
        "nickname": "管理员",
        "age": null,
        "email": null,
        "phone": null,
        "status": 1,
        "created_at": "2026-10-09T12:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 10
  }
}
```

确认：**没有 password**。

---

## 7. 启动与验收

```powershell
cd D:\code-self\thinking-space\AI\后端\Python\fastApiDemo
poetry run uvicorn main:app --reload --port 8000
```

1. `/docs` → `/auth/login` 拿 token → Authorize  
2. `GET /user/list` → 能看到 admin  
3. `POST /user` 建一个 `demo01` / `Demo@123`  
4. `GET /user/{id}` 详情无密码  
5. `PUT /user/{id}` 改昵称；再可选改密码后用新密码登录  
6. `DELETE /user/{id}` 后 list 不再出现；直接查详情 404  
7. 无 token 调任意 CRUD → 401  
8. 重复用户名 → 409/400  
9. 删除自己 → 业务错误  

---

## 8. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `/user/list` 404 或变成查 id | `/{user_id}` 写在 `/list` 前面 | 调整路由顺序 |
| `model_validate` 报 model_type | VO 缺 `from_attributes=True` 或导错模块 | 用 `schemas.user.UserVO` |
| 响应里出现 password | VO 含了该字段或直接 dump Entity | 只用 UserVO |
| 更新没生效 | 没用 `exclude_unset` / 没 commit | 对照 Service |
| 软删后还能登录 | 登录查询未过滤 `deleted_at` | 回看 Step 2 `authenticate` |

---

## 9. 本步刻意不做

| 能力 | 以后再加 |
|---|---|
| 角色 / 菜单权限 | RBAC |
| 操作日志 | 审计表 |
| 唯一「管理员不能删光」 | 业务规则增强 |
| 导出 Excel | 管理端增强 |

---

## 10. 完成检查清单

- [ ] Create / Update / VO / PageVO 齐全，VO 无 password  
- [ ] list / detail / create / update / soft-delete 全部要登录  
- [ ] 密码创建与可选更新均 bcrypt  
- [ ] 用户名冲突有明确错误  
- [ ] 分页返回 list/total/page/size  
- [ ] 软删后列表不可见，详情 404  
- [ ] 不能删除当前登录用户  
- [ ] `/list`、`/info` 在 `/{id}` 之前注册  

→ 下一阶段：**[Step 4：秒杀 + Redis（生产向手敲）](./Step4_秒杀Redis（生产向手敲）.md)**。

---

## 11. 和主教程的关系

主教程第六章给的是接口与骨架；本文按你当前仓库（`schemas/` + `Result` + 软删 + status=1/2 + bcrypt 直用）写成可手敲的生产向落地版。字段名以你表结构为准（含 `phone`、`deleted_at`）。
