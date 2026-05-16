from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.models.task import TaskDevice

router = APIRouter(prefix="/task-logs", tags=["task-logs"])


@router.get("/{log_id}/devices")
async def get_task_device_log(
    log_id: int,
    db: DbSession = ...,
    _user: CurrentUser = ...,
    status: str = Query(default=None),
):
    stmt = select(TaskDevice).where(TaskDevice.log_id == log_id)
    if status:
        stmt = stmt.where(TaskDevice.status == status)

    result = await db.execute(stmt.order_by(TaskDevice.id))
    items = [
        {
            "id": d.id,
            "log_id": d.log_id,
            "task_id": d.task_id,
            "meter_id": d.meter_id,
            "status": d.status,
            "retry_count": d.retry_count,
            "error_code": d.error_code,
            "error_message": d.error_message,
            "start_time": d.start_time.strftime("%Y-%m-%d %H:%M:%S") if d.start_time else "",
            "end_time": d.end_time.strftime("%Y-%m-%d %H:%M:%S") if d.end_time else "",
            "duration_ms": d.duration_ms,
            "data_count": d.data_count,
        }
        for d in result.scalars().all()
    ]
    return success({"items": items, "total": len(items)})
