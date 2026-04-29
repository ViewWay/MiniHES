from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "MiniHES"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_TYPE: str = "postgresql"
    DATABASE_URL: str = ""
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
