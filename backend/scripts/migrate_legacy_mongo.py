#!/usr/bin/env python3
"""将旧拓扑（按项目分库 × 按电表分集合）迁移到新拓扑（单库单集合）。

旧拓扑（generate_testdata_mongo.py 产出的数据）：
  DB: Cusk-01_DCPP_DailyCheck / Andromeda-01_DailyCheck / ...
  Collection: KFM2025030100001（按电表序列号命名）
  每集合 1 个文档，无 meter_id/session_id/schema_version 等字段

新拓扑（设计文档定义）：
  DB: minihes
  Collection: meter_sessions
  每文档含完整元数据 + sheets + key_value_pairs + summary

用法：
    cd backend && uv run python scripts/migrate_legacy_mongo.py            # 正式迁移
    cd backend && uv run python scripts/migrate_legacy_mongo.py --dry-run  # 干跑（只统计）
"""

import argparse
import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MONGODB_URL = "mongodb://localhost:27017"
TARGET_DB = "minihes"
TARGET_COLLECTION = "meter_sessions"

# 旧数据库 → 项目信息映射
LEGACY_DB_MAP = {
    "Cusk-01_DCPP_DailyCheck": {"project_id": None, "project_name": "Cusk-01"},
    "Andromeda-01_DailyCheck": {"project_id": None, "project_name": "Andromeda-01"},
    "Draco-01_DCPP_DailyCheck": {"project_id": None, "project_name": "Draco-01"},
    "Puma-01_DCPP_DailyCheck": {"project_id": None, "project_name": "Puma-01"},
}


async def migrate(dry_run: bool = False) -> None:
    """执行迁移。"""
    client = AsyncIOMotorClient(MONGODB_URL)
    target = client[TARGET_DB][TARGET_COLLECTION]

    total_migrated = 0
    total_skipped = 0
    total_failed = 0

    for legacy_db_name, project_info in LEGACY_DB_MAP.items():
        db = client[legacy_db_name]
        try:
            collections = await db.list_collection_names()
        except Exception as e:
            logger.warning("无法访问旧库 %s: %s，跳过", legacy_db_name, e)
            continue

        if not collections:
            logger.info("旧库 %s 无集合，跳过", legacy_db_name)
            continue

        logger.info("处理旧库 %s: %d 个集合", legacy_db_name, len(collections))

        for coll_name in collections:
            meter_serial = coll_name

            async for doc in db[coll_name].find({}):
                old_id = doc.get("_id")

                # 幂等检查：如果目标已有同 _id 文档，跳过
                existing = await target.find_one({"_id": old_id})
                if existing:
                    total_skipped += 1
                    continue

                # 构建新格式文档
                summary = doc.get("summary", {})
                timestamp = doc.get("timestamp")

                new_doc = {
                    "_id": old_id,  # 保留原 _id
                    "session_id": None,
                    "meter_id": None,  # 需后续从 PG 回填
                    "meter_serial": meter_serial,
                    "project_id": project_info["project_id"],
                    "project_name": project_info["project_name"],
                    "task_id": None,
                    "collected_at": timestamp,
                    "imported_at": timestamp,
                    "source": "import",
                    "source_file": doc.get("source_file", ""),
                    "connection_type": "",
                    "status": "success" if summary.get("total_failed", 0) == 0 else "partial",
                    "total_points": summary.get("total_read", 0),
                    "success_points": summary.get("total_success", 0),
                    "failed_points": summary.get("total_failed", 0),
                    "sheets": doc.get("sheets", {}),
                    "key_value_pairs": doc.get("key_value_pairs", {}),
                    "summary": summary,
                    "schema_version": 1,
                    "_legacy_db": legacy_db_name,
                    "_legacy_collection": coll_name,
                }

                if not dry_run:
                    try:
                        await target.insert_one(new_doc)
                        total_migrated += 1
                    except Exception as e:
                        logger.error("写入失败 %s/%s: %s", legacy_db_name, coll_name, e)
                        total_failed += 1
                else:
                    total_migrated += 1

    logger.info(
        "迁移完成: %d 文档已迁移, %d 文档跳过, %d 失败 (dry_run=%s)",
        total_migrated,
        total_skipped,
        total_failed,
        dry_run,
    )
    client.close()


def main():
    parser = argparse.ArgumentParser(description="迁移旧 MongoDB 拓扑到新设计")
    parser.add_argument("--dry-run", action="store_true", help="干跑模式，不实际写入")
    args = parser.parse_args()

    asyncio.run(migrate(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
