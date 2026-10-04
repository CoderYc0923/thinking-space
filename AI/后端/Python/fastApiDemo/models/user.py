from pydantic import BaseModel, ConfigDict, Field


class UserDTO(BaseModel):
    name: str = Field(min_length=2, max_length=10, description="用户名2-10个字符")
    password: str = Field(min_length=6, max_length=16, description="密码6-16个字符")
    age: int | None = Field(default=None, description="年龄")
    email: str | None = Field(default=None, description="邮箱")


class UserVO(BaseModel):
    id: int
    name: str
    age: int | None

    # Pydantic v1
    # class Config:
    #     orm_mode = True  # 支持ORM对象转JSON（后续数据库必备）

    # Pydantic v2
    model_config = ConfigDict(from_attributes=True)
