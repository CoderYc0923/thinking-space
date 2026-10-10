# Step 4：秒杀 + Redis（生产向手敲）

> 承接：[Step3_用户CRUD（生产向手敲）](./Step3_用户CRUD（生产向手敲）.md)  
> 原理对照：主教程第七章  
> 项目：`fastApiDemo`  
> 本步目标：**商品库存预热到 Redis → Lua 原子扣减防超卖/防重复买 → 成功后落 MySQL 订单；失败要补偿**  
> 说明：这是**教学向生产习惯 Demo**，不是完整电商秒杀中台（限流、MQ、对账见文末差距表）

---

## 0. 本步交付与生产约定

### 0.1 做完应有

| 项 | 说明 |
|---|---|
| Compose 增加 Redis | 与 MySQL 一起起 |
| `sql/seckill_*.sql` | 商品表 + 订单表（手写 DDL） |
| `models/seckill.py` | ORM 映射 |
| `core/redis_client.py` | Redis 连接（对标 Data Redis） |
| `services/seckill_service.py` | 预热 / 查库存 / 下单 |
| `lua/seckill_buy.lua` 或常量 | 原子脚本 |
| `routers/seckill.py` | 鉴权接口 |
| 补偿逻辑 | Redis 扣成功但 DB 失败时回滚 Redis |

### 0.2 接口一览（全部要登录）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/seckill/product` | 创建秒杀商品（写 MySQL） |
| POST | `/seckill/warm/{product_id}` | 把 MySQL 库存预热进 Redis |
| GET | `/seckill/stock/{product_id}` | 查 Redis 当前库存 |
| POST | `/seckill/buy/{product_id}` | 秒杀下单 |
| GET | `/seckill/orders/me` | 我的秒杀订单（便于验收） |

### 0.3 核心链路

```text
创建商品 stock=5（MySQL）
    → warm：SET seckill:stock:{id} 5 ，DEL/重建 bought set
    → buy：Lua（库存>0 且未买过 → DECR + SADD）
        → 成功：INSERT seckill_order（uk: user_id+product_id）
        → DB 失败：补偿 Redis（INCR + SREM）
    → 售罄 / 重复买：直接失败，不打无意义写库
```

### 0.4 生产硬规则（本 Demo 遵守）

1. **扣库存以 Redis 为准**，下单热路径不先 `UPDATE stock` 打热点行  
2. **判库存 + 扣减 + 记已买** 必须在 **同一段 Lua** 里，避免竞态超卖  
3. MySQL 订单表保留 **`UNIQUE(user_id, product_id)`** 作最终防线  
4. Redis 成功、DB 失败 → **必须补偿**，否则库存被「吃掉」  
5. 所有接口 `Depends(get_current_user)`  
6. DDL 手写；应用启动不 `create_all`  

### 0.5 和 Spring 对照

| Spring | 本步 |
|---|---|
| `StringRedisTemplate` | `redis.Redis` |
| `DefaultRedisScript` + Lua | `redis.eval` / `script_load` |
| `@Transactional` 落单 | Session + `get_db` 统一 commit |
| 唯一索引防重复下单 | `uk_user_product` |

---

## 1. Docker Compose 增加 Redis

改 `docker-compose.yml`，在 `services` 下增加（与 mysql 同级）：

```yaml
  redis:
    image: redis:7-alpine
    container_name: fastapi-demo-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - py_demo_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
```

顶层 `volumes:` 增加：

```yaml
  py_demo_redis_data:
```

启动：

```powershell
docker compose up -d
docker compose ps
# 应能看到 mysql、redis 都 healthy/running
```

确认 `.env`：

```env
REDIS_URL=redis://127.0.0.1:6379/0
```

`core/config.py` 已有 `REDIS_URL` 即可。

依赖（若未装）：

```powershell
poetry add redis
```

---

## 2. 手写 DDL

### 2.1 `sql/seckill_product.sql`

```sql
CREATE TABLE IF NOT EXISTS seckill_product (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  name          VARCHAR(100) NOT NULL COMMENT '商品名',
  stock         INT NOT NULL DEFAULT 0 COMMENT 'MySQL库存（预热源）',
  seckill_price DECIMAL(10,2) NOT NULL COMMENT '秒杀价',
  status        TINYINT NOT NULL DEFAULT 1 COMMENT '1上架 0下架',
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='秒杀商品';
```

### 2.2 `sql/seckill_order.sql`

```sql
CREATE TABLE IF NOT EXISTS seckill_order (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id     BIGINT NOT NULL,
  product_id  BIGINT NOT NULL,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_user_product (user_id, product_id),
  KEY idx_product_id (product_id),
  KEY idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='秒杀订单';
```

在客户端执行建表（或按 Step1 习惯收进 Alembic 手写 revision）。

---

## 3. ORM：`models/seckill.py`

```python
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class SeckillProductEntity(Base):
    __tablename__ = "seckill_product"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    seckill_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class SeckillOrderEntity(Base):
    __tablename__ = "seckill_order"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uk_user_product"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
```

---

## 4. Schemas：`schemas/seckill.py`

```python
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SeckillProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    stock: int = Field(gt=0, le=100000)
    seckill_price: Decimal = Field(gt=0)


class SeckillProductVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    stock: int
    seckill_price: Decimal
    status: int
    created_at: datetime | None = None


class SeckillStockVO(BaseModel):
    product_id: int
    redis_stock: int
    warmed: bool


class SeckillOrderVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    created_at: datetime | None = None


class SeckillBuyVO(BaseModel):
    order_id: int
    product_id: int
    user_id: int
    message: str = "秒杀成功"
```

---

## 5. Redis 客户端：`core/redis_client.py`

```python
from functools import lru_cache

import redis

from core.config import settings


@lru_cache
def get_redis() -> redis.Redis:
    """
    进程内复用连接池。
    decode_responses=True：读写都是 str，Lua 返回值更好处理。
    """
    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
    )


def stock_key(product_id: int) -> str:
    return f"seckill:stock:{product_id}"


def bought_key(product_id: int) -> str:
    return f"seckill:bought:{product_id}"
```

可选：在 FastAPI lifespan 里 `ping()` 一次，启动期尽早暴露 Redis 连不上的问题（本步不强制）。

---

## 6. Lua 脚本（核心）

新建 `lua/seckill_buy.lua`（也可用 Python 多行字符串，**建议独立文件便于评审**）：

```lua
-- KEYS[1] = stock key
-- KEYS[2] = bought set key
-- ARGV[1] = user_id
local stock = tonumber(redis.call('GET', KEYS[1]) or '0')
if stock <= 0 then
  return -1
end
if redis.call('SISMEMBER', KEYS[2], ARGV[1]) == 1 then
  return -2
end
redis.call('DECR', KEYS[1])
redis.call('SADD', KEYS[2], ARGV[1])
return 1
```

返回值约定：

| 返回 | 含义 |
|---|---|
| `1` | 抢购成功（已扣库存并记入已买集合） |
| `-1` | 售罄 |
| `-2` | 该用户已买过 |

为什么必须 Lua：若用「GET → 判断 → DECR」分多步，两个请求可能同时看到 stock=1，一起 DECR → **超卖**。

---

## 7. 业务异常（可扩 `schemas/error.py`）

```python
class SoldOutError(AppError):
    def __init__(self, message: str = "已售罄") -> None:
        super().__init__(message, code=409)


class AlreadyBoughtError(AppError):
    def __init__(self, message: str = "请勿重复购买") -> None:
        super().__init__(message, code=409)


class NotWarmedError(AppError):
    def __init__(self, message: str = "活动未预热") -> None:
        super().__init__(message, code=400)
```

---

## 8. Service：`services/seckill_service.py`

生产向要点写进代码注释，按这个结构手敲：

```python
from pathlib import Path

from redis import Redis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.redis_client import bought_key, get_redis, stock_key
from models.seckill import SeckillOrderEntity, SeckillProductEntity
from schemas.error import (
    AlreadyBoughtError,
    AppError,
    ConflictError,
    NotFoundError,
    NotWarmedError,
    SoldOutError,
)
from schemas.seckill import (
    SeckillBuyVO,
    SeckillOrderVO,
    SeckillProductCreate,
    SeckillProductVO,
    SeckillStockVO,
)

# 读入 Lua（项目根/lua/seckill_buy.lua）
_LUA_PATH = Path(__file__).resolve().parents[1] / "lua" / "seckill_buy.lua"
SECKILL_BUY_LUA = _LUA_PATH.read_text(encoding="utf-8")


def _to_product_vo(p: SeckillProductEntity) -> SeckillProductVO:
    return SeckillProductVO.model_validate(p)


class SeckillService:
    @staticmethod
    def create_product(db: Session, dto: SeckillProductCreate) -> SeckillProductVO:
        entity = SeckillProductEntity(
            name=dto.name,
            stock=dto.stock,
            seckill_price=dto.seckill_price,
            status=1,
        )
        db.add(entity)
        db.flush()
        db.refresh(entity)
        return _to_product_vo(entity)

    @staticmethod
    def warm(db: Session, r: Redis, product_id: int) -> SeckillStockVO:
        product = db.get(SeckillProductEntity, product_id)
        if product is None or product.status != 1:
            raise NotFoundError("商品不存在或未上架")

        sk = stock_key(product_id)
        bk = bought_key(product_id)

        # 预热：覆盖库存；清空已买集合（演示可重复预热；生产要按活动版本号设计）
        pipe = r.pipeline()
        pipe.set(sk, product.stock)
        pipe.delete(bk)
        pipe.execute()

        return SeckillStockVO(
            product_id=product_id,
            redis_stock=product.stock,
            warmed=True,
        )

    @staticmethod
    def get_stock(r: Redis, product_id: int) -> SeckillStockVO:
        sk = stock_key(product_id)
        val = r.get(sk)
        if val is None:
            return SeckillStockVO(product_id=product_id, redis_stock=0, warmed=False)
        return SeckillStockVO(
            product_id=product_id,
            redis_stock=int(val),
            warmed=True,
        )

    @staticmethod
    def buy(db: Session, r: Redis, *, user_id: int, product_id: int) -> SeckillBuyVO:
        sk = stock_key(product_id)
        bk = bought_key(product_id)

        if r.get(sk) is None:
            raise NotWarmedError("请先预热库存")

        # 1) Redis 原子扣减
        result = int(
            r.eval(SECKILL_BUY_LUA, 2, sk, bk, str(user_id))
        )
        if result == -1:
            raise SoldOutError()
        if result == -2:
            raise AlreadyBoughtError()
        if result != 1:
            raise AppError("秒杀失败", code=500)

        # 2) 落库订单；失败必须补偿 Redis
        order = SeckillOrderEntity(user_id=user_id, product_id=product_id)
        try:
            db.add(order)
            db.flush()
            db.refresh(order)
        except IntegrityError:
            db.rollback()
            # 唯一索引冲突：DB 认为已买过 → 补偿 Redis
            SeckillService._compensate(r, sk, bk, user_id)
            raise AlreadyBoughtError() from None
        except Exception:
            db.rollback()
            SeckillService._compensate(r, sk, bk, user_id)
            raise

        return SeckillBuyVO(
            order_id=order.id,
            product_id=product_id,
            user_id=user_id,
        )

    @staticmethod
    def _compensate(r: Redis, sk: str, bk: str, user_id: int) -> None:
        """DB 失败时回滚 Redis 侧扣减，避免库存被永久吃掉。"""
        pipe = r.pipeline()
        pipe.incr(sk)
        pipe.srem(bk, str(user_id))
        pipe.execute()

    @staticmethod
    def list_my_orders(db: Session, user_id: int) -> list[SeckillOrderVO]:
        rows = db.scalars(
            select(SeckillOrderEntity)
            .where(SeckillOrderEntity.user_id == user_id)
            .order_by(SeckillOrderEntity.id.desc())
        ).all()
        return [SeckillOrderVO.model_validate(o) for o in rows]


seckill_service = SeckillService()
```

> 关于 `db.rollback()`：若你已在 `get_db` 统一 rollback，这里 `IntegrityError` 后仍建议 `rollback()` 清掉失败事务状态，再让请求以业务异常结束；具体以你当前 `get_db` 实现为准，避免 Session 处于「需要 rollback」却继续用。

依赖注入 Redis：可在 `core/deps.py` 增加：

```python
from core.redis_client import get_redis
from redis import Redis

def get_redis_dep() -> Redis:
    return get_redis()
```

---

## 9. Router：`routers/seckill.py`

```python
from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user, get_redis_dep  # 按你实际 deps 命名
from models.user import UserEntity
from schemas.error import AppError
from schemas.seckill import SeckillProductCreate
from services.seckill_service import seckill_service
from utils.response import Result

router = APIRouter(prefix="/seckill", tags=["秒杀"])


def _handle_app_error(exc: AppError) -> NoReturn:
    raise HTTPException(status_code=exc.code, detail=exc.message) from exc


@router.post("/product", response_model=Result)
def create_product(
    dto: SeckillProductCreate,
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),
) -> Result:
    vo = seckill_service.create_product(db, dto)
    return Result.success(data=vo.model_dump(mode="json"), msg="创建成功")


@router.post("/warm/{product_id}", response_model=Result)
def warm(
    product_id: int,
    db: Session = Depends(get_db),
    r: Redis = Depends(get_redis_dep),
    _: UserEntity = Depends(get_current_user),
) -> Result:
    try:
        vo = seckill_service.warm(db, r, product_id)
    except AppError as exc:
        _handle_app_error(exc)
    return Result.success(data=vo.model_dump(), msg="预热成功")


@router.get("/stock/{product_id}", response_model=Result)
def stock(
    product_id: int,
    r: Redis = Depends(get_redis_dep),
    _: UserEntity = Depends(get_current_user),
) -> Result:
    vo = seckill_service.get_stock(r, product_id)
    return Result.success(data=vo.model_dump())


@router.post("/buy/{product_id}", response_model=Result)
def buy(
    product_id: int,
    db: Session = Depends(get_db),
    r: Redis = Depends(get_redis_dep),
    current_user: UserEntity = Depends(get_current_user),
) -> Result:
    try:
        vo = seckill_service.buy(
            db, r, user_id=current_user.id, product_id=product_id
        )
    except AppError as exc:
        _handle_app_error(exc)
    return Result.success(data=vo.model_dump(), msg="秒杀成功")


@router.get("/orders/me", response_model=Result)
def my_orders(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> Result:
    rows = seckill_service.list_my_orders(db, current_user.id)
    return Result.success(data=[x.model_dump(mode="json") for x in rows])
```

`Decimal` 序列化：用 `model_dump(mode="json")` 更稳。

### 汇总路由

`routers/__init__.py`：

```python
from routers import auth, user, seckill

api_router.include_router(seckill.router)
```

---

## 10. 验收步骤

```powershell
docker compose up -d
poetry run uvicorn main:app --reload --port 8000
```

1. 登录拿 token → Authorize  
2. `POST /seckill/product`  

```json
{ "name": "测试手机", "stock": 5, "seckill_price": "99.00" }
```

3. `POST /seckill/warm/{id}`  
4. `GET /seckill/stock/{id}` → `redis_stock=5`, `warmed=true`  
5. 用户 A：`POST /seckill/buy/{id}` → 成功；再买 → 重复购买  
6. 换用户 B（再建一个用户并登录）继续买，直到售罄  
7. 连续/多用户合计成功次数 **≤ 5**，库存不为负  
8. `GET /seckill/orders/me` 能看到自己的单  

### 建议压测心智（手工也行）

库存 5，同一用户狂点：最多成功 1 次。  
5 个用户各买 1 次：成功 5；第 6 人售罄。

---

## 11. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| Connection refused 6379 | Redis 没起 / 端口不对 | `docker compose ps`，检查 `.env` |
| 未预热 | 没 warm 或 key 被清 | 先 warm |
| 超卖 | 没用 Lua / 分步扣减 | 必须 eval 整段脚本 |
| Redis 扣了但无订单 | DB 失败且未补偿 | 检查 `_compensate` |
| `IntegrityError` 后 Session 脏 | 未 rollback | 捕获后 `db.rollback()` |
| Decimal JSON 报错 | dump 模式 | `model_dump(mode="json")` |

---

## 12. 与真实秒杀的差距（必读）

| 真实常见 | 本 Demo |
|---|---|
| 网关/接口限流、验证码、设备指纹 | 无 |
| MQ 削峰、异步创单 | 同步写订单 |
| 库存服务独立、多级缓存 | 单 Redis + 单库 |
| 对账：Redis vs DB 定时校准 | 仅补偿路径 |
| 活动时间窗、预约、分片库存 | 无 |
| 分布式锁 / 集群 Lua 同 slot | 单机 Redis 足够学原理 |

你要带走的能力：**热点读改走 Redis + Lua 原子性 + DB 唯一约束兜底 + 失败补偿**。

---

## 13. 完成检查清单

- [ ] Compose 中 Redis 可连，`REDIS_URL` 正确  
- [ ] 两张表已建，订单有唯一索引  
- [ ] 预热后 stock key 有值  
- [ ] Lua 返回 -1/-2/1 三种路径都测过  
- [ ] 不超卖、不重复买  
- [ ] DB 失败有补偿（可人为制造唯一冲突验证）  
- [ ] 路由已挂到 `api_router`  
- [ ] 知道 Demo 与真实秒杀差距  

→ Step 5：CORS / README / 锁文件与启动说明收尾。

---

## 14. 文件清单（手敲对照）

```text
fastApiDemo/
├── docker-compose.yml          # + redis
├── lua/seckill_buy.lua
├── sql/seckill_product.sql
├── sql/seckill_order.sql
├── core/redis_client.py
├── core/deps.py                # + get_redis_dep
├── models/seckill.py
├── schemas/seckill.py
├── schemas/error.py            # + SoldOut/AlreadyBought/NotWarmed
├── services/seckill_service.py
└── routers/seckill.py
```
