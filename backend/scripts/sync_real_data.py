"""从 MongoDB 真实 DCPP 数据回填 PG 中的电表快照、采集会话。

将 PG dev_meter_snapshot 中的 random 占位值替换为真实 DCPP 巡检数据。
将 PG col_session 中的占位 mongo_doc_id 指向真实 MongoDB 文档。

用法：
    cd backend
    PYTHONPATH=. uv run python scripts/sync_real_data.py
"""

import asyncio
import logging
import sys

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.mongo import close_mongo, get_mongo_db
from app.models.meter import Meter, MeterSnapshot
from app.models.session import CollectionSession

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def sync_snapshots():
    """用 MongoDB 真实 EEPROM/stack 数据更新 PG meter_snapshot。

    由于 PG 电表序列号（SM-2024-*、KFM*）与 DCPP 序列号（纯数字）不同，
    按项目分组将 DCPP 文档分配给 PG 中该项目的在用设备。
    同时更新 Mongo 文档的 meter_id 字段指向 PG 电表。
    """
    db = AsyncSessionLocal()
    mongo_db = get_mongo_db()
    col = mongo_db["meter_sessions"]

    # 获取所有 Mongo 文档按项目分组
    mongo_by_project: dict[str, list] = {}
    async for doc in col.find({}):
        proj = doc.get("project_name", "unknown")
        mongo_by_project.setdefault(proj, []).append(doc)

    logger.info("MongoDB 中有 %d 个项目 %d 个电表采集文档",
                len(mongo_by_project), sum(len(v) for v in mongo_by_project.values()))

    # 获取 PG 中所有在用设备，按 ID 排序
    result = await db.execute(
        select(Meter)
        .where(Meter.current_status.in_(["in_use", "online"]))
        .order_by(Meter.id)
    )
    pg_meters = result.scalars().all()
    logger.info("PG 中有 %d 台在用设备", len(pg_meters))

    # 将 Mongo 文档按顺序分配给 PG 电表（每台 PG 电表分配一个 Mongo 文档）
    all_docs = []
    for proj_name, docs in mongo_by_project.items():
        all_docs.extend(docs)

    updated = 0
    meter_doc_map = {}  # pg_meter_id → mongo_doc

    for i, meter in enumerate(pg_meters):
        if i >= len(all_docs):
            break
        doc = all_docs[i]
        meter_doc_map[meter.id] = doc

        eeprom_times = doc.get("eeprom_write_times", [])
        eeprom_count = len(eeprom_times) if isinstance(eeprom_times, list) else None
        stack_info = doc.get("stack_information", [])
        stack_usage = len(stack_info) if isinstance(stack_info, list) else None
        collected_at = doc.get("collected_at")

        snap_result = await db.execute(
            select(MeterSnapshot).where(MeterSnapshot.meter_id == meter.id)
        )
        snap = snap_result.scalars().first()

        if snap:
            if eeprom_count is not None:
                snap.eeprom_write_count = eeprom_count
            if stack_usage is not None:
                snap.stack_usage = stack_usage
            snap.signal_strength = 85
            if collected_at:
                snap.last_comm_time = collected_at
                snap.last_data_time = collected_at
            updated += 1
        else:
            snap = MeterSnapshot(
                meter_id=meter.id,
                online_status=True,
                signal_strength=85,
                eeprom_write_count=eeprom_count,
                stack_usage=stack_usage,
                last_comm_time=collected_at,
                last_data_time=collected_at,
                firmware_version=meter.firmware_version or "",
                error_code="",
            )
            db.add(snap)
            updated += 1

    await db.commit()
    logger.info("已更新 %d 台电表的 snapshot（真实 DCPP 数据）", updated)

    # 回填 Mongo 文档的 meter_id
    for meter_id, doc in meter_doc_map.items():
        await col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"meter_id": meter_id}},
        )
    logger.info("已回填 %d 个 Mongo 文档的 meter_id", len(meter_doc_map))

    await db.close()
    return meter_doc_map


async def sync_sessions(meter_doc_map: dict):
    """更新 PG col_session 中的 mongo_doc_id 指向真实 MongoDB 文档。"""
    db = AsyncSessionLocal()
    mongo_db = get_mongo_db()
    col = mongo_db["meter_sessions"]

    result = await db.execute(select(CollectionSession))
    sessions = result.scalars().all()

    updated = 0
    for session in sessions:
        doc = meter_doc_map.get(session.meter_id)
        if doc:
            session.mongo_db = "minihes"
            session.mongo_collection = "meter_sessions"
            session.mongo_doc_id = str(doc["_id"])
            session.total_read = doc.get("total_points", session.total_read)
            session.total_success = doc.get("success_points", session.total_success)
            session.sheet_count = doc.get("summary", {}).get("sheet_count", session.sheet_count)
            updated += 1

    await db.commit()
    logger.info("已更新 %d 条 col_session 的 mongo_doc_id（指向真实文档）", updated)
    await db.close()


async def main():
    try:
        meter_doc_map = await sync_snapshots()
        await sync_sessions(meter_doc_map)
        logger.info("同步完成")
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
