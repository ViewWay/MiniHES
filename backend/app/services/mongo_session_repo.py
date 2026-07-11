"""MongoDB 采集会话数据访问层。

所有对 meter_sessions 集合的读写都通过此类，
保证投影策略、错误处理、日志记录的一致性。
"""

import logging
from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class MongoSessionRepo:
    """采集会话 MongoDB 数据访问对象。"""

    COLLECTION = "meter_sessions"

    # 常用投影：分析 API 只需元数据 + 特定 sheet，避免加载完整 1.2MB
    PROJ_META = {
        "meter_id": 1,
        "meter_serial": 1,
        "project_id": 1,
        "project_name": 1,
        "collected_at": 1,
        "status": 1,
        "total_points": 1,
        "success_points": 1,
        "failed_points": 1,
        "summary": 1,
        "source": 1,
        "source_file": 1,
        "_id": 0,
    }
    PROJ_DAILY = {
        "key_value_pairs": 1,
        "collected_at": 1,
        "_id": 0,
    }
    PROJ_LOAD_PROFILE = {
        "key_value_pairs": 1,
        "collected_at": 1,
        "_id": 0,
    }
    PROJ_INSTANTANEOUS = {
        "key_value_pairs": 1,
        "_id": 0,
    }

    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db[self.COLLECTION]

    # ─── 写入 ───

    async def insert_session(self, doc: dict) -> str:
        """写入完整采集文档，返回 _id（hex 字符串）。"""
        result = await self.col.insert_one(doc)
        return str(result.inserted_id)

    # ─── 单文档查询 ───

    async def get_by_doc_id(self, mongo_doc_id: str) -> dict | None:
        """按 col_session.mongo_doc_id 查原始文档。"""
        from bson import ObjectId

        try:
            return await self.col.find_one({"_id": ObjectId(mongo_doc_id)})
        except Exception:
            # mongo_doc_id 可能是非 ObjectId 格式（旧 seed 数据）
            return await self.col.find_one({"_id": mongo_doc_id})

    async def get_latest_by_meter(self, meter_id: int, projection: dict | None = None) -> dict | None:
        """查某电表最新一次采集文档（分析 API 最常用）。

        优先返回有完整 DLMS 数据的文档（total_points >= 50，即真实 DCPP 巡检），
        避免被 execute_task 写入的空壳文档（4 个点）覆盖。
        """
        # 先查有完整数据的最新文档
        doc = await self.col.find_one(
            {"meter_id": meter_id, "total_points": {"$gte": 50}},
            sort=[("collected_at", -1)],
            projection=projection or self.PROJ_META,
        )
        if doc:
            return doc
        # 退化：返回任意最新文档
        return await self.col.find_one(
            {"meter_id": meter_id},
            sort=[("collected_at", -1)],
            projection=projection or self.PROJ_META,
        )

    async def get_sessions_by_date_range(
        self,
        meter_id: int,
        start: datetime,
        end: datetime,
        limit: int = 200,
        projection: dict | None = None,
    ) -> list[dict]:
        """按时间范围查历史采集文档列表。"""
        proj = projection or {
            **self.PROJ_META,
            "key_value_pairs": 1,
        }
        cursor = self.col.find(
            {"meter_id": meter_id, "collected_at": {"$gte": start, "$lte": end}},
            projection=proj,
        ).sort("collected_at", -1)
        return await cursor.to_list(length=limit)

    async def get_all_latest(self, project_id: int | None = None, limit: int = 500) -> list[dict]:
        """获取所有电表的最新采集文档元数据（设备健康、一致性检查用）。"""
        match: dict = {}
        if project_id is not None:
            match["project_id"] = project_id

        pipeline = [
            {"$match": match} if match else {"$match": {}},
            {"$sort": {"collected_at": -1}},
            {
                "$group": {
                    "_id": "$meter_id",
                    "doc": {"$first": "$$ROOT"},
                }
            },
            {"$replaceRoot": {"newRoot": "$doc"}},
            {"$limit": limit},
        ]
        cursor = self.col.aggregate(pipeline)
        return await cursor.to_list(length=limit)

    async def count_sessions(
        self,
        meter_id: int | None = None,
        project_id: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> int:
        """统计采集会话数（一致性检查用）。"""
        query: dict = {}
        if meter_id is not None:
            query["meter_id"] = meter_id
        if project_id is not None:
            query["project_id"] = project_id
        if start or end:
            query["collected_at"] = {}
            if start:
                query["collected_at"]["$gte"] = start
            if end:
                query["collected_at"]["$lte"] = end
        return await self.col.count_documents(query)

    # ─── 分析 API 专用查询（带投影优化） ───

    async def get_daily_billing(self, meter_id: int, days: int = 30) -> list[dict]:
        """从最新采集文档的 Daily Billing buffer 提取日用电曲线。"""
        doc = await self.get_latest_by_meter(meter_id, projection=self.PROJ_DAILY)
        if not doc:
            return []
        return self._parse_daily_billing_buffer(doc, days)

    async def get_load_profile(self, meter_id: int) -> list[dict]:
        """从最新采集文档的 Load Profile buffer 提取 96 点负荷曲线。"""
        doc = await self.get_latest_by_meter(meter_id, projection=self.PROJ_LOAD_PROFILE)
        if not doc:
            return []
        return self._parse_load_profile_buffer(doc)

    async def get_instantaneous(self, meter_id: int) -> dict:
        """从最新采集文档的 Instantaneous Data sheet 提取瞬时量。"""
        doc = await self.get_latest_by_meter(meter_id, projection=self.PROJ_INSTANTANEOUS)
        if not doc:
            return {}
        return self._parse_instantaneous(doc)

    async def get_energy(self, meter_id: int) -> dict:
        """从 key_value_pairs 提取累计电能。"""
        doc = await self.get_latest_by_meter(meter_id, projection={"key_value_pairs": 1, "_id": 0})
        if not doc:
            return {}
        kvp = doc.get("key_value_pairs", {})
        # 兼容两种键名：template（Energy.Cumulative...）和 DCPP（Active energy import...）
        return {
            "cumulative_positive": (
                kvp.get("Energy.Cumulative A Positive.Value")
                if kvp.get("Energy.Cumulative A Positive.Value") is not None
                else kvp.get("Active energy import.value")
            ),
            "cumulative_positive_r1": (
                kvp.get("Energy.Cumulative A Positive rate1.Value")
                if kvp.get("Energy.Cumulative A Positive rate1.Value") is not None
                else kvp.get("Active energy import rate 1.value")
            ),
            "cumulative_positive_r2": (
                kvp.get("Energy.Cumulative A Positive rate2.Value")
                if kvp.get("Energy.Cumulative A Positive rate2.Value") is not None
                else kvp.get("Active energy import rate 2.value")
            ),
            "cumulative_negative": (
                kvp.get("Energy.Cumulative A Negative.Value")
                if kvp.get("Energy.Cumulative A Negative.Value") is not None
                else kvp.get("Active energy export.value")
            ),
        }

    async def get_events(self, meter_id: int) -> list[dict]:
        """从最新采集文档的 Event Record sheet 提取事件列表。"""
        doc = await self.get_latest_by_meter(meter_id, projection={"key_value_pairs": 1, "_id": 0})
        if not doc:
            return []
        return self._parse_events(doc)

    async def get_clock_status(self, meter_id: int) -> dict:
        """从 key_value_pairs 提取时钟状态。"""
        doc = await self.get_latest_by_meter(meter_id, projection={"key_value_pairs": 1, "_id": 0})
        if not doc:
            return {}
        kvp = doc.get("key_value_pairs", {})
        time_str = kvp.get("Clock.Clock.Time", "")
        deviation = kvp.get("Clock.Clock.Deviation", 0)
        return {
            "raw_time": time_str,
            "deviation": deviation,
            "is_accurate": abs(deviation) < 60 if isinstance(deviation, (int, float)) else True,
        }

    async def get_kv_value(self, meter_id: int, key: str) -> Any:
        """查 key_value_pairs 中某个 key 的值。

        注意：key 含点号（如 'Clock.Clock.Time'），不能用于 Mongo projection
        的点路径语法（会被解释为嵌套路径）。必须取整个 key_value_pairs 再 Python 层取值。
        """
        doc = await self.get_latest_by_meter(meter_id, projection={"key_value_pairs": 1, "_id": 0})
        if not doc:
            return None
        return doc.get("key_value_pairs", {}).get(key)

    async def get_profile_completeness(self, meter_id: int) -> list[dict]:
        """获取各 profile buffer 的完整性。"""
        doc = await self.get_latest_by_meter(meter_id, projection={"key_value_pairs": 1, "_id": 0})
        if not doc:
            return []
        kvp = doc.get("key_value_pairs", {})
        profiles = [
            ("Daily Billing", "Daily Billing.E-meter Daily Billing.Buffer", 365),
            ("Month Billing", "Month Billing.E-meter Month Billing.Buffer", 12),
            ("Load Profile", "Load Profile.Energy Profile.Buffer", 96),
        ]
        result = []
        for name, key, expected in profiles:
            buffer = kvp.get(key, {})
            actual = len(buffer) if isinstance(buffer, dict) else 0
            completeness = round(actual / expected * 100, 1) if expected > 0 else 0
            result.append({"name": name, "completeness": completeness, "expected": expected, "actual": actual})
        return result

    # ─── Buffer 解析（私有方法，统一从 key_value_pairs 读取） ───

    @staticmethod
    def _parse_daily_billing_buffer(doc: dict, days: int) -> list[dict]:
        """解析 Daily Billing buffer 为结构化日用电列表。

        buffer 格式: {"0": [timestamp, interval, energy, r1, r2, r3], ...}
        """
        kvp = doc.get("key_value_pairs", {})
        buffer_key = "Daily Billing.E-meter Daily Billing.Buffer"
        buffer = kvp.get(buffer_key, {})
        if not isinstance(buffer, dict):
            return []

        result = []
        for idx, entry in buffer.items():
            if not isinstance(entry, list) or len(entry) < 3:
                continue
            result.append(
                {
                    "index": int(idx),
                    "raw_timestamp": entry[0],
                    "interval_minutes": entry[1],
                    "cumulative_energy": entry[2],
                    "rate1": entry[3] if len(entry) > 3 else 0,
                    "rate2": entry[4] if len(entry) > 4 else 0,
                    "rate3": entry[5] if len(entry) > 5 else 0,
                }
            )

        result.sort(key=lambda x: x["index"], reverse=True)
        return result[:days]

    @staticmethod
    def _parse_load_profile_buffer(doc: dict) -> list[dict]:
        """解析 Load Profile buffer 为 96 点负荷曲线。

        buffer 格式: {"0": [timestamp, status, energy, rate1], ...}
        """
        kvp = doc.get("key_value_pairs", {})
        buffer_key = "Load Profile.Energy Profile.Buffer"
        buffer = kvp.get(buffer_key, {})
        if not isinstance(buffer, dict):
            return []

        result = []
        prev_energy = None
        for idx in sorted(buffer.keys(), key=lambda x: int(x)):
            entry = buffer[idx]
            if not isinstance(entry, list) or len(entry) < 3:
                continue
            energy = entry[2]
            delta = energy - prev_energy if prev_energy is not None else 0
            i = int(idx)
            result.append(
                {
                    "index": i,
                    "time_slot": f"{i * 15 // 60:02d}:{i * 15 % 60:02d}",
                    "raw_timestamp": entry[0],
                    "status": entry[1],
                    "cumulative_energy": energy,
                    "interval_delta": delta,
                }
            )
            prev_energy = energy
        return result

    @staticmethod
    def _parse_instantaneous(doc: dict) -> dict:
        """解析 Instantaneous Data sheet 为瞬时量字典。"""
        kvp = doc.get("key_value_pairs", {})
        prefix = "Instantaneous Data."
        result = {}
        for key, value in kvp.items():
            if key.startswith(prefix) and key.endswith(".Value"):
                short_name = key[len(prefix) : -len(".Value")]
                result[short_name] = value
        return result

    @staticmethod
    def _parse_events(doc: dict) -> list[dict]:
        """从 key_value_pairs 提取 Event Record 事件。

        事件存储在 sheets["Event Record"].objects 中，
        但 key_value_pairs 中也有 Event Record 相关的键。
        """
        kvp = doc.get("key_value_pairs", {})
        events: list[dict] = []
        for key, value in kvp.items():
            if key.startswith("Event Record.") and isinstance(value, dict):
                events.append(
                    {
                        "code": value.get("value", ""),
                        "timestamp": value.get("timestamp", ""),
                        "name": value.get("controlName", key.split(".")[-1]),
                    }
                )
            elif key.startswith("Event Record.") and isinstance(value, (str, int)):
                events.append(
                    {
                        "code": str(value),
                        "timestamp": "",
                        "name": key.split(".")[-1],
                    }
                )
        return events
