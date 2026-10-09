from fastapi import APIRouter, Depends

from core.deps import get_current_user
from models.user import UserEntity
from schemas.user import UserVO
from utils.response import Result

router = APIRouter(prefix="/user", tags=["用户管理"])

