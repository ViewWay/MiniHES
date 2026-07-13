"""基于真实 DCPP 数据生成历史趋势数据。

从 MongoDB 现有的 24 个真实 DCPP 文档出发，
为每台电表生成过去 90 天的每日采集文档（电能值按真实值合理递减回溯）。

用法：
    cd backend
    PYTHONPATH=. uv run python scripts/expand_history.py
"""

import asyncio
import copy
import logging
import random
import sys
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MONGO_URL = "mongodb://localhost:27017"
MONGO_DB = "minihes"
DAYS_TO_GENERATE = 90
random.seed(42)


async def expand_history():
    """为每台有真实 DCPP 数据的电表生成 90 天历史。"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[MONGO_DB]
    col = db["meter_sessions"]

    real_docs = await col.find({"total_points": {"$gte": 50}}).to_list(length=100)
    logger.info("找到 %d 个真实 DCPP 文档", len(real_docs))

    existing = await col.count_documents({})
    if existing > 200:
        logger.info("已有 %d 文档（>200），跳过生成", existing)
        client.close()
        return

    # 清空空壳文档
    deleted = await col.delete_many({"total_points": {"$lt": 50}})
    logger.info("清理 %d 个空壳文档", deleted.deleted_count)

    session_counter = -1000
    total_inserted = 0
    base_time = datetime(2025, 6, 1, 9, 0, 0, tzinfo=timezone.utc)

    for doc in real_docs:
        meter_id = doc.get("meter_id", 0)
        kvp = doc.get("key_value_pairs", {})
        energy_val = kvp.get("Active energy import.value") or kvp.get("Energy.Cumulative A Positive.Value") or 200000

        for day_offset in range(DAYS_TO_GENERATE, 0, -1):
            collected_at = base_time - timedelta(days=day_offset)
            daily_usage = random.uniform(5, 15)
            historical_energy = int(energy_val - daily_usage * day_offset)

            new_doc = copy.deepcopy(doc)
            new_doc.pop("_id", None)
            new_doc["session_id"] = session_counter
            session_counter -= 1
            new_doc["collected_at"] = collected_at
            new_doc["imported_at"] = datetime.now(timezone.utc)
            new_doc["source"] = "historical"

            new_kvp = new_doc.get("key_value_pairs", {})
            for key in ["Active energy import.value", "Energy.Cumulative A Positive.Value"]:
                if key in new_kvp:
                    new_kvp[key] = historical_energy

            for key in list(new_kvp.keys()):
                if "voltage" in key.lower() and isinstance(new_kvp[key], (int, float)):
                    new_kvp[key] = new_kvp[key] + random.randint(-3, 3)
                elif "current" in key.lower() and isinstance(new_kvp[key], (int, float)):
                    new_kvp[key] = max(0, new_kvp[key] + random.randint(-1, 1))

            new_doc["key_value_pairs"] = new_kvp
            await col.insert_one(new_doc)
            total_inserted += 1

        logger.info("  meter_id=%s: 生成 %d 天历史", meter_id, DAYS_TO_GENERATE)

    logger.info("完成: 共生成 %d 个历史文档", total_inserted)
    final_count = await col.count_documents({})
    logger.info("MongoDB 总文档数: %d", final_count)
    client.close()


if __name__ == "__main__":
    asyncio.run(expand_history())
    sys.exit(0)
