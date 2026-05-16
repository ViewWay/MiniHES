from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.test import Defect


def _defect_to_dict(d: Defect) -> dict:
    """Convert a Defect ORM object to a plain dict for API responses."""
    return {
        "id": d.id,
        "test_id": d.test_id,
        "title": d.title,
        "description": d.description,
        "severity": d.severity,
        "status": d.status,
        "meter_id": d.meter_id,
        "detected_at": d.detected_at.strftime("%Y-%m-%d %H:%M:%S") if d.detected_at else None,
        "resolved_by": d.resolved_by,
        "resolved_at": d.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if d.resolved_at else None,
        "created_at": d.created_at.strftime("%Y-%m-%d %H:%M:%S") if d.created_at else None,
    }


async def list_defects(
    db: AsyncSession,
    *,
    test_id: int | None = None,
    severity: str | None = None,
    status: str | None = None,
) -> dict:
    """Return defects list with total count."""
    stmt = select(Defect)
    count_stmt = select(func.count()).select_from(Defect)

    if test_id is not None:
        stmt = stmt.where(Defect.test_id == test_id)
        count_stmt = count_stmt.where(Defect.test_id == test_id)
    if severity:
        stmt = stmt.where(Defect.severity == severity)
        count_stmt = count_stmt.where(Defect.severity == severity)
    if status:
        stmt = stmt.where(Defect.status == status)
        count_stmt = count_stmt.where(Defect.status == status)

    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(stmt.order_by(Defect.id.desc()))
    items = [_defect_to_dict(d) for d in result.scalars().all()]
    return {"items": items, "total": total}


async def create_defect(db: AsyncSession, test_id: int, data: dict) -> int:
    """Create a defect for a test. Returns the defect id."""
    data["test_id"] = test_id
    defect = Defect(**data)
    db.add(defect)
    await db.flush()
    return defect.id


async def update_defect(db: AsyncSession, defect_id: int, data: dict) -> dict:
    """Update a defect. Automatically sets resolved_at when status becomes 'resolved'."""
    defect = await db.get(Defect, defect_id)
    if not defect:
        raise BusinessException(code=404, message="缺陷记录不存在")

    new_status = data.get("status")
    if new_status == "resolved" and defect.status != "resolved":
        data["resolved_at"] = datetime.now(timezone.utc)

    for key, value in data.items():
        if hasattr(defect, key) and value is not None:
            setattr(defect, key, value)
    await db.flush()
    return _defect_to_dict(defect)
