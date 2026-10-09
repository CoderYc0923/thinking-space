from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from models.user import UserEntity
from schemas.common import PageVO
from schemas.user import CreateUserDTO, UpdateUserDTO, UserVO
from schemas.error import AppError
from services.user_service import user_service
from utils.response import Result

router = APIRouter(prefix="/user", tags=["用户管理"])


def _handle_app_error(exc: AppError) -> NoReturn:
    """NoReturn：告诉类型检查器此函数必定抛出，不会正常返回。"""
    raise HTTPException(status_code=exc.code, detail=exc.message) from exc


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
    dto: CreateUserDTO,
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),
) -> Result:
    try:
        vo = user_service.create(db, dto)
    except AppError as exc:
        _handle_app_error(exc)
    return Result.success(data=vo.model_dump(), msg="创建成功")


@router.put("/{user_id}", response_model=Result)
def update_user(
    user_id: int,
    dto: UpdateUserDTO,
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),
) -> Result:
    try:
        vo = user_service.update(db, user_id, dto)
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
        user_service.delete(db, user_id, operator_id=current_user.id)
    except AppError as exc:
        _handle_app_error(exc)
    return Result.success(msg="删除成功")