"""WebSocket 端点。

前端通过 ``ws://host/ws?token=<accessToken>`` 连接，
连接后发送 ``{"action": "subscribe", "topics": [...]}`` 订阅 topic。

消息格式见 ``app/core/ws_manager.py``。
"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.core.ws_manager import SUPPORTED_TOPICS, manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    """WebSocket 主端点。

    认证流程：
      1. 从查询参数 ``token`` 解码 JWT
      2. 验证失败则关闭连接（code=4001）
      3. 验证成功则接受连接，进入消息循环

    消息循环：
      - 接收 ``{"action": "subscribe", "topics": [...]}``
      - 接收 ``{"action": "unsubscribe", "topics": [...]}``
      - 连接断开时清理订阅
    """
    # ── 认证 ──
    if not token:
        await websocket.close(code=4001, reason="缺少 token 参数")
        return

    payload = decode_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="token 无效或已过期")
        return

    user_id = payload.get("id")
    username = payload.get("sub", "unknown")
    if not user_id:
        await websocket.close(code=4001, reason="token 中无用户信息")
        return

    # ── 接受连接 ──
    await manager.connect(websocket)
    logger.info("WebSocket 用户已连接: %s (id=%s)", username, user_id)

    # 发送欢迎消息（含可用 topic 列表）
    await websocket.send_text(
        json.dumps(
            {
                "topic": "system",
                "type": "connected",
                "data": {
                    "message": "WebSocket 连接成功",
                    "available_topics": sorted(SUPPORTED_TOPICS),
                },
            },
            ensure_ascii=False,
        )
    )

    # ── 消息循环 ──
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps(
                        {
                            "topic": "system",
                            "type": "error",
                            "data": {"message": "无效的 JSON 格式"},
                        },
                        ensure_ascii=False,
                    )
                )
                continue

            action = msg.get("action")
            topics = msg.get("topics", [])

            if action == "subscribe":
                accepted = manager.subscribe(websocket, topics)
                await websocket.send_text(
                    json.dumps(
                        {
                            "topic": "system",
                            "type": "subscribed",
                            "data": {"topics": accepted},
                        },
                        ensure_ascii=False,
                    )
                )

            elif action == "unsubscribe":
                manager.unsubscribe(websocket, topics)
                await websocket.send_text(
                    json.dumps(
                        {
                            "topic": "system",
                            "type": "unsubscribed",
                            "data": {"topics": topics},
                        },
                        ensure_ascii=False,
                    )
                )

            else:
                await websocket.send_text(
                    json.dumps(
                        {
                            "topic": "system",
                            "type": "error",
                            "data": {"message": f"未知 action: {action}"},
                        },
                        ensure_ascii=False,
                    )
                )

    except WebSocketDisconnect:
        logger.info("WebSocket 用户断开: %s", username)
    except Exception as e:
        logger.warning("WebSocket 异常: %s", e)
    finally:
        await manager.disconnect(websocket)
