from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.models.meter import MeterType, WireType
from app.models.meter_point import MeterPoint

router = APIRouter()


@router.get("/meter-types")
async def list_meter_types(db: DbSession = ...):
    result = await db.execute(select(MeterType).order_by(MeterType.id))
    items = [
        {"id": t.id, "name": t.name, "code": t.code, "description": t.description}
        for t in result.scalars().all()
    ]
    return success(items)


@router.get("/wire-types")
async def list_wire_types(db: DbSession = ...):
    result = await db.execute(select(WireType).order_by(WireType.id))
    items = [
        {"id": w.id, "name": w.name, "code": w.code, "description": w.description}
        for w in result.scalars().all()
    ]
    return success(items)


@router.get("/meter-points")
async def list_meter_points(db: DbSession = ..., protocol: str = Query(default=None)):
    stmt = select(MeterPoint).order_by(MeterPoint.id)
    if protocol:
        stmt = stmt.where(MeterPoint.protocol == protocol)
    result = await db.execute(stmt)
    items = [
        {
            "id": p.id,
            "name": p.point_name,
            "code": p.point_code,
            "type": p.point_type,
            "data_type": p.data_type,
            "unit": p.unit,
            "protocol": p.protocol,
            "description": p.description,
            "storage_target": p.storage_target,
            "retention_days": p.retention_days,
        }
        for p in result.scalars().all()
    ]
    return success(items)


@router.post("/meter-points")
async def create_meter_point(body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    point = MeterPoint(
        point_code=body.get("code", ""),
        point_name=body.get("name", ""),
        point_type=body.get("type", "register"),
        data_type=body.get("data_type", "numeric"),
        unit=body.get("unit", ""),
        protocol=body.get("protocol", "DLMS"),
        description=body.get("description", ""),
        storage_target=body.get("storage_target", "influxdb"),
        retention_days=body.get("retention_days", 365),
    )
    db.add(point)
    await db.flush()
    return success({"id": point.id})


@router.put("/meter-points/{point_id}")
async def update_meter_point(point_id: int, body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    result = await db.execute(select(MeterPoint).where(MeterPoint.id == point_id))
    point = result.scalar_one_or_none()
    if not point:
        return success(None)

    field_map = {"name": "point_name", "code": "point_code", "type": "point_type"}
    for key, value in body.items():
        attr = field_map.get(key, key)
        if hasattr(point, attr):
            setattr(point, attr, value)

    return success(None)


@router.delete("/meter-points/{point_id}")
async def delete_meter_point(point_id: int, db: DbSession = ..., _user: CurrentUser = ...):
    result = await db.execute(select(MeterPoint).where(MeterPoint.id == point_id))
    point = result.scalar_one_or_none()
    if not point:
        return success(None)
    await db.delete(point)
    return success(None)
