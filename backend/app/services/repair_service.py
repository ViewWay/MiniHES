from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.meter import Meter, MeterRepair

VALID_REPAIR_STATUSES = {"in_progress", "completed", "cancelled"}


def _repair_to_dict(r: MeterRepair) -> dict:
    """Convert a MeterRepair ORM object to a plain dict."""
    return {
        "id": r.id,
        "meter_id": r.meter_id,
        "description": r.description,
        "cost": r.cost,
        "status": r.status,
        "repaired_by": r.repaired_by,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
        "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None,
    }


async def list_repairs(
    db: AsyncSession,
    *,
    meter_id: int | None = None,
    status: str | None = None,
) -> dict:
    """List repair records with optional filters."""
    stmt = select(MeterRepair).order_by(MeterRepair.id.desc())
    if meter_id:
        stmt = stmt.where(MeterRepair.meter_id == meter_id)
    if status:
        stmt = stmt.where(MeterRepair.status == status)

    result = await db.execute(stmt)
    items = [_repair_to_dict(r) for r in result.scalars().all()]
    return {"items": items, "total": len(items)}


async def create_repair(
    db: AsyncSession,
    *,
    meter_id: int,
    description: str,
    cost: int = 0,
    user_id: int | None = None,
) -> dict:
    """Create a new repair record."""
    meter = await db.get(Meter, meter_id)
    if not meter:
        raise BusinessException(code=404, message="样机不存在")

    repair = MeterRepair(
        meter_id=meter_id,
        description=description,
        cost=cost,
        status="in_progress",
        repaired_by=user_id,
    )
    db.add(repair)
    await db.flush()
    return {"id": repair.id, **_repair_to_dict(repair)}


async def update_repair(
    db: AsyncSession,
    repair_id: int,
    *,
    description: str | None = None,
    cost: int | None = None,
    status: str | None = None,
) -> dict:
    """Update a repair record."""
    result = await db.execute(select(MeterRepair).where(MeterRepair.id == repair_id))
    repair = result.scalar_one_or_none()
    if not repair:
        raise BusinessException(code=404, message="维修记录不存在")

    if status is not None:
        if status not in VALID_REPAIR_STATUSES:
            raise BusinessException(code=400, message=f"无效的维修状态: {status}")
        repair.status = status
    if description is not None:
        repair.description = description
    if cost is not None:
        repair.cost = cost

    await db.flush()
    await db.refresh(repair)
    return _repair_to_dict(repair)
