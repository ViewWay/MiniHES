from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.services import task_service

router = APIRouter(prefix="/task-logs", tags=["task-logs"])


@router.get("/{log_id}/devices")
async def get_task_device_log(
    log_id: int,
    db: DbSession = ...,
    _user: CurrentUser = ...,
    status: str = Query(default=None),
):
    data = await task_service.get_task_device_log(db, log_id, status=status)
    return success(data)
