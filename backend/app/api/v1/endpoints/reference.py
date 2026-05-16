from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.services.reference_service import (
    list_meter_types, list_wire_types, list_meter_points,
    create_meter_point, update_meter_point, delete_meter_point,
)

router = APIRouter()


@router.get("/meter-types")
async def api_list_meter_types(db: DbSession = ...):
    items = await list_meter_types(db)
    return success(items)


@router.get("/wire-types")
async def api_list_wire_types(db: DbSession = ...):
    items = await list_wire_types(db)
    return success(items)


@router.get("/meter-points")
async def api_list_meter_points(db: DbSession = ...):
    items = await list_meter_points(db)
    return success(items)


@router.post("/meter-points")
async def api_create_meter_point(body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    point_id = await create_meter_point(db, body)
    return success({"id": point_id})


@router.put("/meter-points/{point_id}")
async def api_update_meter_point(point_id: int, body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    await update_meter_point(db, point_id, body)
    return success(None)


@router.delete("/meter-points/{point_id}")
async def api_delete_meter_point(point_id: int, db: DbSession = ..., _user: CurrentUser = ...):
    await delete_meter_point(db, point_id)
    return success(None)
