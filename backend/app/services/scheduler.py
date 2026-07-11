"""APScheduler 任务调度引擎。

在 FastAPI lifespan 中启动，每 60 秒扫描 col_task 表中
is_enabled=True AND next_execute_time <= now() 的任务并执行。

用法（main.py lifespan）：
    from app.services.scheduler import init_scheduler, shutdown_scheduler
    await init_scheduler()
    yield
    await shutdown_scheduler()
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_SCAN_INTERVAL_SECONDS = 60


def init_scheduler():
    """初始化并启动调度器（非阻塞，在 FastAPI lifespan 中调用）。"""
    global _scheduler
    if _scheduler is not None:
        logger.warning("调度器已在运行，跳过重复初始化")
        return _scheduler

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _scan_and_execute,
        "interval",
        seconds=_SCAN_INTERVAL_SECONDS,
        id="task_scanner",
        name="扫描到期任务并执行",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info("任务调度器已启动，扫描间隔 %ds", _SCAN_INTERVAL_SECONDS)
    return _scheduler


async def shutdown_scheduler():
    """关闭调度器。"""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("任务调度器已关闭")


async def _scan_and_execute():
    """扫描到期任务并执行。"""
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.task import Task
    from app.services.task_service import _compute_next_execute_time, execute_task

    now = datetime.now(timezone.utc)

    try:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(Task)
                .where(Task.is_enabled == True)  # noqa: E712
                .where(Task.next_execute_time <= now)
                .order_by(Task.priority.desc(), Task.next_execute_time)
                .limit(50)
            )
            result = await db.execute(stmt)
            due_tasks = result.scalars().all()

            if not due_tasks:
                return

            logger.info("发现 %d 个到期任务", len(due_tasks))

            for task in due_tasks:
                try:
                    logger.info(
                        "执行任务: id=%d name=%s type=%s",
                        task.id,
                        task.task_name,
                        task.task_type,
                    )
                    await execute_task(db, task.id)

                    # 计算下次执行时间
                    task.next_execute_time = _compute_next_execute_time(task)

                    await db.commit()
                    logger.info(
                        "任务 %d 执行完成，下次执行: %s",
                        task.id,
                        task.next_execute_time,
                    )
                except Exception as e:
                    logger.error("任务 %d 执行失败: %s", task.id, e)
                    await db.rollback()

    except Exception as e:
        logger.error("任务扫描异常: %s", e)
