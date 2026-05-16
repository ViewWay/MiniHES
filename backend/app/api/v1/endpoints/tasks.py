from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from app.core.auth import get_current_user
from app.core.database import AsyncSessionLocal as async_session
from app.core.response import success
from app.models.task import Task, TaskLog, TaskDevice

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
async def list_tasks(
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    task_type: str = Query(default=None),
    task_category: str = Query(default=None),
    status: str = Query(default=None),
    is_enabled: bool = Query(default=None),
):
    async with async_session() as session:
        stmt = select(Task)
        count_stmt = select(func.count()).select_from(Task)

        if task_type:
            stmt = stmt.where(Task.task_type == task_type)
            count_stmt = count_stmt.where(Task.task_type == task_type)
        if is_enabled is not None:
            stmt = stmt.where(Task.is_enabled == is_enabled)
            count_stmt = count_stmt.where(Task.is_enabled == is_enabled)

        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        running_count_result = await session.execute(
            select(func.count()).select_from(Task).where(Task.is_enabled == True)
        )
        running_count = running_count_result.scalar() or 0

        stmt = stmt.order_by(Task.id).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
        tasks = result.scalars().all()

        items = [_task_to_dict(t) for t in tasks]
        return success({"items": items, "total": total, "running_count": running_count})


@router.post("")
async def create_task(body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        t = Task(**body)
        session.add(t)
        await session.commit()
        await session.refresh(t)
        return success({"id": t.id, **_task_to_dict(t)})


@router.get("/{task_id}")
async def get_task(task_id: int):
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        t = result.scalar_one_or_none()
        if not t:
            return success(None)
        return success(_task_to_dict(t))


@router.put("/{task_id}")
async def update_task(task_id: int, body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        t = result.scalar_one_or_none()
        if not t:
            return success(None)
        for key, value in body.items():
            if hasattr(t, key):
                setattr(t, key, value)
        await session.commit()
        return success(_task_to_dict(t))


@router.delete("/{task_id}")
async def delete_task(task_id: int, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        t = result.scalar_one_or_none()
        if t:
            await session.delete(t)
            await session.commit()
        return success({"success": True})


@router.post("/{task_id}/execute")
async def execute_task(task_id: int, body: dict = None):
    from datetime import datetime, timezone
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        t = result.scalar_one_or_none()
        if not t:
            return success(None)
        now = datetime.now(timezone.utc)
        log = TaskLog(
            task_id=task_id,
            start_time=now,
            end_time=now,
            duration_ms=100,
            status="completed",
            total_devices=1,
            success_devices=1,
            failed_devices=0,
        )
        session.add(log)
        t.last_execute_time = now
        await session.commit()
        await session.refresh(log)
        return success({"success": True, "execution_id": log.id})


@router.get("/{task_id}/logs")
async def get_task_logs(task_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(TaskLog).where(TaskLog.task_id == task_id).order_by(TaskLog.id.desc())
        )
        items = [
            {
                "id": l.id,
                "task_id": l.task_id,
                "status": l.status,
                "start_time": l.start_time.strftime("%Y-%m-%d %H:%M:%S") if l.start_time else "",
                "end_time": l.end_time.strftime("%Y-%m-%d %H:%M:%S") if l.end_time else "",
                "duration_ms": l.duration_ms,
                "total_devices": l.total_devices,
                "success_devices": l.success_devices,
                "failed_devices": l.failed_devices,
            }
            for l in result.scalars().all()
        ]
        return success({"items": items, "total": len(items)})


@router.patch("/{task_id}/toggle")
async def toggle_task(task_id: int, body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        t = result.scalar_one_or_none()
        if not t:
            return success(None)
        t.is_enabled = body.get("is_enabled", not t.is_enabled)
        await session.commit()
        return success({"success": True, "is_enabled": t.is_enabled})


def _task_to_dict(t: Task) -> dict:
    return {
        "id": t.id,
        "task_name": t.task_name,
        "task_type": t.task_type,
        "schedule_config": t.schedule_config or {},
        "execution_content": t.execution_content or {},
        "filter_config": t.filter_config or {},
        "priority": t.priority,
        "retry_times": t.retry_times,
        "timeout": t.timeout,
        "is_enabled": t.is_enabled,
        "last_execute_time": t.last_execute_time.strftime("%Y-%m-%d %H:%M:%S") if t.last_execute_time else None,
        "next_execute_time": t.next_execute_time.strftime("%Y-%m-%d %H:%M:%S") if t.next_execute_time else None,
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
        "updated_at": t.updated_at.strftime("%Y-%m-%d %H:%M:%S") if t.updated_at else "",
    }
