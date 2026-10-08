from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.MYSQL_URL,
)

# 创建数据库会话
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

class Base(DeclarativeBase):
    """所有ORM Entity 的基类"""
    pass # pass是空实现，让子类去实现


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 依赖注入的会话，请求进来后，会创建一个会话，请求结束后，会关闭会话。
    类似：try { SqlSession } finally { close}
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

