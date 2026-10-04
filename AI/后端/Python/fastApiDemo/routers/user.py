from fastapi import APIRouter
from models.user import UserDTO, UserVO
from services.user_service import user_service
from utils.response import Result

router = APIRouter(prefix="/user", tags=["用户管理"])


@router.post("/add")
def add_user(user: UserDTO):
    user_vo = user_service.create_user(user)
    return Result.success(data=user_vo)


@router.get("/{user_id}")
def get_user_info(user_id: int):
    user_vo = UserVO(id=user_id, name="Cyrus", age=20)
    return Result.success(data=user_vo)
