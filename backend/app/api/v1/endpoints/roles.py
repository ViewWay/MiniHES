from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.schemas.system import RoleCreate, RoleUpdate
from app.services.role_service import list_roles as svc_list_roles, create_role, update_role, delete_role, get_permission_tree

router = APIRouter(prefix="/system/role", tags=["role"])


@router.get("/list")
async def list_roles_endpoint(
    db: DbSession = ...,
    _user: CurrentUser = ...,
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    name: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    data = await svc_list_roles(db)
    items = data.get("items", [])
    if name:
        items = [i for i in items if name.lower() in i.get("name", "").lower()]
    if status:
        items = [i for i in items if i.get("status") == status]
    total = len(items)
    items = items[(page - 1) * page_size : page * page_size]
    return success({"items": items, "total": total})


@router.post("")
async def create_role_endpoint(body: RoleCreate, db: DbSession = ..., _user: CurrentUser = ...):
    rid = await create_role(db, body.model_dump())
    return success({"id": rid})


@router.put("/{role_id}")
async def update_role_endpoint(role_id: int, body: RoleUpdate, db: DbSession = ..., _user: CurrentUser = ...):
    await update_role(db, role_id, body.model_dump(exclude_unset=True))
    return success(None)


@router.delete("/{role_id}")
async def delete_role_endpoint(role_id: int, db: DbSession = ..., _user: CurrentUser = ...):
    await delete_role(db, role_id)
    return success(None)
