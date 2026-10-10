
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class SeckillProductCreateDTO(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    stock: int = Field(ge=0, le=10000)
    seckill_price: Decimal = Field(ge=0)

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
    redis_stock: int # 缓存中的库存
    warmed: bool # 是否预热

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