"""MongoDB 集合 + validator + 索引初始化脚本。

用法：
    cd backend
    uv run python scripts/init_mongo.py

创建：
    - Database: minihes（或 MONGODB_DATABASE 配置值）
    - Collection: meter_sessions
    - Validator ($jsonSchema)
    - 4 个索引（idx_meter_time, idx_project_time, idx_session_id, idx_serial_time）
"""

import asyncio
import logging
import sys

from app.core.config import settings
from app.core.mongo import close_mongo, get_mongo_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

COLLECTION = "meter_sessions"

VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["meter_id", "collected_at", "sheets", "schema_version"],
        "properties": {
            "meter_id": {"bsonType": "int", "description": "PG dev_meter.id，必填"},
            "meter_serial": {"bsonType": "string"},
            "session_id": {"bsonType": "int", "description": "PG col_session.id"},
            "project_id": {"bsonType": "int"},
            "task_id": {"bsonType": ["int", "null"]},
            "collected_at": {"bsonType": "date", "description": "采集时刻，必填"},
            "imported_at": {"bsonType": "date"},
            "source": {"enum": ["auto", "manual", "import"]},
            "source_file": {"bsonType": "string"},
            "connection_type": {"enum": ["HDLC", "TCP", "WPDU", "FEP", ""]},
            "status": {"enum": ["success", "partial", "failed"]},
            "sheets": {"bsonType": "object", "description": "DLMS 24 sheets 完整文档，必填"},
            "key_value_pairs": {"bsonType": "object"},
            "summary": {"bsonType": "object"},
            "schema_version": {
                "bsonType": "int",
                "minimum": 1,
                "description": "文档 schema 版本，必填",
            },
        },
    }
}

INDEXES = [
    ([("meter_id", 1), ("collected_at", -1)], {"name": "idx_meter_time"}),
    ([("project_id", 1), ("collected_at", -1)], {"name": "idx_project_time"}),
    ([("session_id", 1)], {"name": "idx_session_id", "unique": True}),
    ([("meter_serial", 1), ("collected_at", -1)], {"name": "idx_serial_time"}),
]


async def init_mongo():
    """创建集合 + validator + 索引。"""
    client = get_mongo_client()
    db = client[settings.MONGODB_DATABASE]

    # 列出已有集合
    existing_cols = await db.list_collection_names()
    if COLLECTION in existing_cols:
        logger.info("集合 %s.%s 已存在，更新 validator...", settings.MONGODB_DATABASE, COLLECTION)
        await db.command(
            "collMod",
            COLLECTION,
            validator=VALIDATOR,
            validationLevel="moderate",
            validationAction="warn",
        )
    else:
        logger.info("创建集合 %s.%s with validator...", settings.MONGODB_DATABASE, COLLECTION)
        await db.create_collection(COLLECTION, validator=VALIDATOR, validationAction="warn")

    col = db[COLLECTION]

    # 创建索引
    existing_indexes = await col.index_information()
    for keys, options in INDEXES:
        idx_name = options["name"]
        if idx_name in existing_indexes:
            logger.info("  索引 %s 已存在，跳过", idx_name)
        else:
            await col.create_index(keys, **options)
            logger.info("  索引 %s 已创建", idx_name)

    # 验证
    count = await col.count_documents({})
    logger.info(
        "初始化完成: %s.%s, 当前文档数: %d", settings.MONGODB_DATABASE, COLLECTION, count
    )


async def main():
    try:
        await init_mongo()
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
