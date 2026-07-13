"""采集会话写入路径。

将 DLMS 采集引擎产出的原始文档写入 MongoDB，
同时在 PG col_session 表创建桥梁记录。

双写一致性策略：PG 先登记 pending → Mongo 写入 → PG 补全。
"""

import datetime
import logging

import bson
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.mongo import get_mongo_db
from app.models.session import CollectionSession
from app.services.mongo_session_repo import MongoSessionRepo

logger = logging.getLogger(__name__)

_MAX_DOC_BYTES = 15 * 1024 * 1024  # 15MB 安全阈值（16MB 为硬限）


async def save_collection_session(
    db: AsyncSession,
    meter_id: int,
    meter_serial: str,
    project_id: int | None,
    project_name: str,
    raw_doc: dict,
    source: str = "import",
    source_file: str = "",
    connection_type: str = "HDLC",
    task_id: int | None = None,
) -> CollectionSession:
    """将原始采集文档写入 Mongo，并在 PG 创建桥梁记录。

    返回：PG CollectionSession 对象
    """
    mongo_db = get_mongo_db()
    repo = MongoSessionRepo(mongo_db)

    collected_at = _parse_timestamp(raw_doc.get("timestamp"))
    imported_at = datetime.datetime.now(datetime.timezone.utc)
    summary = raw_doc.get("summary", {})

    total_read = summary.get("total_read", 0)
    total_success = summary.get("total_success", 0)
    total_failed = summary.get("total_failed", 0)

    # ── 步骤 1: PG 先登记（status=pending），获取 session.id ──
    session = CollectionSession(
        meter_id=meter_id,
        project_id=project_id,
        task_id=task_id,
        mongo_db=settings.MONGODB_DATABASE,
        mongo_collection=MongoSessionRepo.COLLECTION,
        mongo_doc_id="",  # 待 Mongo 写入后补全
        source=source,
        source_file=source_file,
        started_at=collected_at,
        finished_at=imported_at,
        duration_ms=int((imported_at - collected_at).total_seconds() * 1000),
        status="pending",
        total_read=total_read,
        total_success=total_success,
        total_failed=total_failed,
        sheet_count=len(raw_doc.get("sheets", {})),
        connection_type=connection_type,
    )
    db.add(session)
    await db.flush()  # 获取 session.id（不 commit，保持事务）

    # ── 步骤 2: 构建 Mongo 文档（含 session_id 反向指针） ──
    mongo_status = _derive_status(total_read, total_failed)
    mongo_doc = {
        "session_id": session.id,
        "meter_id": meter_id,
        "meter_serial": meter_serial,
        "project_id": project_id,
        "project_name": project_name,
        "task_id": task_id,
        "collected_at": collected_at,
        "imported_at": imported_at,
        "source": source,
        "source_file": source_file,
        "connection_type": connection_type,
        "status": mongo_status,
        "total_points": total_read,
        "success_points": total_success,
        "failed_points": total_failed,
        "sheets": raw_doc.get("sheets", {}),
        "key_value_pairs": raw_doc.get("key_value_pairs", {}),
        "summary": summary,
        "schema_version": 1,
    }

    # ── 步骤 2a: 文档大小检查 ──
    try:
        doc_size = len(bson.encode(mongo_doc))
        if doc_size > _MAX_DOC_BYTES:
            raise ValueError(
                f"MongoDB 文档大小 {doc_size / 1024 / 1024:.1f}MB 超过 15MB 安全阈值，"
                f"需拆分 Profile buffer 到独立集合"
            )
    except ValueError:
        raise
    except Exception:
        # bson.encode 可能因类型问题失败，此时跳过大小检查继续写入
        logger.warning("bson.encode 失败，跳过文档大小检查")

    # ── 步骤 3: 写入 Mongo ──
    mongo_id = await repo.insert_session(mongo_doc)

    # ── 步骤 4: 更新 PG 记录（补全 mongo_doc_id + 状态映射） ──
    session.mongo_doc_id = mongo_id
    session.status = _map_status(mongo_status)
    await db.flush()

    logger.info(
        "采集会话已保存: session_id=%d, meter_id=%d, mongo_doc_id=%s, status=%s",
        session.id,
        meter_id,
        mongo_id,
        session.status,
    )
    return session


def _parse_timestamp(ts: str | None) -> datetime.datetime:
    """解析采集文档 timestamp 字段（ISO 格式字符串）。"""
    if not ts:
        return datetime.datetime.now(datetime.timezone.utc)
    try:
        return datetime.datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return datetime.datetime.now(datetime.timezone.utc)


def _derive_status(total_read: int, total_failed: int) -> str:
    """根据采集统计推导 Mongo 数据质量状态。

    返回值: success / partial / failed（Mongo 枚举）
    """
    if total_read == 0:
        return "failed"
    if total_failed == 0:
        return "success"
    if total_failed < total_read:
        return "partial"
    return "failed"


def _map_status(mongo_status: str) -> str:
    """Mongo 数据质量枚举 → PG 生命周期枚举。"""
    return "failed" if mongo_status == "failed" else "completed"
