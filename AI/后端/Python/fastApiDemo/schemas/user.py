from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateUserDTO(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=64)
    nickname: str | None = Field(default=None, min_length=2, max_length=50)
    age: int | None = Field(default=None, ge=0, le=150)
    # Pydantic v2 用 pattern，不要用已废弃的 regex
    email: str | None = Field(
        default=None,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    )
    phone: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")


class UpdateUserDTO(BaseModel):
    password: str | None = Field(default=None, min_length=6, max_length=64)
    status: int | None = Field(default=None, description="用户状态: 1-正常, 0-禁用")
    nickname: str | None = Field(default=None, min_length=2, max_length=50)
    age: int | None = Field(default=None, ge=0, le=150)
    email: str | None = Field(
        default=None,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    )
    phone: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")



class UserVO(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str | None = None
    age: int | None = None
    email: str | None = None
    phone: str | None = None
    status: int
    created_at: datetime | None = None
