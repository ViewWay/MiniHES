from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.schemas.task import TaskCreate, TaskToggle, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
async def list_tasks(
    db: DbSession = ...,
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    task_type: str = Query(default=None),
    task_category: str = Query(default=None),
    status: str = Query(default=None),
    is_enabled: bool = Query(default=None),
):
    data = await task_service.list_tasks(
        db,
        page=page,
        page_size=page_size,
        task_type=task_type,
        is_enabled=is_enabled,
    )
    return success(data)


@router.post("")
async def create_task(body: TaskCreate, db: DbSession = ..., _user: CurrentUser = ...):
    data = await task_service.create_task(db, body.model_dump())
    return success(data)


@router.get("/{task_id}")
async def get_task(task_id: int, db: DbSession = ...):
    data = await task_service.get_task(db, task_id)
    return success(data)


@router.put("/{task_id}")
async def update_task(task_id: int, body: TaskUpdate, db: DbSession = ..., _user: CurrentUser = ...):
    data = await task_service.update_task(db, task_id, body.model_dump(exclude_unset=True))
    return success(data)


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: DbSession = ..., _user: CurrentUser = ...):
    await task_service.delete_task(db, task_id)
    return success({"success": True})


@router.post("/{task_id}/execute")
async def execute_task(task_id: int, db: DbSession = ..., body: dict = None):
    data = await task_service.execute_task(db, task_id)
    return success(data)


@router.get("/{task_id}/logs")
async def get_task_logs(task_id: int, db: DbSession = ...):
    data = await task_service.get_task_logs(db, task_id)
    return success(data)


@router.patch("/{task_id}/toggle")
async def toggle_task(task_id: int, body: TaskToggle, db: DbSession = ..., _user: CurrentUser = ...):
    is_enabled = await task_service.toggle_task(db, task_id, body.is_enabled)
    return success({"success": True, "is_enabled": is_enabled})
