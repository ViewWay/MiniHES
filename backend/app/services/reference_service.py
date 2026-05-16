from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.meter import MeterType, WireType
from app.models.meter_point import MeterPoint


def _meter_type_to_dict(t: MeterType) -> dict:
    return {"id": t.id, "name": t.name, "code": t.code, "description": t.description}


def _wire_type_to_dict(w: WireType) -> dict:
    return {"id": w.id, "name": w.name, "code": w.code, "description": w.description}


def _meter_point_to_dict(p: MeterPoint) -> dict:
    return {
        "id": p.id,
        "meter_id": p.meter_id,
        "obis_code": p.obis_code,
        "point_name": p.point_name,
        "point_type": p.point_type,
        "data_type": p.data_type,
        "unit": p.unit,
        "scaler": p.scaler,
        "is_collectible": p.is_collectible,
        "description": p.description,
    }


async def list_meter_types(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(MeterType).order_by(MeterType.id))
    return [_meter_type_to_dict(t) for t in result.scalars().all()]


async def list_wire_types(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(WireType).order_by(WireType.id))
    return [_wire_type_to_dict(w) for w in result.scalars().all()]


async def list_meter_points(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(MeterPoint).order_by(MeterPoint.id))
    return [_meter_point_to_dict(p) for p in result.scalars().all()]


async def create_meter_point(db: AsyncSession, data: dict) -> int:
    point = MeterPoint(
        meter_id=data.get("meter_id", 0),
        obis_code=data.get("obis_code", ""),
        point_name=data.get("point_name", ""),
        point_type=data.get("point_type", "register"),
        data_type=data.get("data_type", "numeric"),
        unit=data.get("unit", ""),
        description=data.get("description", ""),
    )
    db.add(point)
    await db.flush()
    return point.id


async def update_meter_point(db: AsyncSession, point_id: int, data: dict) -> None:
    point = await db.get(MeterPoint, point_id)
    if not point:
        raise BusinessException(code=404, message="采集点不存在")
    for key, value in data.items():
        if hasattr(point, key):
            setattr(point, key, value)


async def delete_meter_point(db: AsyncSession, point_id: int) -> None:
    point = await db.get(MeterPoint, point_id)
    if not point:
        raise BusinessException(code=404, message="采集点不存在")
    await db.delete(point)
