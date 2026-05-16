from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.task import Task, TaskDevice, TaskLog


def _task_to_dict(t: Task) -> dict:
    """Convert a Task ORM object to a plain dict for API responses."""
    return {
        "id": t.id,
        "task_name": t.task_name,
        "task_type": t.task_type,
        "schedule_config": t.schedule_config,
        "execution_content": t.execution_content,
        "filter_config": t.filter_config,
        "priority": t.priority,
        "retry_times": t.retry_times,
        "timeout": t.timeout,
        "is_enabled": t.is_enabled,
        "last_execute_time": t.last_execute_time.strftime("%Y-%m-%d %H:%M:%S") if t.last_execute_time else None,
        "next_execute_time": t.next_execute_time.strftime("%Y-%m-%d %H:%M:%S") if t.next_execute_time else None,
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
        "updated_at": t.updated_at.strftime("%Y-%m-%d %H:%M:%S") if t.updated_at else "",
    }


def _task_log_to_dict(log: TaskLog) -> dict:
    """Convert a TaskLog ORM object to a plain dict for API responses."""
    return {
        "id": log.id,
        "task_id": log.task_id,
        "start_time": log.start_time.strftime("%Y-%m-%d %H:%M:%S") if log.start_time else None,
        "end_time": log.end_time.strftime("%Y-%m-%d %H:%M:%S") if log.end_time else None,
        "duration_ms": log.duration_ms,
        "status": log.status,
        "total_devices": log.total_devices,
        "success_devices": log.success_devices,
        "failed_devices": log.failed_devices,
        "error_message": log.error_message or "",
    }


def _task_device_to_dict(d: TaskDevice) -> dict:
    """Convert a TaskDevice ORM object to a plain dict for API responses."""
    return {
        "id": d.id,
        "log_id": d.log_id,
        "task_id": d.task_id,
        "meter_id": d.meter_id,
        "status": d.status,
        "retry_count": d.retry_count,
        "error_code": d.error_code or "",
        "error_message": d.error_message or "",
        "start_time": d.start_time.strftime("%Y-%m-%d %H:%M:%S") if d.start_time else None,
        "end_time": d.end_time.strftime("%Y-%m-%d %H:%M:%S") if d.end_time else None,
        "duration_ms": d.duration_ms,
        "data_count": d.data_count,
    }


async def list_tasks(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    task_type: str | None = None,
    is_enabled: bool | None = None,
) -> dict:
    """Return paginated task list with total and running_count."""
    stmt = select(Task)
    count_stmt = select(func.count()).select_from(Task)

    if task_type:
        stmt = stmt.where(Task.task_type == task_type)
        count_stmt = count_stmt.where(Task.task_type == task_type)
    if is_enabled is not None:
        stmt = stmt.where(Task.is_enabled == is_enabled)
        count_stmt = count_stmt.where(Task.is_enabled == is_enabled)

    total = (await db.execute(count_stmt)).scalar() or 0

    running_count_result = await db.execute(
        select(func.count()).select_from(Task).where(Task.is_enabled == True)  # noqa: E712
    )
    running_count = running_count_result.scalar() or 0

    result = await db.execute(
        stmt.order_by(Task.id).offset((page - 1) * page_size).limit(page_size)
    )
    items = [_task_to_dict(t) for t in result.scalars().all()]
    return {"items": items, "total": total, "running_count": running_count}


async def get_task(db: AsyncSession, task_id: int) -> dict | None:
    """Return a single task by id, or None if not found."""
    t = await db.get(Task, task_id)
    if not t:
        return None
    return _task_to_dict(t)


async def create_task(db: AsyncSession, data: dict) -> dict:
    """Create a task and return its data dict."""
    task = Task(**data)
    db.add(task)
    await db.flush()
    return {"id": task.id, **_task_to_dict(task)}


async def update_task(db: AsyncSession, task_id: int, data: dict) -> dict | None:
    """Update a task. Returns None if task not found."""
    t = await db.get(Task, task_id)
    if not t:
        return None
    for key, value in data.items():
        if hasattr(t, key):
            setattr(t, key, value)
    return _task_to_dict(t)


async def delete_task(db: AsyncSession, task_id: int) -> None:
    """Delete a task. Raises 404 if not found."""
    t = await db.get(Task, task_id)
    if not t:
        raise BusinessException(code=404, message="任务不存在")
    await db.delete(t)


async def toggle_task(db: AsyncSession, task_id: int, is_enabled: bool) -> bool:
    """Toggle task enabled state. Returns False if task not found."""
    t = await db.get(Task, task_id)
    if not t:
        raise BusinessException(code=404, message="任务不存在")
    t.is_enabled = is_enabled
    return is_enabled


async def execute_task(db: AsyncSession, task_id: int) -> dict:
    """Execute a task: create a TaskLog and update last_execute_time."""
    t = await db.get(Task, task_id)
    if not t:
        raise BusinessException(code=404, message="任务不存在")

    now = datetime.now(timezone.utc)

    task_log = TaskLog(
        task_id=task_id,
        start_time=now,
        end_time=now,
        duration_ms=100,
        status="completed",
        total_devices=1,
        success_devices=1,
        failed_devices=0,
        error_message="",
    )
    db.add(task_log)

    t.last_execute_time = now
    await db.flush()

    return {
        "success": True,
        "execution_id": task_log.id,
    }


async def get_task_logs(db: AsyncSession, task_id: int) -> dict:
    """Return all logs for a given task."""
    result = await db.execute(
        select(TaskLog)
        .where(TaskLog.task_id == task_id)
        .order_by(TaskLog.id.desc())
    )
    items = [_task_log_to_dict(log) for log in result.scalars().all()]
    return {"items": items, "total": len(items)}


async def get_task_device_log(
    db: AsyncSession, log_id: int, *, status: str | None = None,
) -> dict:
    """Return task device list for a given log, optionally filtered by status."""
    stmt = select(TaskDevice).where(TaskDevice.log_id == log_id)
    if status:
        stmt = stmt.where(TaskDevice.status == status)
    stmt = stmt.order_by(TaskDevice.id)

    result = await db.execute(stmt)
    devices = [_task_device_to_dict(d) for d in result.scalars().all()]

    total = len(devices)
    success_count = sum(1 for d in devices if d["status"] == "success")
    failed_count = sum(1 for d in devices if d["status"] == "failed")

    return {
        "log_id": log_id,
        "devices": devices,
        "total": total,
        "success_count": success_count,
        "failed_count": failed_count,
    }
