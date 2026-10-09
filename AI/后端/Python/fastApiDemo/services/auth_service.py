from sqlalchemy.orm import Session
from sqlalchemy import select

from models.user import UserEntity
from schemas.auth import TokenVO
from core.security import create_access_token, verify_password

class AuthError(Exception):
    def __init__(self, message: str = "用户名或密码错误") -> None:
        self.message = message
        super().__init__(message) # 用当前实例的message初始化父类Exception的message

class AuthService:
    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> UserEntity:
        stmt = select(UserEntity).where(
            UserEntity.username == username,
            UserEntity.deleted_at.is_(None)
        )
        user = db.scalar(stmt)

        if user is None or not verify_password(password, user.password):
            raise AuthError()

        if user.status != 1:
            raise AuthError()
        
        return user

    @staticmethod
    def issue_token(user: UserEntity) -> TokenVO:
        token = create_access_token(
            subject=str(user.id),
            extra_claims={"username": user.username}
        )

        return TokenVO(
            access_token=token,
        )

    @staticmethod
    def login(db: Session, username: str, password: str) -> TokenVO:
        user = AuthService.authenticate(db, username, password)
        return AuthService.issue_token(user)

auth_service = AuthService()

