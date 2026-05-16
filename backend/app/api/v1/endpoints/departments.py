from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.schemas.system import DeptCreate, DeptUpdate
from app.services.dept_service import (
    list_departments, create_department, update_department, delete_department,
)

router = APIRouter(prefix="/system/dept", tags=["department"])


@router.get("/list")
async def api_list_departments(_user: CurrentUser = None, db: DbSession = ...):
    tree = await list_departments(db)
    return success(tree)


@router.post("")
async def api_create_department(body: DeptCreate, _user: CurrentUser = None, db: DbSession = ...):
    result = await create_department(db, body.model_dump())
    return success(result)


@router.put("/{dept_id}")
async def api_update_department(dept_id: int, body: DeptUpdate, _user: CurrentUser = None, db: DbSession = ...):
    await update_department(db, dept_id, body.model_dump(exclude_unset=True))
    return success(None)


@router.delete("/{dept_id}")
async def api_delete_department(dept_id: int, _user: CurrentUser = None, db: DbSession = ...):
    await delete_department(db, dept_id)
    return success(None)
