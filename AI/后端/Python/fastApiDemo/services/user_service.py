from datetime import datetime
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from core.security import hash_password
from models.user import UserEntity
from schemas.common import PageVO
from schemas.error import ConflictError, NotFoundError
from schemas.user import CreateUserDTO, UpdateUserDTO, UserVO


def _to_vo(user: UserEntity) -> UserVO:
    return UserVO.model_validate(user)


def _get_user_by_id(db: Session, user_id: int) -> UserEntity:
    user = db.scalar(
        select(UserEntity).where(
            UserEntity.id == user_id,
            UserEntity.deleted_at.is_(None),
        )
    )

    if user is None:
        raise NotFoundError("用户不存在")

    return user


def _apply_user_filters[T](stmt: Select[T], keyword: str | None) -> Select[T]:
    """未软删 + 可选关键字（用户名/昵称）。"""
    stmt = stmt.where(UserEntity.deleted_at.is_(None))
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                UserEntity.username.like(like),
                UserEntity.nickname.like(like),
            )
        )
    return stmt


class UserService:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> UserVO:
        return _to_vo(_get_user_by_id(db, user_id))

    @staticmethod
    def list_users(
        db: Session,
        *,
        page: int = 1,
        size: int = 10,
        keyword: str | None = None,
    ) -> PageVO[UserVO]:
        page = max(page, 1)
        size = min(max(size, 1), 100)

        count_stmt = _apply_user_filters(
            select(func.count()).select_from(UserEntity),
            keyword,
        )
        total = db.scalar(count_stmt) or 0

        list_stmt = _apply_user_filters(select(UserEntity), keyword)
        rows = db.scalars(
            list_stmt.order_by(UserEntity.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()

        return PageVO(
            list=[_to_vo(u) for u in rows],
            total=total,
            page=page,
            size=size,
        )

    @staticmethod
    def create(db: Session, dto: CreateUserDTO) -> UserVO:
        exists = db.scalar(
            select(UserEntity.id).where(
                UserEntity.username == dto.username,
                UserEntity.deleted_at.is_(None),
            )
        )
        if exists is not None:
            raise ConflictError("用户名已存在")

        entity = UserEntity(
            username=dto.username,
            password=hash_password(dto.password),
            nickname=dto.nickname,
            age=dto.age,
            email=dto.email,
            phone=dto.phone,
            status=1,
        )
        db.add(entity)
        db.flush() # 把SQL发送到数据库，但不会提交
        db.refresh(entity) # 用库中的最新值更新内存中的对象

        return _to_vo(entity)

    @staticmethod
    def update(db: Session, user_id: int, dto: UpdateUserDTO) -> UserVO:
        user = _get_user_by_id(db, user_id)
        
        # exclude_unsert: 只更新请求中出现的字段
        data = dto.model_dump(exclude_unset=True)

        if "password" in data:
            plain = data.pop("password")
            if plain:
                user.password = hash_password(plain)

        if "status" in data and data["status"] != user.status:
            if data["status"] not in (1, 2):
                raise ConflictError("状态值不合法")
            user.status = data.pop("status")

        for key, value in data.items():
            # setattr(对象, 属性名, 值) 用来动态给对象设置属性，属性名是字符串
            setattr(user, key, value)

        db.flush()
        db.refresh(user)

        return _to_vo(user)

    @staticmethod
    def delete(db: Session, user_id: int, *, operator_id: int) -> None:
        if user_id == operator_id:
            raise ConflictError("不能删除当前登录用户")
        
        user = _get_user_by_id(db, user_id)
        user.deleted_at = datetime.now()






user_service = UserService()
