from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "MiniHES"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = [
        "http://localhost:5666",
        "http://localhost:5173",
        "http://localhost:5320",
    ]

    DATABASE_URL: str = "postgresql+asyncpg://minihes:minihes@localhost:5432/minihes"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    REDIS_URL: str = "redis://localhost:6379/0"

    # MongoDB（原始采集文档存储）
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "minihes"

    # DEPRECATED: InfluxDB 已弃用，时序数据改用 PostgreSQL 时序表
    # (col_meter_reading + col_reading_daily_summary)。
    # 配置项保留备未来高并发场景复用，当前无任何代码读写 InfluxDB。
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = ""
    INFLUXDB_ORG: str = "metering"
    INFLUXDB_BUCKET: str = "metering"

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # SMTP 邮件服务
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    COLLECTOR_MAX_WORKERS: int = 10
    COLLECTOR_DEFAULT_TIMEOUT: int = 30
    COLLECTOR_RETRY_TIMES: int = 3

    class Config:
        env_file = ".env"


settings = Settings()
