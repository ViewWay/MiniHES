from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.models.user import Permission

router = APIRouter(prefix="/system/menu", tags=["menu"])


@router.get("/list")
async def list_menus(db: DbSession = ..., _user: CurrentUser = ...):
    result = await db.execute(
        select(Permission).order_by(Permission.sort_order)
    )
    perms = result.scalars().all()
    items = [_perm_to_menu(p) for p in perms]
    return success(items)


@router.get("/name-exists")
async def check_name_exists(
    db: DbSession = ...,
    _user: CurrentUser = ...,
    name: str = Query(...),
    id: int | None = Query(default=None),
):
    stmt = select(Permission).where(Permission.name == name)
    if id:
        stmt = stmt.where(Permission.id != id)
    result = await db.execute(stmt)
    exists = result.scalar_one_or_none() is not None
    return success(exists)


@router.get("/path-exists")
async def check_path_exists(
    db: DbSession = ...,
    _user: CurrentUser = ...,
    path: str = Query(...),
    id: int | None = Query(default=None),
):
    stmt = select(Permission).where(Permission.path == path)
    if id:
        stmt = stmt.where(Permission.id != id)
    result = await db.execute(stmt)
    exists = result.scalar_one_or_none() is not None
    return success(exists)


def _perm_to_menu(p: Permission) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "type": p.type,
        "parent_id": p.parent_id,
        "path": p.path,
        "icon": p.icon,
        "sortOrder": p.sort_order,
        "status": 1 if p.status == "active" else 0,
        "createTime": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "",
    }
