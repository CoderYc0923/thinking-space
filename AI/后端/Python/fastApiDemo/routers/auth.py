

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from models.user import UserEntity
from schemas.user import UserVO
from services.auth_service import AuthError, auth_service
from utils.response import Result


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Result)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Result:
    try:
        token = auth_service.login(db, form_data.username, form_data.password)
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"}
        ) from e
    
    return Result.success(data=token.model_dump())

@router.get("/info", response_model=Result)
def get_user_info(current_user: UserEntity = Depends(get_current_user)) -> Result:
    # from_attributes=True 时，才能把 ORM Entity 转成 UserVO
    return Result.success(data=UserVO.model_validate(current_user).model_dump())