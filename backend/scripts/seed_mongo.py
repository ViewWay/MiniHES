"""MongoDB 测试数据导入脚本。

从 docs/testdata/template_meter.json 读取模板文档，
为 PG 中每个电表生成采集文档写入 minihes.meter_sessions。

用法：
    cd backend
    PYTHONPATH=. uv run python scripts/seed_mongo.py
"""

import asyncio
import json
import logging
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.mongo import close_mongo, get_mongo_db
from app.models.meter import Meter, MeterSnapshot
from app.models.project import Project
from app.services.mongo_session_repo import MongoSessionRepo

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "docs"
    / "testdata"
    / "template_meter.json"
)


def load_template() -> dict:
    """加载模板文档。"""
    if not TEMPLATE_PATH.exists():
        logger.warning("模板文件不存在: %s", TEMPLATE_PATH)
        return {}
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # 规范化 MongoDB Extended JSON 格式（{"$numberInt": "123"} → 123）
    return _normalize_extended_json(raw)


def _normalize_extended_json(obj):
    """递归将 MongoDB Extended JSON 值转为 Python 原生类型。"""
    if isinstance(obj, dict):
        if "$numberInt" in obj:
            return int(obj["$numberInt"])
        if "$numberLong" in obj:
            return int(obj["$numberLong"])
        if "$numberDouble" in obj:
            return float(obj["$numberDouble"])
        return {k: _normalize_extended_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_extended_json(item) for item in obj]
    return obj


async def seed_mongo():
    """为 PG 中每个电表生成采集文档写入 MongoDB。"""
    template = load_template()
    if not template:
        logger.error("无法加载模板文档，退出")
        return

    mongo_db = get_mongo_db()
    repo = MongoSessionRepo(mongo_db)

    # 检查是否已有数据
    existing = await repo.col.count_documents({})
    if existing > 0:
        logger.info("MongoDB 已有 %d 个文档，跳过 seed", existing)
        return

    async with AsyncSessionLocal() as db:
        # 获取所有在用设备
        result = await db.execute(
            select(Meter).where(Meter.current_status == "in_use").limit(50)
        )
        meters = result.scalars().all()

        if not meters:
            logger.warning("PG 中无在用设备，无法 seed")
            return

        # 获取项目映射
        proj_result = await db.execute(select(Project))
        projects = {p.id: p for p in proj_result.scalars()}

        now = datetime.now(timezone.utc)
        count = 0

        for meter in meters:
            project = projects.get(meter.project_id)
            project_name = project.name if project else ""

            # 为每个电表生成 3 个采集文档（最近 3 天）
            for days_ago in range(3):
                collected_at = now - timedelta(days=days_ago, hours=random.randint(0, 6))

                doc = _generate_variant(
                    template, meter, project_name, collected_at, days_ago
                )

                try:
                    await repo.insert_session(doc)
                    count += 1
                except Exception as e:
                    logger.warning("写入 meter_id=%d 失败: %s", meter.id, e)

            # 更新 PG MeterSnapshot
            snap_result = await db.execute(
                select(MeterSnapshot).where(MeterSnapshot.meter_id == meter.id)
            )
            snap = snap_result.scalars().first()
            if snap:
                snap.online_status = True
                snap.last_comm_time = now
                snap.signal_strength = random.randint(70, 100)
                snap.eeprom_write_count = random.randint(500, 5000)
                snap.stack_usage = random.randint(20, 80)
            else:
                snap = MeterSnapshot(
                    meter_id=meter.id,
                    online_status=True,
                    last_comm_time=now,
                    signal_strength=random.randint(70, 100),
                    eeprom_write_count=random.randint(500, 5000),
                    stack_usage=random.randint(20, 80),
                    firmware_version=meter.firmware_version or "",
                    error_code="",
                )
                db.add(snap)

        await db.commit()

    logger.info("MongoDB seed 完成: 共写入 %d 个采集文档", count)


def _generate_variant(
    template: dict, meter: Meter, project_name: str, collected_at: datetime, days_ago: int
) -> dict:
    """基于模板生成变体文档。"""
    kvp = dict(template.get("key_value_pairs", {}))
    sheets = dict(template.get("sheets", {}))
    summary = dict(template.get("summary", {}))

    # 修改累计电能值（模拟每天增长）
    energy_key = "Energy.Cumulative A Positive.Value"
    if energy_key in kvp and isinstance(kvp[energy_key], (int, float)):
        kvp[energy_key] = int(kvp[energy_key]) + days_ago * random.randint(500, 2000)

    # 添加随机波动到瞬时量
    for key in list(kvp.keys()):
        if key.startswith("Instantaneous Data.") and isinstance(kvp[key], (int, float)):
            kvp[key] = kvp[key] + random.randint(-5, 5)

    # 统计
    total_read = summary.get("total_read", 796)
    total_failed = random.randint(0, 3)
    total_success = total_read - total_failed

    return {
        "session_id": 0,  # 无 PG session 关联（纯 Mongo seed）
        "meter_id": meter.id,
        "meter_serial": meter.serial_number,
        "project_id": meter.project_id,
        "project_name": project_name,
        "task_id": None,
        "collected_at": collected_at,
        "imported_at": datetime.now(timezone.utc),
        "source": "import",
        "source_file": "template_meter.json",
        "connection_type": "HDLC",
        "status": "success" if total_failed == 0 else "partial",
        "total_points": total_read,
        "success_points": total_success,
        "failed_points": total_failed,
        "sheets": sheets,
        "key_value_pairs": kvp,
        "summary": {
            "total_read": total_read,
            "total_success": total_success,
            "total_failed": total_failed,
            "sheet_count": summary.get("sheet_count", 24),
        },
        "schema_version": 1,
    }


async def main():
    try:
        await seed_mongo()
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
