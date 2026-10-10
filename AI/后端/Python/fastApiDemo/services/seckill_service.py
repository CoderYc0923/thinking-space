
from pathlib import Path

from redis import Redis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.redis_client import bought_key, stock_key
from models.seckill import SeckillOrderEntity, SeckillProductEntity
from schemas.error import AppError, NotFoundError, SeckillAlreadyBoughtError, SeckillSoldOutError
from schemas.seckill import SeckillBuyVO, SeckillOrderVO, SeckillProductCreateDTO, SeckillProductVO, SeckillStockVO


_LUA_PATH = Path(__file__).resolve().parents[1] / "lua" / "seckill_buy.lua"
SECKILL_BUY_LUA = _LUA_PATH.read_text(encoding="utf-8")

def _to_product_vo(p: SeckillProductEntity) -> SeckillProductVO:
    return SeckillProductVO.model_validate(p)

class SeckillService:
    @staticmethod
    def create_product(db: Session, dto: SeckillProductCreateDTO) -> SeckillProductVO:
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
    def warm_up_stock(db: Session, r: Redis, product_id: int) -> SeckillStockVO:
        p = db.get(SeckillProductEntity, product_id)
        if p is None:
            raise NotFoundError("商品不存在")
        
        sk = stock_key(product_id)
        bk = bought_key(product_id)

        # 预热库存
        pipe = r.pipeline()
        pipe.set(sk, p.stock)
        pipe.delete(bk)
        pipe.execute()

        return SeckillStockVO(
            product_id=product_id,
            redis_stock=p.stock,
            warmed=True,
        )

    @staticmethod
    def get_stock(r: Redis, product_id: int) -> SeckillStockVO:
        sk = stock_key(product_id)
        value = r.get(sk)
        if value is None:
            return SeckillStockVO(
                product_id=product_id,
                redis_stock=0,
                warmed=False,
            )

        return SeckillStockVO(
            product_id=product_id,
            redis_stock=int(value),
            warmed=True,
        )

    @staticmethod
    def buy(db: Session, r: Redis, *, user_id: int, product_id: int) -> SeckillBuyVO:
        sk = stock_key(product_id)
        bk = bought_key(product_id)

        if r.get(sk) is None:
            raise AppError("商品不存在")
        
        # redis lua 原子扣减库存
        res = int(r.eval(SECKILL_BUY_LUA, 2, sk, bk, str(user_id)))

        if res == -1:
            raise SeckillSoldOutError()
        if res == -2:
            raise SeckillAlreadyBoughtError()
        if res != 1:
            raise AppError("秒杀失败", code=500)
        
        # 落库
        order = SeckillOrderEntity(
            user_id=user_id,
            product_id=product_id,
        )
        try:
            db.add(order)
            db.flush()
            db.refresh(order)
        except IntegrityError:
            db.rollback()
            # 唯一索引冲突：DB认为买过了，补偿redis
            SeckillService._compensate(r, sk, bk, user_id)
            raise SeckillAlreadyBoughtError() from None
        except Exception:
            db.rollback()
            SeckillService._compensate(r, sk, bk, user_id)
            raise

        return SeckillBuyVO(
            product_id=product_id,
            order_id=order.id,
            user_id=user_id,
        )

    @staticmethod
    def _compensate(r: Redis, sk: str, bk: str, user_id: int):
        """补偿redis库存"""

        pipe = r.pipeline()
        pipe.incr(sk) # incr 增加1
        pipe.srem(bk, str(user_id)) # srem 删除元素
        pipe.execute()

    @staticmethod
    def list_my_orders(db: Session, user_id: int) -> list[SeckillOrderVO]:
        rows = db.scalars(
            select(SeckillOrderEntity)
            .where(SeckillOrderEntity.user_id == user_id)
            .order_by(SeckillOrderEntity.created_at.desc())
        ).all()

        return [SeckillOrderVO.model_validate(o) for o in rows]


seckill_service = SeckillService()