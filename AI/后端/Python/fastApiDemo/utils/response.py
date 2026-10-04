from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# 统一响应体
# 需要自己转成dict， pydantic v1 用.dict()， pydantic v2 用.model_dump()
class Result(BaseModel):
    code: int
    msg: str
    data: Any | None = None

    @staticmethod
    def success(data: Any = None, msg: str = "success") -> Result:
        return Result(code=200, msg=msg, data=data)

    @staticmethod
    def error(code: int = 500, msg: str = "error") -> Result:
        return Result(code=code, msg=msg, data=None)
