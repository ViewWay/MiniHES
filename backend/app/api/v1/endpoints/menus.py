from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.services.menu_service import check_name_exists, check_path_exists, list_menus

router = APIRouter(prefix="/system/menu", tags=["menu"])


@router.get("/list")
async def list_menus_endpoint(db: DbSession = ..., _user: CurrentUser = ...):
    items = await list_menus(db)
    return success(items)


@router.get("/name-exists")
async def check_name_exists_endpoint(
    db: DbSession = ...,
    _user: CurrentUser = ...,
    name: str = Query(...),
    id: int | None = Query(default=None),
):
    exists = await check_name_exists(db, name, id)
    return success(exists)


@router.get("/path-exists")
async def check_path_exists_endpoint(
    db: DbSession = ...,
    _user: CurrentUser = ...,
    path: str = Query(...),
    id: int | None = Query(default=None),
):
    exists = await check_path_exists(db, path, id)
    return success(exists)
