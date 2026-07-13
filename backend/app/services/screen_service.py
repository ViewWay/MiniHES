"""大屏数据服务。

为大屏监控页面提供聚合数据，使用 Redis 缓存热点查询（TTL 30s）。
"""

import logging
from datetime import datetime, timezone
from functools import partial

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import cached
from app.models.alarm import Alarm
from app.models.meter import Meter, MeterSnapshot
from app.models.meter_point import MeterReading
from app.models.task import Task

logger = logging.getLogger(__name__)


async def get_overview(db: AsyncSession) -> dict:
    """大屏总览数据（Redis 缓存 30s）。

    包含：设备总数/在线率、告警统计、今日采集量、任务执行统计。
    """
    return await cached(
        "screen:overview",
        ttl=30,
        fetch_func=partial(_fetch_overview, db),
    )


async def _fetch_overview(db: AsyncSession) -> dict:
    """从 PG 查询总览原始数据。"""
    now = datetime.now(timezone.utc)

    # 设备统计
    meter_total = (
        await db.execute(select(func.count()).select_from(Meter).where(Meter.current_status == "in_use"))
    ).scalar() or 0

    # 在线设备（通过快照）
    online_result = await db.execute(
        select(func.count()).select_from(MeterSnapshot).where(MeterSnapshot.online_status == True)  # noqa: E712
    )
    meter_online = online_result.scalar() or 0

    # 告警统计
    alarm_unhandled = (
        await db.execute(
            select(func.count()).select_from(Alarm).where(Alarm.is_handled == False)  # noqa: E712
        )
    ).scalar() or 0

    alarm_critical = (
        await db.execute(
            select(func.count()).select_from(Alarm).where(Alarm.is_handled == False, Alarm.severity == "critical")  # noqa: E712
        )
    ).scalar() or 0

    # 今日采集量
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    reading_today = (
        await db.execute(select(func.count()).select_from(MeterReading).where(MeterReading.reading_time >= today_start))
    ).scalar() or 0

    # 任务统计
    task_active = (
        await db.execute(
            select(func.count()).select_from(Task).where(Task.is_enabled == True)  # noqa: E712
        )
    ).scalar() or 0

    return {
        "meters": {
            "total": meter_total,
            "online": meter_online,
            "offline": max(meter_total - meter_online, 0),
            "online_rate": round(meter_online / meter_total * 100, 1) if meter_total else 0,
        },
        "alarms": {
            "unhandled": alarm_unhandled,
            "critical": alarm_critical,
        },
        "collection": {
            "readings_today": reading_today,
        },
        "tasks": {
            "active": task_active,
        },
        "updated_at": now.isoformat(),
    }


async def get_project_screen(db: AsyncSession, project_id: int) -> dict:
    """项目大屏数据（Redis 缓存 30s）。"""
    cache_key = f"screen:project:{project_id}"
    return await cached(
        cache_key,
        ttl=30,
        fetch_func=partial(_fetch_project_screen, db, project_id),
    )


async def _fetch_project_screen(db: AsyncSession, project_id: int) -> dict:
    """从 PG 查询项目维度大屏数据。"""
    now = datetime.now(timezone.utc)

    # 项目设备
    meter_total = (
        await db.execute(
            select(func.count())
            .select_from(Meter)
            .where(Meter.project_id == project_id, Meter.current_status == "in_use")
        )
    ).scalar() or 0

    # 项目在线
    online_result = await db.execute(
        select(func.count())
        .select_from(MeterSnapshot)
        .join(Meter, Meter.id == MeterSnapshot.meter_id)
        .where(Meter.project_id == project_id, MeterSnapshot.online_status == True)  # noqa: E712
    )
    meter_online = online_result.scalar() or 0

    # 项目告警
    alarm_count = (
        await db.execute(
            select(func.count())
            .select_from(Alarm)
            .join(Meter, Meter.id == Alarm.meter_id)
            .where(Meter.project_id == project_id, Alarm.is_handled == False)  # noqa: E712
        )
    ).scalar() or 0

    # 今日采集
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    reading_today = (
        await db.execute(
            select(func.count())
            .select_from(MeterReading)
            .join(Meter, Meter.id == MeterReading.meter_id)
            .where(Meter.project_id == project_id, MeterReading.reading_time >= today_start)
        )
    ).scalar() or 0

    # 设备列表（前 20）
    meter_rows = await db.execute(
        select(Meter, MeterSnapshot)
        .outerjoin(MeterSnapshot, MeterSnapshot.meter_id == Meter.id)
        .where(Meter.project_id == project_id)
        .limit(20)
    )
    meters = []
    for meter, snap in meter_rows.all():
        meters.append(
            {
                "id": meter.id,
                "serial_number": meter.serial_number,
                "meter_name": meter.meter_name,
                "online": snap.online_status if snap else False,
                "signal_strength": snap.signal_strength if snap else None,
                "last_comm_time": snap.last_comm_time.isoformat() if snap and snap.last_comm_time else None,
            }
        )

    return {
        "project_id": project_id,
        "meters": {
            "total": meter_total,
            "online": meter_online,
            "offline": max(meter_total - meter_online, 0),
        },
        "alarms": {"unhandled": alarm_count},
        "collection": {"readings_today": reading_today},
        "meter_list": meters,
        "updated_at": now.isoformat(),
    }


async def get_meter_detail(db: AsyncSession, meter_id: int) -> dict:
    """单电表大屏详情。"""
    meter = await db.get(Meter, meter_id)
    if not meter:
        return None

    # 快照
    snap_result = await db.execute(select(MeterSnapshot).where(MeterSnapshot.meter_id == meter_id))
    snap = snap_result.scalar_one_or_none()

    # 最近 10 条读数
    readings_result = await db.execute(
        select(MeterReading)
        .where(MeterReading.meter_id == meter_id)
        .order_by(MeterReading.reading_time.desc())
        .limit(10)
    )
    readings = readings_result.scalars().all()

    # 最近告警
    alarm_result = await db.execute(
        select(Alarm).where(Alarm.meter_id == meter_id).order_by(Alarm.created_at.desc()).limit(5)
    )
    alarms = alarm_result.scalars().all()

    return {
        "meter": {
            "id": meter.id,
            "serial_number": meter.serial_number,
            "meter_name": meter.meter_name,
            "model": meter.model,
            "firmware_version": meter.firmware_version,
            "location": meter.location,
            "current_status": meter.current_status,
        },
        "snapshot": {
            "online": snap.online_status if snap else False,
            "signal_strength": snap.signal_strength if snap else None,
            "last_comm_time": snap.last_comm_time.isoformat() if snap and snap.last_comm_time else None,
            "firmware_version": snap.firmware_version if snap else None,
            "error_code": snap.error_code if snap else "",
        },
        "recent_readings": [
            {
                "reading_value": float(r.reading_value) if r.reading_value else None,
                "reading_time": r.reading_time.isoformat() if r.reading_time else None,
                "quality": r.quality,
            }
            for r in readings
        ],
        "recent_alarms": [
            {
                "alarm_type": a.alarm_type,
                "severity": a.severity,
                "alarm_message": a.alarm_message,
                "is_handled": a.is_handled,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alarms
        ],
    }
