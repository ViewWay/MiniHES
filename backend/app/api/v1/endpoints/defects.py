from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.models.test import Defect

router = APIRouter(prefix="/defects", tags=["defects"])


@router.get("")
async def list_defects(
    db: DbSession = ...,
    test_id: int = Query(default=None),
    severity: str = Query(default=None),
    status: str = Query(default=None),
):
    stmt = select(Defect).order_by(Defect.id)
    if test_id:
        stmt = stmt.where(Defect.test_id == test_id)
    if severity:
        stmt = stmt.where(Defect.severity == severity)
    if status:
        stmt = stmt.where(Defect.status == status)

    result = await db.execute(stmt)
    items = [
        {
            "id": d.id,
            "test_id": d.test_id,
            "title": d.title,
            "description": d.description,
            "severity": d.severity,
            "status": d.status,
            "meter_id": d.meter_id,
            "detected_at": d.detected_at.strftime("%Y-%m-%d %H:%M:%S") if d.detected_at else None,
            "resolved_at": d.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if d.resolved_at else None,
        }
        for d in result.scalars().all()
    ]
    return success({"items": items, "total": len(items)})


@router.put("/{defect_id}")
async def update_defect(defect_id: int, body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    d = result.scalar_one_or_none()
    if not d:
        return success(None)

    for key, value in body.items():
        if hasattr(d, key):
            setattr(d, key, value)

    if body.get("status") == "resolved":
        from datetime import datetime, timezone
        d.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    return success({"id": d.id})
