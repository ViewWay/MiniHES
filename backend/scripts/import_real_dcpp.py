"""导入真实 DCPP DailyCheck 数据到 MongoDB meter_sessions。

从 docs/testdata/ 下的 3 个真实电表巡检 JSON 文件（每个 8 台电表），
转换并写入 MongoDB meter_sessions 集合。

这些是真实电表硬件采集的数据，不是 mock。

用法：
    cd backend
    PYTHONPATH=. uv run python scripts/import_real_dcpp.py
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TESTDATA_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "testdata"

# 项目文件 → 项目信息映射
DCPP_FILES = [
    ("Cusk-01_DCPP_DailyCheck.json", "Cusk-01_DCPP_DailyCheck"),
    ("Andromeda-01_DailyCheck.json", "Andromeda-01_DailyCheck"),
    ("Draco-01_DCPP_DailyCheck.json", "Draco-01_DCPP_DailyCheck"),
]

MONGO_URL = "mongodb://localhost:27017"
MONGO_DB = "minihes"


def convert_dcpp_to_session(doc: dict, project_name: str, meter_index: int) -> dict:
    """将一条 DCPP 真实巡检记录转换为 meter_sessions 文档。

    DCPP 键名格式: "classId,obis,attrId#ControlName&attrName"
    需要解析为 key_value_pairs 和 sheets 结构。
    """
    kvp = {}
    sheets: dict[str, dict] = {}
    total_read = 0
    total_success = 0

    for key, value in doc.items():
        if key.startswith("_"):
            continue

        # 解析 DCPP 键名: "3,1.0.1.8.0.255,2#Active energy import&value"
        if "#" in key:
            obis_part, name_part = key.split("#", 1)
            parts = obis_part.split(",")
            class_id = int(parts[0]) if len(parts) >= 1 and parts[0].isdigit() else 0
            obis = parts[1] if len(parts) >= 2 else ""
            attr_id = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 2

            if "&" in name_part:
                control_name, attr_name = name_part.split("&", 1)
            else:
                control_name, attr_name = name_part, ""

            # 构建 key_value_pairs 键
            kvp_key = f"{control_name}.{attr_name}" if control_name else attr_name
            kvp[kvp_key] = _normalize_value(value)

            # 构建 sheets 结构
            sheet_name = _infer_sheet_name(control_name, class_id, obis)
            if sheet_name not in sheets:
                sheets[sheet_name] = {"sheet_name": sheet_name, "objects": []}
            sheets[sheet_name]["objects"].append(
                {
                    "key": kvp_key,
                    "classId": class_id,
                    "obis": obis,
                    "attributeId": attr_id,
                    "attributeName": attr_name,
                    "controlName": control_name,
                    "value": _normalize_value(value),
                    "status": "success",
                }
            )
            total_read += 1
            total_success += 1
        else:
            # 元数据字段（pos, ip, ping 等）
            kvp[key] = _normalize_value(value)

    # 提取真实 EEPROM/stack 数据
    eeprom_writes = doc.get("eeprom_write_times", [])
    stack_info = doc.get("stack_information", [])

    # 提取 Device ID 作为序列号
    device_id_key = "1,0.0.96.1.0.255,2#Device ID&value"
    device_id = str(doc.get(device_id_key, ""))

    # 真实采集时间
    timestamp_str = doc.get("reading_end_time") or doc.get("currently_time") or ""
    collected_at = _parse_dcpp_time(timestamp_str)

    return {
        "session_id": 0,
        "meter_id": 0,  # 后续回填
        "meter_serial": device_id,
        "project_id": 0,
        "project_name": project_name,
        "task_id": None,
        "collected_at": collected_at,
        "imported_at": datetime.now(timezone.utc),
        "source": "import",
        "source_file": f"{project_name}.json",
        "connection_type": "HDLC",
        "status": "success",
        "total_points": total_read,
        "success_points": total_success,
        "failed_points": 0,
        "sheets": sheets,
        "key_value_pairs": kvp,
        "summary": {
            "total_read": total_read,
            "total_success": total_success,
            "total_failed": 0,
            "sheet_count": len(sheets),
        },
        "eeprom_write_times": eeprom_writes,
        "stack_information": stack_info,
        "schema_version": 1,
    }


def _normalize_value(v):
    """规范化 Extended JSON 值。"""
    if isinstance(v, dict):
        if "$numberInt" in v:
            return int(v["$numberInt"])
        if "$numberLong" in v:
            return int(v["$numberLong"])
        if "$numberDouble" in v:
            return float(v["$numberDouble"])
        return {k: _normalize_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_normalize_value(item) for item in v]
    return v


def _infer_sheet_name(control_name: str, class_id: int, obis: str) -> str:
    """根据 control_name/class_id 推断所属 sheet。"""
    cn = control_name.lower()
    if "energy" in cn and "import" in cn:
        return "Energy"
    if "voltage" in cn or "current" in cn or "power" in cn or "frequency" in cn:
        return "Instantaneous Data"
    if "billing" in cn and "daily" in cn:
        return "Daily Billing"
    if "billing" in cn and "month" in cn:
        return "Month Billing"
    if "load profile" in cn:
        return "Load Profile"
    if "event" in cn:
        return "Event Record"
    if "clock" in cn:
        return "Clock"
    if "device id" in cn or "logical" in cn:
        return "Basic Information"
    if "tariff" in cn:
        return "Tariff"
    if "quality" in cn:
        return "Power Quality"
    if "m-bus" in cn:
        return "M-Bus"
    if "lte" in cn or "communication" in cn:
        return "LTE Communication Setup"
    return "Other"


def _parse_dcpp_time(ts: str) -> datetime:
    """解析 DCPP 时间字符串。"""
    if not ts:
        return datetime.now(timezone.utc)
    try:
        m = re.match(r"(\d{4}-\d{2}-\d{2})\s+\d+\s+(\d{2}:\d{2}:\d{2})", ts)
        if m:
            return datetime.fromisoformat(f"{m.group(1)}T{m.group(2)}")
    except (ValueError, TypeError):
        pass
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


async def import_all():
    """导入全部 3 个项目的 DCPP 数据。"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[MONGO_DB]
    col = db["meter_sessions"]

    existing = await col.count_documents({})
    if existing > 0:
        logger.info("MongoDB 已有 %d 文档，先清空旧数据...", existing)
        await col.delete_many({})

    # DCPP 数据无 PG session 关联，用负值 session_id 避免与 PG 冲突
    session_counter = -1

    total = 0
    for filename, project_name in DCPP_FILES:
        filepath = TESTDATA_DIR / filename
        if not filepath.exists():
            logger.warning("文件不存在: %s", filepath)
            continue

        with open(filepath, encoding="utf-8") as f:
            raw_docs = json.load(f)

        logger.info("导入 %s: %d 台电表", project_name, len(raw_docs))

        for idx, raw_doc in enumerate(raw_docs):
            session_doc = convert_dcpp_to_session(raw_doc, project_name, idx)
            session_doc["session_id"] = session_counter
            session_counter -= 1
            await col.insert_one(session_doc)
            total += 1

    logger.info("导入完成: 共 %d 个真实采集文档", total)

    # 验证
    sample = await col.find_one({})
    if sample:
        kvp = sample.get("key_value_pairs", {})
        energy_keys = [k for k in kvp if "energy" in k.lower() and "import" in k.lower()]
        logger.info("验证 - 采样文档:")
        logger.info("  meter_serial: %s", sample.get("meter_serial"))
        logger.info("  project: %s", sample.get("project_name"))
        logger.info("  total_points: %s", sample.get("total_points"))
        logger.info("  sheet_count: %s", sample.get("summary", {}).get("sheet_count"))
        logger.info("  energy value: %s", kvp.get(energy_keys[0]) if energy_keys else "NOT FOUND")
        logger.info("  eeprom_write_times: %s", sample.get("eeprom_write_times"))

    client.close()


if __name__ == "__main__":
    asyncio.run(import_all())
    sys.exit(0)
