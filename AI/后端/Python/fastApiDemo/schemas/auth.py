from pydantic import BaseModel, Field

class TokenVO(BaseModel):
    access_token: str

class LoginDTO(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=8, max_length=64)
