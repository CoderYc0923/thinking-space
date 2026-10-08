from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """从.env文件中加载配置"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str
    MYSQL_URL: str
    REDIS_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120

settings = Settings()