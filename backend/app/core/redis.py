"""Redis 异步客户端单例。

提供进程级 Redis 连接池，支持 JSON 序列化的 get/set/cached 模式。

用法：
    from app.core.redis import get_redis, cached

    redis = await get_redis()
    await redis.set("key", "value", ex=30)

    # 或使用缓存装饰器
    data = await cached("screen:overview", ttl=30, fetch_func=fetch_from_db)
"""

import json
import logging
from typing import Any, Awaitable, Callable

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """获取/初始化 Redis 客户端单例（懒加载）。"""
    global _client
    if _client is None:
        _client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _client


async def close_redis() -> None:
    """关闭 Redis 连接。"""
    global _client
    if _client:
        await _client.aclose()
        _client = None


async def cache_get(key: str) -> Any | None:
    """从 Redis 获取 JSON 缓存值。返回 None 表示未命中。"""
    try:
        redis = await get_redis()
        raw = await redis.get(key)
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning("Redis cache_get 失败: %s", e)
    return None


async def cache_set(key: str, value: Any, ttl: int = 30) -> None:
    """写入 JSON 缓存值，TTL 秒。"""
    try:
        redis = await get_redis()
        await redis.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=ttl)
    except Exception as e:
        logger.warning("Redis cache_set 失败: %s", e)


async def cached(key: str, ttl: int, fetch_func: Callable[[], Awaitable[Any]]) -> Any:
    """缓存装饰器：先查 Redis，未命中则调用 fetch_func 并缓存结果。

    Redis 不可用时直接调用 fetch_func，不影响功能。
    """
    # 先查缓存
    cached_val = await cache_get(key)
    if cached_val is not None:
        return cached_val

    # 未命中，查源数据
    result = await fetch_func()

    # 写入缓存（失败不影响返回）
    await cache_set(key, result, ttl)

    return result


async def cache_delete(key: str) -> None:
    """删除缓存键。"""
    try:
        redis = await get_redis()
        await redis.delete(key)
    except Exception as e:
        logger.warning("Redis cache_delete 失败: %s", e)
