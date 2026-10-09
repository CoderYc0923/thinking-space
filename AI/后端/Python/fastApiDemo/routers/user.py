from fastapi import APIRouter, Depends

from core.deps import get_current_user
from models.user import UserEntity
from schemas.user import UserVO
from utils.response import Result

router = APIRouter(prefix="/user", tags=["用户管理"])


@router.get("/info", response_model=Result)
def get_user_info(current_user: UserEntity = Depends(get_current_user)) -> Result:
    # from_attributes=True 时，才能把 ORM Entity 转成 UserVO
    return Result.success(data=UserVO.model_validate(current_user).model_dump())
