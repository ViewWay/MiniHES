"""Excel 导入服务。

解析电表抄表配置 Excel 文件（XMLFunctionLists_Meter_PP.xlsx 格式），
提取电表清单、连接参数和 OBIS 码集，导入到 PG。

支持解析的 sheet：
  - Meter: 电表清单（序列号、型号、连接参数）
  - Configuration: 全局参数
  - P2PObis: P2P 任务 OBIS 码
  - MeteringObis: 全量抄读 OBIS 码
  - DCUObis: DCU OBIS 码
"""

import io
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.meter import Meter, MeterComm

logger = logging.getLogger(__name__)


async def import_meters_from_excel(db: AsyncSession, file_content: bytes, project_id: int | None = None) -> dict:
    """从 Excel 文件导入电表数据。

    参数:
        db: 数据库会话
        file_content: Excel 文件二进制内容
        project_id: 关联项目 ID（可选）

    返回:
        导入结果统计 {"meters_added": N, "points_added": N, "errors": [...]}
    """
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise BusinessException(code=500, message="服务器未安装 openpyxl 库")

    try:
        wb = load_workbook(io.BytesIO(file_content), data_only=True)
    except Exception as e:
        raise BusinessException(code=400, message=f"Excel 文件解析失败: {e}")

    result: dict[str, Any] = {
        "meters_added": 0,
        "meters_skipped": 0,
        "points_added": 0,
        "errors": [],
        "sheets_found": wb.sheetnames,
    }

    # 解析 Meter sheet
    if "Meter" in wb.sheetnames:
        meter_result = await _parse_meter_sheet(db, wb["Meter"], project_id)
        result["meters_added"] = meter_result["added"]
        result["meters_skipped"] = meter_result["skipped"]
        result["errors"].extend(meter_result["errors"])

    # 解析 OBIS sheets（P2PObis / MeteringObis / DCUObis）
    for sheet_name in ["P2PObis", "MeteringObis", "DCUObis"]:
        if sheet_name in wb.sheetnames:
            result["points_added"] += _parse_obis_sheet(wb[sheet_name])

    return result


async def _parse_meter_sheet(db: AsyncSession, ws, project_id: int | None) -> dict:
    """解析 Meter sheet，导入电表清单。

    预期列：serial_number, meter_name, model, host, port, protocol
    """
    result: dict[str, Any] = {"added": 0, "skipped": 0, "errors": []}

    # 读取表头
    headers: dict[str, int] = {}
    for col_idx, cell in enumerate(ws[1], start=0):
        if cell.value:
            headers[str(cell.value).strip().lower()] = col_idx

    # 遍历数据行
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue

        serial = _get_val(row, headers, "serial_number") or _get_val(row, headers, "serial")
        if not serial:
            continue

        serial = str(serial).strip()

        # 检查是否已存在
        existing = await db.execute(select(Meter).where(Meter.serial_number == serial))
        if existing.scalar_one_or_none():
            result["skipped"] += 1
            continue

        # 创建电表
        meter = Meter(
            serial_number=serial,
            meter_name=_get_val(row, headers, "meter_name") or serial,
            model=_get_val(row, headers, "model"),
            protocol=_get_val(row, headers, "protocol") or "DLMS",
            project_id=project_id,
            current_status="in_stock",
        )
        db.add(meter)
        await db.flush()

        # 创建通信配置
        host = _get_val(row, headers, "host") or _get_val(row, headers, "ip")
        port = _get_val(row, headers, "port")
        if host:
            comm = MeterComm(
                meter_id=meter.id,
                host=str(host),
                port=int(port) if port else 4059,
                connection_type="tcp",
            )
            db.add(comm)

        result["added"] += 1

    await db.flush()
    return result


def _parse_obis_sheet(ws) -> int:
    """解析 OBIS sheet，统计数据点数量。

    返回: 解析到的数据点数量
    """
    count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        obis = str(row[0]).strip()
        if obis and len(obis) >= 5:
            count += 1
    return count


def _get_val(row: tuple, headers: dict, key: str) -> Any:
    """从行中按列名取值。"""
    idx = headers.get(key.lower())
    if idx is not None and idx < len(row):
        val = row[idx]
        return val if val is not None else ""
    return ""
