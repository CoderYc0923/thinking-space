from multiprocessing import Value
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from jose import JWTError

from core.database import get_db
from core.security import decode_access_token
from models.user import UserEntity


# 从请求中取出Bearer Token，并告诉Swagger登陆地址在哪
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserEntity:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或登录已过期",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError, TypeError):
        # from None 就是告诉异常的来源是None，不用关联上面的JWTError, ValueError, TypeError，不必暴露具体的异常信息
        raise credentials_exception from None

    user = db.scalar(
        select(UserEntity).where(
            UserEntity.id == user_id,
            UserEntity.deleted_at.is_(None)
        )
    )

    if user is None or user.status != 1:
        raise credentials_exception
    
    return user


