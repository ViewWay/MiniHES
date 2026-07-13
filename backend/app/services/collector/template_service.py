"""OBIS 模板服务 — 模板列表查询 + 详情查询。

对应 endpoints/collector.py 的模板管理接口。
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.obis_template import DataPointTemplate, ObisTemplate


async def list_templates(
    db: AsyncSession,
    *,
    device_type: str | None = None,
    task_category: str | None = None,
) -> list[dict]:
    """模板列表，含每模板的数据点数量。

    可选按 device_type / task_category 筛选。
    """
    stmt = select(ObisTemplate).order_by(ObisTemplate.device_type, ObisTemplate.id)
    if device_type:
        stmt = stmt.where(ObisTemplate.device_type == device_type)
    if task_category:
        stmt = stmt.where(ObisTemplate.task_category == task_category)

    result = await db.execute(stmt)
    templates = result.scalars().all()

    # 批量查询各模板的数据点数量
    count_stmt = select(DataPointTemplate.template_id, func.count(DataPointTemplate.id)).group_by(
        DataPointTemplate.template_id
    )
    count_result = await db.execute(count_stmt)
    count_map: dict[int, int] = dict(count_result.all())

    return [
        {
            "id": t.id,
            "name": t.name,
            "device_type": t.device_type,
            "task_category": t.task_category,
            "description": t.description,
            "is_system": t.is_system,
            "version": t.version,
            "item_count": count_map.get(t.id, 0),
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in templates
    ]


async def get_template_detail(db: AsyncSession, template_id: int) -> dict | None:
    """模板详情，含全部数据点明细（按 sort_order 排序）"""
    stmt = select(ObisTemplate).options(selectinload(ObisTemplate.items)).where(ObisTemplate.id == template_id)
    result = await db.execute(stmt)
    tpl = result.scalar_one_or_none()
    if tpl is None:
        return None

    items_sorted = sorted(tpl.items, key=lambda x: x.sort_order)

    return {
        "id": tpl.id,
        "name": tpl.name,
        "device_type": tpl.device_type,
        "task_category": tpl.task_category,
        "description": tpl.description,
        "is_system": tpl.is_system,
        "version": tpl.version,
        "created_at": tpl.created_at.isoformat() if tpl.created_at else None,
        "updated_at": tpl.updated_at.isoformat() if tpl.updated_at else None,
        "items": [
            {
                "id": item.id,
                "module": item.module,
                "point_name": item.point_name,
                "address": item.address,
                "data_type": item.data_type,
                "unit": item.unit,
                "scaler": item.scaler,
                "is_read": item.is_read,
                "sort_order": item.sort_order,
                "protocol_params": item.protocol_params,
                "remark": item.remark,
            }
            for item in items_sorted
        ],
    }
