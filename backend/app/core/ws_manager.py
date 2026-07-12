"""WebSocket 连接管理器。

负责维护 topic → WebSocket 连接的映射，提供广播接口供其他 service 调用。

消息格式（与前端 useWebSocket.ts 匹配）：
    {"topic": "...", "type": "...", "data": {...}}

前端订阅协议：
    发送: {"action": "subscribe", "topics": ["task:progress", ...]}
    发送: {"action": "unsubscribe", "topics": [...]}
"""

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# 系统支持的 topic 列表
SUPPORTED_TOPICS = frozenset(
    {
        "task:progress",
        "alarm:new",
        "meter:snapshot",
        "data:instant",
    }
)


class ConnectionManager:
    """WebSocket 连接管理器单例。

    内部维护 ``topic → set[WebSocket]`` 映射。
    所有方法都是 async 安全的（单事件循环内无需加锁）。
    """

    def __init__(self) -> None:
        # topic → set of WebSocket
        self._subscriptions: dict[str, set[WebSocket]] = {topic: set() for topic in SUPPORTED_TOPICS}
        # WebSocket → set of topics（用于断开时快速清理）
        self._client_topics: dict[WebSocket, set[str]] = {}

    # ─── 连接生命周期 ───

    async def connect(self, ws: WebSocket) -> None:
        """接受 WebSocket 连接。"""
        await ws.accept()
        self._client_topics[ws] = set()
        logger.info("WebSocket 已连接, 当前连接数: %d", len(self._client_topics))

    async def disconnect(self, ws: WebSocket) -> None:
        """断开连接并清理所有订阅。"""
        topics = self._client_topics.pop(ws, set())
        for topic in topics:
            self._subscriptions.get(topic, set()).discard(ws)
        logger.info("WebSocket 已断开, 当前连接数: %d", len(self._client_topics))

    # ─── 订阅管理 ───

    def subscribe(self, ws: WebSocket, topics: list[str]) -> list[str]:
        """为 ws 订阅 topics，返回实际订阅成功的 topic 列表。"""
        accepted: list[str] = []
        for topic in topics:
            if topic in self._subscriptions:
                self._subscriptions[topic].add(ws)
                self._client_topics.setdefault(ws, set()).add(topic)
                accepted.append(topic)
            else:
                logger.warning("未知 topic 被拒绝: %s", topic)
        return accepted

    def unsubscribe(self, ws: WebSocket, topics: list[str]) -> None:
        """取消 ws 对 topics 的订阅。"""
        for topic in topics:
            self._subscriptions.get(topic, set()).discard(ws)
            self._client_topics.get(ws, set()).discard(topic)

    # ─── 广播 ───

    async def broadcast(self, topic: str, type: str, data: Any) -> None:
        """向某 topic 的所有订阅者广播消息。

        供 alarm_engine / task_service / 等其他 service 调用。

        参数:
            topic: 目标 topic（如 "alarm:new"）
            type: 消息子类型（如 "created"、"updated"）
            data: 任意 JSON 可序列化数据
        """
        subscribers = self._subscriptions.get(topic, set())
        if not subscribers:
            return

        message = json.dumps(
            {"topic": topic, "type": type, "data": data},
            ensure_ascii=False,
            default=str,
        )
        failed: list[WebSocket] = []

        for ws in subscribers:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.warning("WebSocket 发送失败，即将清理: %s", e)
                failed.append(ws)

        # 清理已断开的连接
        for ws in failed:
            await self.disconnect(ws)

    @property
    def connection_count(self) -> int:
        """当前活跃连接数。"""
        return len(self._client_topics)

    def get_topic_subscriber_count(self, topic: str) -> int:
        """某 topic 的订阅者数量。"""
        return len(self._subscriptions.get(topic, set()))


# 全局单例
manager = ConnectionManager()
