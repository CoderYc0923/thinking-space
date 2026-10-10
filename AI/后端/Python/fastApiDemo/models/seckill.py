



from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, Numeric, String, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class SeckillProductEntity(Base):
    __tablename__ = "seckill_product"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seckill_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SeckillOrderEntity(Base):
    __tablename__ = "seckill_order"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uk_user_product")
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)