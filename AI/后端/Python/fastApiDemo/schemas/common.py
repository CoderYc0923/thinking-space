
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PageVO(BaseModel, Generic[T]):
    list: list[T]
    total: int
    page: int
    size: int
