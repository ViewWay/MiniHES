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
    # 通信告警扫描：每 15 分钟检测一次离线设备
    _scheduler.add_job(
        _scan_communication_alarms,
        "interval",
        minutes=15,
        id="comm_alarm_scanner",
        name="扫描通信超时告警",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info("任务调度器已启动，扫描间隔 %ds，通信告警间隔 15min", _SCAN_INTERVAL_SECONDS)
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


async def _scan_communication_alarms():
    """扫描通信超时告警（离线设备检测）。

    每 15 分钟执行一次，检查所有在用电表的最后通信时间，
    对超过 offline_hours 阈值的设备生成 communication 类型告警。
    """
    from app.core.database import AsyncSessionLocal
    from app.services.alarm_engine import check_communication_alarms

    try:
        async with AsyncSessionLocal() as db:
            alarms = await check_communication_alarms(db)
            if alarms:
                await db.commit()
                logger.info("通信告警扫描完成，生成 %d 条告警", len(alarms))
    except Exception as e:
        logger.error("通信告警扫描异常: %s", e)
