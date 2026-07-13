"""MongoDB 异步客户端（motor）。

职责：
  - 单例 AsyncIOMotorClient（进程级连接池）
  - 提供 get_mongo() 依赖注入
  - 读取 MONGODB_URL 环境变量
"""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """获取/初始化 Motor 客户端单例（懒加载）。"""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URL)
        logger.info("MongoDB 客户端已初始化: %s", settings.MONGODB_URL)
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    """获取默认数据库句柄。"""
    return get_mongo_client()[settings.MONGODB_DATABASE]


async def get_mongo() -> AsyncIOMotorDatabase:
    """FastAPI 依赖注入入口。"""
    return get_mongo_db()


async def close_mongo():
    """应用关闭时清理连接。"""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("MongoDB 客户端已关闭")
