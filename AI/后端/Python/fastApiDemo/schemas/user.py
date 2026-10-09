from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserDTO(BaseModel):
    """创建用户入参（Step 3 会用到）"""

    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=64)
    nickname: str | None = None
    age: int | None = Field(default=None, ge=0, le=150)
    email: str | None = None
    phone: str | None = None


class UserVO(BaseModel):
    """对外用户视图：不含 password；可从 ORM Entity 转换"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str | None = None
    age: int | None = None
    email: str | None = None
    phone: str | None = None
    status: int
    created_at: datetime | None = None
