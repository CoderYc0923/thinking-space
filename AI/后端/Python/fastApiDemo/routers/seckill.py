from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from sqlalchemy.orm import Session

from core.deps import get_current_user, get_db, get_redis_dep
from models.user import UserEntity
from schemas.error import AppError
from schemas.seckill import SeckillProductCreateDTO
from services.seckill_service import seckill_service
from utils.response import Result


router = APIRouter(prefix="/seckill", tags=["秒杀"])


def _handle_app_error(exc: AppError) -> NoReturn:
    raise HTTPException(status_code=exc.code, detail=exc.message) from exc


@router.post("/product", response_model=Result)
def create_product(
    dto: SeckillProductCreateDTO,
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),
) -> Result:
    vo = seckill_service.create_product(db, dto)
    # decimal用json序列化会丢失精度，所以用model_dump(mode="json")
    return Result.success(data=vo.model_dump(mode="json"), msg="创建商品成功")


@router.post("/warm/{product_id}", response_model=Result)
def warm_up_stock(
    product_id: int,
    db: Session = Depends(get_db),
    r: Redis = Depends(get_redis_dep),
    _: UserEntity = Depends(get_current_user),
) -> Result:
    try:
        vo = seckill_service.warm_up_stock(db, r, product_id)
    except AppError as e:
        _handle_app_error(e)
    
    return Result.success(data=vo.model_dump(), msg="预热库存成功")


@router.get("/stock/{product_id}", response_model=Result)
def get_stock(
    product_id: int,
    r: Redis = Depends(get_redis_dep),
    _: UserEntity = Depends(get_current_user),
) -> Result:
    vo = seckill_service.get_stock(r, product_id)
    return Result.success(data=vo.model_dump(), msg="获取库存成功")



@router.post("/buy/{product_id}", response_model=Result)
def buy(
    product_id: int,
    db: Session = Depends(get_db),
    r: Redis = Depends(get_redis_dep),
    current_user: UserEntity = Depends(get_current_user),
) -> Result:

    try:
        vo = seckill_service.buy(db, r, user_id=current_user.id, product_id=product_id)
    except AppError as e:
        _handle_app_error(e)

    return Result.success(data=vo.model_dump(), msg="秒杀成功")



@router.get("/orders", response_model=Result)
def list_my_orders(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> Result:
    orders = seckill_service.list_my_orders(db, current_user.id)
    return Result.success(data=[o.model_dump(mode="json") for o in orders], msg="获取订单成功")
