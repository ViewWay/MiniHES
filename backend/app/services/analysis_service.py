"""Analysis & reporting service layer.

Each report function returns a unified structure::

    {
        "summary": {  ...kpi cards... , "demo": bool },
        "charts":  { chart_name: {"labels": [...], "series": {name: [..]} } },
        "items":   [ ...paginated rows... ],
        "total":   int,
    }

When the database has no real data for a given report, we fall back to
representative mock values and set ``summary.demo = True`` so the frontend
can show a "demo data" badge.
"""

from __future__ import annotations

import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alarm import Alarm
from app.models.meter import Meter, MeterSnapshot
from app.models.meter_point import ReadingDailySummary
from app.models.task import DataQuality, Task, TaskDevice, TaskLog

# ── helpers ─────────────────────────────────────────────────────────────


def _fmt_dt(dt: datetime.datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _fmt_date(d: datetime.date | None) -> str | None:
    if d is None:
        return None
    return d.strftime("%Y-%m-%d")


def _hours_since(dt: datetime.datetime | None) -> float | None:
    """Return hours elapsed since *dt* relative to now, or None."""
    if dt is None:
        return None
    delta = datetime.datetime.now(dt.tzinfo) - dt
    return round(delta.total_seconds() / 3600, 1)


def _silence_label(hours: float | None) -> str:
    if hours is None:
        return "—"
    if hours < 48:
        return f"{hours:.0f}h"
    if hours < 168:
        return f"{hours / 24:.1f}d"
    return f"{hours / 24:.0f}d"


def _parse_date_range(date_from: str | None, date_to: str | None) -> tuple[datetime.date, datetime.date]:
    """Parse flexible date strings into a (start, end) pair."""
    today = datetime.date.today()
    end = datetime.date.fromisoformat(date_to) if date_to else today
    start = datetime.date.fromisoformat(date_from) if date_from else end - datetime.timedelta(days=6)
    return start, end


# ── 1. R-01 Communication Success/Failure Rate ──────────────────────────


async def get_comm_success_rate(
    db: AsyncSession,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    project_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    start, end = _parse_date_range(date_from, date_to)

    # Build base query for task logs in the date range
    stmt = select(TaskLog).where(
        TaskLog.start_time >= datetime.datetime.combine(start, datetime.time.min),
        TaskLog.start_time <= datetime.datetime.combine(end, datetime.time.max),
    )
    if project_id is not None:
        # 过滤该项目下的电表对应的任务日志
        from app.models.meter import Meter

        select(Meter.id).where(Meter.project_id == project_id)
        stmt = stmt.where(
            TaskLog.task_id.in_(select(Task.id).where(Task.filter_config["project_id"].as_integer() == project_id))
        ).where(TaskLog.id.isnot(None))

    result = await db.execute(stmt.order_by(TaskLog.start_time.desc()))
    logs = result.scalars().all()

    total_attempts = sum(log.total_devices for log in logs)
    total_success = sum(log.success_devices for log in logs)
    total_failed = sum(log.failed_devices for log in logs)

    # 从真实 TaskDevice.error_message 分类统计失败原因
    failure_reasons = {"timeout": 0, "protocol": 0, "offline": 0, "signal": 0, "other": 0}
    if total_failed > 0:
        log_ids = [log.id for log in logs]
        if log_ids:
            td_result = await db.execute(
                select(TaskDevice.error_message).where(
                    TaskDevice.log_id.in_(log_ids),
                    TaskDevice.status == "failed",
                )
            )
            for (msg,) in td_result.all():
                msg_lower = (msg or "").lower()
                if "timeout" in msg_lower or "超时" in (msg or ""):
                    failure_reasons["timeout"] += 1
                elif "protocol" in msg_lower or "协议" in (msg or ""):
                    failure_reasons["protocol"] += 1
                elif "offline" in msg_lower or "离线" in (msg or "") or "refuse" in msg_lower:
                    failure_reasons["offline"] += 1
                elif "signal" in msg_lower or "信号" in (msg or ""):
                    failure_reasons["signal"] += 1
                else:
                    failure_reasons["other"] += 1

    demo = total_attempts == 0

    if demo:
        total_attempts, total_success, total_failed = 0, 0, 0

    success_rate = round(total_success / total_attempts * 100, 1) if total_attempts else 0
    success_rate = round(total_success / total_attempts * 100, 1) if total_attempts else 0
    failure_rate = round(total_failed / total_attempts * 100, 1) if total_attempts else 0

    # Daily breakdown for charts
    daily_map: dict[str, dict] = {}
    for log in logs:
        day = _fmt_date(log.start_time.date()) if log.start_time else None
        if not day:
            continue
        bucket = daily_map.setdefault(day, {"attempts": 0, "success": 0, "failed": 0, "retries": 0})
        bucket["attempts"] += log.total_devices
        bucket["success"] += log.success_devices
        bucket["failed"] += log.failed_devices

    daily_labels = sorted(daily_map.keys())[-14:]
    daily_attempts = [daily_map[d]["attempts"] for d in daily_labels]
    daily_success_pct = [
        round(daily_map[d]["success"] / daily_map[d]["attempts"] * 100, 1) if daily_map[d]["attempts"] else 0
        for d in daily_labels
    ]

    # Paginated table items from logs
    offset = (page - 1) * page_size
    total = len(logs)
    page_logs = logs[offset : offset + page_size]
    items = [
        {
            "date": _fmt_dt(log.start_time),
            "total_attempts": log.total_devices,
            "success": log.success_devices,
            "failed": log.failed_devices,
            "success_rate": round(log.success_devices / log.total_devices * 100, 1) if log.total_devices else 0,
            "duration_ms": log.duration_ms,
            "status": log.status,
        }
        for log in page_logs
    ]

    return {
        "summary": {
            "total_attempts": total_attempts,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "total_success": total_success,
            "total_failed": total_failed,
            "demo": demo,
        },
        "charts": {
            "daily_trend": {
                "labels": daily_labels or ["—"],
                "series": {
                    "attempts": daily_attempts or [0],
                    "success_rate": daily_success_pct or [0],
                },
            },
            "failure_reasons": {
                "labels": ["超时", "协议错误", "设备离线", "信号弱", "其他"],
                "series": {
                    "count": [
                        failure_reasons["timeout"],
                        failure_reasons["protocol"],
                        failure_reasons["offline"],
                        failure_reasons["signal"],
                        failure_reasons["other"],
                    ]
                },
            },
        },
        "items": items,
        "total": total,
    }


# ── 2. UC-8 Non-Communicating Devices ────────────────────────────────────


async def get_non_comm_devices(
    db: AsyncSession,
    *,
    hours_min: int = 24,
    project_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    stmt = (
        select(Meter, MeterSnapshot)
        .outerjoin(MeterSnapshot, MeterSnapshot.meter_id == Meter.id)
        .where(Meter.current_status == "in_use")
    )
    if project_id is not None:
        stmt = stmt.where(Meter.project_id == project_id)

    result = await db.execute(stmt)
    rows = result.all()

    # Filter: snapshot offline OR last_comm_time older than threshold
    non_comm = []
    for meter, snap in rows:
        is_non_comm = False
        silence_hours: float | None = None
        if snap and snap.last_comm_time:
            silence_hours = _hours_since(snap.last_comm_time)
            if silence_hours and silence_hours >= hours_min:
                is_non_comm = True
        elif snap and not snap.online_status:
            is_non_comm = True
            silence_hours = _hours_since(snap.last_comm_time) if snap.last_comm_time else 999
        if is_non_comm:
            non_comm.append((meter, snap, silence_hours))

    demo = len(non_comm) == 0

    # Aging buckets
    buckets = {"24h_48h": 0, "2d_7d": 0, "7d_30d": 0, "30d_plus": 0}
    for _, _, hours in non_comm:
        if hours is None:
            continue
        if hours < 48:
            buckets["24h_48h"] += 1
        elif hours < 168:
            buckets["2d_7d"] += 1
        elif hours < 720:
            buckets["7d_30d"] += 1
        else:
            buckets["30d_plus"] += 1

    if demo:
        buckets = {"24h_48h": 0, "2d_7d": 0, "7d_30d": 0, "30d_plus": 0}

    total = len(non_comm)
    total = len(non_comm)
    offset = (page - 1) * page_size
    page_rows = non_comm[offset : offset + page_size]
    items = [
        {
            "id": meter.id,
            "serial_number": meter.serial_number,
            "meter_name": meter.meter_name,
            "location": meter.location,
            "last_comm_time": _fmt_dt(snap.last_comm_time) if snap else None,
            "silence_hours": hours,
            "silence_label": _silence_label(hours),
            "online_status": snap.online_status if snap else False,
            "signal_strength": snap.signal_strength if snap else None,
        }
        for meter, snap, hours in page_rows
    ]

    return {
        "summary": {
            "total_non_comm": total if not demo else sum(buckets.values()),
            "24h_48h": buckets["24h_48h"],
            "2d_7d": buckets["2d_7d"],
            "7d_30d": buckets["7d_30d"],
            "30d_plus": buckets["30d_plus"],
            "demo": demo,
        },
        "charts": {
            "aging_buckets": {
                "labels": ["24-48h", "2-7天", "7-30天", "30天+"],
                "series": {
                    "count": [
                        buckets["24h_48h"],
                        buckets["2d_7d"],
                        buckets["7d_30d"],
                        buckets["30d_plus"],
                    ]
                },
            },
        },
        "items": items,
        "total": total,
    }


# ── 3. R-07 Read Completeness ────────────────────────────────────────────


async def get_read_completeness(
    db: AsyncSession,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    project_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    start, end = _parse_date_range(date_from, date_to)

    stmt = select(DataQuality).where(
        DataQuality.stat_date >= start,
        DataQuality.stat_date <= end,
    )
    if project_id is not None:
        stmt = stmt.join(Meter, DataQuality.meter_id == Meter.id).where(Meter.project_id == project_id)

    result = await db.execute(stmt.order_by(DataQuality.stat_date.desc()))
    records = result.scalars().all()

    demo = len(records) == 0

    total_points = sum(r.total_points for r in records)
    success_points = sum(r.success_points for r in records)
    failed_points = sum(r.failed_points for r in records)
    completeness = round(success_points / total_points * 100, 1) if total_points else 0

    if demo:
        total_points, success_points, failed_points = 0, 0, 0
        completeness = 0  # demo: no data

    # By meter aggregation
    # By meter aggregation
    meter_map: dict[int, dict] = {}
    for r in records:
        bucket = meter_map.setdefault(r.meter_id, {"total": 0, "success": 0, "failed": 0})
        bucket["total"] += r.total_points
        bucket["success"] += r.success_points
        bucket["failed"] += r.failed_points

    total = len(meter_map)
    offset = (page - 1) * page_size
    meter_ids = list(meter_map.keys())[offset : offset + page_size]

    # Fetch meter names
    meter_names: dict[int, tuple] = {}
    if meter_ids:
        name_result = await db.execute(
            select(Meter.id, Meter.serial_number, Meter.meter_name).where(Meter.id.in_(meter_ids))
        )
        meter_names = {row[0]: (row[1], row[2]) for row in name_result.all()}

    items = []
    for mid in meter_ids:
        bucket = meter_map[mid]
        mc = round(bucket["success"] / bucket["total"] * 100, 1) if bucket["total"] else 0
        sn, name = meter_names.get(mid, ("—", "—"))
        items.append(
            {
                "meter_id": mid,
                "serial_number": sn,
                "meter_name": name,
                "total_points": bucket["total"],
                "success_points": bucket["success"],
                "failed_points": bucket["failed"],
                "completeness": mc,
            }
        )

    # 计算分布桶
    dist_100 = dist_98 = dist_95 = dist_90 = dist_below = 0
    for b in meter_map.values():
        if not b["total"]:
            continue
        pct = b["success"] / b["total"] * 100
        if pct >= 100:
            dist_100 += 1
        elif pct >= 98:
            dist_98 += 1
        elif pct >= 95:
            dist_95 += 1
        elif pct >= 90:
            dist_90 += 1
        else:
            dist_below += 1

    return {
        "summary": {
            "completeness": completeness,
            "total_points": total_points,
            "success_points": success_points,
            "failed_points": failed_points,
            "total_meters": total,
            "below_sla": sum(1 for b in meter_map.values() if b["total"] and b["success"] / b["total"] < 0.98),
            "demo": demo,
        },
        "charts": {
            "distribution": {
                "labels": ["100%", "98-99.9%", "95-97.9%", "90-94.9%", "<90%"],
                "series": {"count": [dist_100, dist_98, dist_95, dist_90, dist_below]},
            },
        },
        "items": items,
        "total": total,
    }


# ── 4. R-10 Retry Analysis ───────────────────────────────────────────────


async def get_retry_analysis(
    db: AsyncSession,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    project_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    start, end = _parse_date_range(date_from, date_to)

    stmt = (
        select(TaskDevice)
        .join(TaskLog, TaskDevice.log_id == TaskLog.id)
        .where(
            TaskLog.start_time >= datetime.datetime.combine(start, datetime.time.min),
            TaskLog.start_time <= datetime.datetime.combine(end, datetime.time.max),
            TaskDevice.retry_count > 0,
        )
    )

    result = await db.execute(stmt.order_by(TaskDevice.retry_count.desc()))
    devices = result.scalars().all()

    demo = len(devices) == 0

    total_retries = sum(d.retry_count for d in devices)
    avg_retries = round(total_retries / len(devices), 1) if devices else 0
    high_retry_count = sum(1 for d in devices if d.retry_count >= 3)

    if demo:
        total_retries, avg_retries, high_retry_count = 0, 0, 0

    # Paginate
    # Paginate
    total = len(devices)
    offset = (page - 1) * page_size
    page_devices = devices[offset : offset + page_size]

    # Fetch meter info
    meter_ids = list({d.meter_id for d in page_devices})
    meter_names: dict[int, str] = {}
    if meter_ids:
        name_result = await db.execute(select(Meter.id, Meter.serial_number).where(Meter.id.in_(meter_ids)))
        meter_names = {row[0]: row[1] for row in name_result.all()}

    items = [
        {
            "id": d.id,
            "meter_id": d.meter_id,
            "serial_number": meter_names.get(d.meter_id, "—"),
            "retry_count": d.retry_count,
            "error_code": d.error_code,
            "error_message": d.error_message,
            "status": d.status,
            "duration_ms": d.duration_ms,
            "start_time": _fmt_dt(d.start_time),
        }
        for d in page_devices
    ]

    return {
        "summary": {
            "total_retries": total_retries,
            "avg_retries": avg_retries,
            "high_retry_count": high_retry_count,
            "total_devices": total,
            "demo": demo,
        },
        "charts": {
            "retry_distribution": {
                "labels": ["1次", "2次", "3次", "4次", "5次+"],
                "series": {
                    "count": [
                        sum(1 for d in devices if d.retry_count == 1),
                        sum(1 for d in devices if d.retry_count == 2),
                        sum(1 for d in devices if d.retry_count == 3),
                        sum(1 for d in devices if d.retry_count == 4),
                        sum(1 for d in devices if d.retry_count >= 5),
                    ]
                },
            },
        },
        "items": items,
        "total": total,
    }


# ── 5. R-12 Open / Unacknowledged Alarms ────────────────────────────────


async def get_open_alarms_report(
    db: AsyncSession,
    *,
    severity: str | None = None,
    alarm_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    stmt = select(Alarm).where(Alarm.is_handled == False)  # noqa: E712
    if severity:
        stmt = stmt.where(Alarm.severity == severity)
    if alarm_type:
        stmt = stmt.where(Alarm.alarm_type == alarm_type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    result = await db.execute(stmt.order_by(Alarm.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    alarms = result.scalars().all()

    demo = total == 0

    # KPI summary from full dataset
    all_stmt = select(Alarm).where(Alarm.is_handled == False)  # noqa: E712
    all_result = await db.execute(all_stmt)
    all_alarms = all_result.scalars().all()

    critical = sum(1 for a in all_alarms if a.severity == "critical")
    major = sum(1 for a in all_alarms if a.severity == "warning")
    info = sum(1 for a in all_alarms if a.severity == "info")

    if demo:
        total, critical, major, info = 0, 0, 0, 0

    avg_age = 0
    avg_age = 0
    if all_alarms:
        ages = [_hours_since(a.created_at) or 0 for a in all_alarms]
        avg_age = round(sum(ages) / len(ages), 1) if ages else 0

    items = [
        {
            "id": a.id,
            "alarm_type": a.alarm_type,
            "severity": a.severity,
            "alarm_message": a.alarm_message,
            "alarm_value": float(a.alarm_value) if a.alarm_value else None,
            "threshold_value": float(a.threshold_value) if a.threshold_value else None,
            "meter_id": a.meter_id,
            "created_at": _fmt_dt(a.created_at),
            "age_hours": _hours_since(a.created_at),
        }
        for a in alarms
    ]

    return {
        "summary": {
            "total_open": total,
            "critical": critical,
            "major": major,
            "info": info,
            "avg_age_hours": avg_age,
            "demo": demo,
        },
        "charts": {
            "by_severity": {
                "labels": ["严重", "警告", "信息"],
                "series": {"count": [critical, major, info]},
            },
        },
        "items": items,
        "total": total,
    }


# ── 6. R-13 Alarm Trend & Volume ────────────────────────────────────────


async def get_alarm_trend(
    db: AsyncSession,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    start, end = _parse_date_range(date_from, date_to)
    # Extend range for trend
    start = start - datetime.timedelta(days=84)  # 12 weeks

    stmt = select(Alarm).where(
        Alarm.created_at >= datetime.datetime.combine(start, datetime.time.min),
        Alarm.created_at <= datetime.datetime.combine(end, datetime.time.max),
    )
    result = await db.execute(stmt.order_by(Alarm.created_at.desc()))
    alarms = result.scalars().all()

    demo = len(alarms) == 0

    # Group by week
    week_map: dict[str, dict[str, int]] = {}
    for a in alarms:
        if not a.created_at:
            continue
        year, week, _ = a.created_at.isocalendar()
        week_key = f"{year}-W{week:02d}"
        bucket = week_map.setdefault(
            week_key,
            {"critical": 0, "warning": 0, "info": 0},
        )
        if a.severity in bucket:
            bucket[a.severity] += 1

    week_labels = sorted(week_map.keys())[-16:]

    if demo:
        week_labels = [f"W{i}" for i in range(1, 17)]
        week_map = {w: {"critical": 0, "warning": 0, "info": 0} for w in week_labels}

    # Paginated items
    # Paginated items
    total = len(alarms)
    offset = (page - 1) * page_size
    page_alarms = alarms[offset : offset + page_size]
    items = [
        {
            "id": a.id,
            "alarm_type": a.alarm_type,
            "severity": a.severity,
            "alarm_message": a.alarm_message,
            "meter_id": a.meter_id,
            "created_at": _fmt_dt(a.created_at),
            "is_handled": a.is_handled,
        }
        for a in page_alarms
    ]

    return {
        "summary": {
            "total_alarms": total if not demo else 142580,
            "weekly_avg": round(total / 16) if not demo else 8911,
            "demo": demo,
        },
        "charts": {
            "weekly_trend": {
                "labels": week_labels,
                "series": {
                    "critical": [week_map[w]["critical"] for w in week_labels],
                    "warning": [week_map[w]["warning"] for w in week_labels],
                    "info": [week_map[w]["info"] for w in week_labels],
                },
            },
        },
        "items": items,
        "total": total,
    }


# ── 7. R-16 Device Health ────────────────────────────────────────────────


async def get_device_health(
    db: AsyncSession,
    *,
    project_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    stmt = (
        select(Meter, MeterSnapshot)
        .outerjoin(MeterSnapshot, MeterSnapshot.meter_id == Meter.id)
        .where(Meter.current_status == "in_use")
    )
    if project_id is not None:
        stmt = stmt.where(Meter.project_id == project_id)

    result = await db.execute(stmt)
    rows = result.all()

    demo = len(rows) == 0

    total = len(rows)
    healthy = sum(1 for _, s in rows if s and s.online_status and (not s.error_code or s.error_code == ""))
    watch = sum(
        1
        for _, s in rows
        if s and s.error_code and s.error_code != "" and s.signal_strength is not None and s.signal_strength < 50
    )
    alert = sum(1 for _, s in rows if s and s.online_status == False)  # noqa: E712

    if demo:
        total, healthy, watch, alert = 0, 0, 0, 0

    # Group by model
    # Group by model
    model_map: dict[str, dict] = {}
    for meter, snap in rows:
        model = meter.model or "未知"
        bucket = model_map.setdefault(model, {"total": 0, "healthy": 0, "alert": 0})
        bucket["total"] += 1
        if snap and snap.online_status and not snap.error_code:
            bucket["healthy"] += 1
        elif snap and not snap.online_status:
            bucket["alert"] += 1

    model_labels = sorted(model_map.keys()) or ["KFM-S100", "KFM-S200", "KFM-T300"]

    # Paginate
    offset = (page - 1) * page_size
    page_rows = rows[offset : offset + page_size]
    items = [
        {
            "id": meter.id,
            "serial_number": meter.serial_number,
            "meter_name": meter.meter_name,
            "model": meter.model or "—",
            "firmware_version": meter.firmware_version or (snap.firmware_version if snap else "—"),
            "online_status": snap.online_status if snap else False,
            "signal_strength": snap.signal_strength if snap else None,
            "error_code": snap.error_code if snap else "",
            "health": (
                "healthy"
                if snap and snap.online_status and not snap.error_code
                else "alert"
                if snap and not snap.online_status
                else "watch"
            ),
        }
        for meter, snap in page_rows
    ]

    return {
        "summary": {
            "total_meters": total,
            "healthy": healthy,
            "watch": watch,
            "alert": alert,
            "health_score": round(healthy / total * 100, 1) if total else 0,
            "demo": demo,
        },
        "charts": {
            "by_model": {
                "labels": model_labels,
                "series": {
                    "total": [model_map.get(m, {}).get("total", 0) for m in model_labels],
                    "healthy": [model_map.get(m, {}).get("healthy", 0) for m in model_labels],
                    "alert": [model_map.get(m, {}).get("alert", 0) for m in model_labels],
                },
            },
        },
        "items": items,
        "total": total,
    }


# ── 8. R-18 Signal Strength Aging (battery degraded) ────────────────────


async def get_signal_aging(
    db: AsyncSession,
    *,
    project_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    stmt = (
        select(Meter, MeterSnapshot)
        .outerjoin(MeterSnapshot, MeterSnapshot.meter_id == Meter.id)
        .where(Meter.current_status == "in_use")
    )
    if project_id is not None:
        stmt = stmt.where(Meter.project_id == project_id)

    result = await db.execute(stmt)
    rows = result.all()

    demo = len(rows) == 0

    # Signal buckets (using signal_strength as proxy for battery/health)
    signal_buckets = {"good": 0, "warning": 0, "critical": 0}
    devices_with_signal = []
    for meter, snap in rows:
        if snap and snap.signal_strength is not None:
            devices_with_signal.append((meter, snap))
            if snap.signal_strength >= 60:
                signal_buckets["good"] += 1
            elif snap.signal_strength >= 30:
                signal_buckets["warning"] += 1
            else:
                signal_buckets["critical"] += 1

    if demo:
        signal_buckets = {"good": 0, "warning": 0, "critical": 0}

    total = len(devices_with_signal)
    total = len(devices_with_signal)
    offset = (page - 1) * page_size
    page_rows = devices_with_signal[offset : offset + page_size]
    items = [
        {
            "id": meter.id,
            "serial_number": meter.serial_number,
            "meter_name": meter.meter_name,
            "signal_strength": snap.signal_strength,
            "health": (
                "good" if snap.signal_strength >= 60 else "warning" if snap.signal_strength >= 30 else "critical"
            ),
            "last_comm_time": _fmt_dt(snap.last_comm_time),
            "online_status": snap.online_status,
        }
        for meter, snap in page_rows
    ]

    return {
        "summary": {
            "total_devices": total if not demo else 186,
            "good": signal_buckets["good"],
            "warning": signal_buckets["warning"],
            "critical": signal_buckets["critical"],
            "demo": demo,
        },
        "charts": {
            "health_distribution": {
                "labels": ["良好 (>60%)", "警告 (30-60%)", "严重 (<30%)"],
                "series": {
                    "count": [
                        signal_buckets["good"],
                        signal_buckets["warning"],
                        signal_buckets["critical"],
                    ]
                },
            },
        },
        "items": items,
        "total": total,
    }


# ── 9. R-30 Interval Consumption Trend ───────────────────────────────────


async def get_consumption_trend(
    db: AsyncSession,
    *,
    meter_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    start, end = _parse_date_range(date_from, date_to)

    stmt = select(ReadingDailySummary).where(
        ReadingDailySummary.stat_date >= start,
        ReadingDailySummary.stat_date <= end,
    )
    if meter_id is not None:
        stmt = stmt.where(ReadingDailySummary.meter_id == meter_id)

    result = await db.execute(stmt.order_by(ReadingDailySummary.stat_date.asc()))
    records = result.scalars().all()

    demo = len(records) == 0

    # Group by date
    daily_map: dict[str, dict] = {}
    for r in records:
        day = _fmt_date(r.stat_date)
        if not day:
            continue
        bucket = daily_map.setdefault(day, {"total_delta": 0, "max": 0, "count": 0})
        delta = float(r.delta) if r.delta else float(r.last_value) - float(r.first_value)
        bucket["total_delta"] += delta
        bucket["max"] = max(bucket["max"], float(r.max_value))
        bucket["count"] += 1

    daily_labels = sorted(daily_map.keys())
    daily_values = [round(daily_map[d]["total_delta"], 2) for d in daily_labels]

    if demo:
        daily_labels = [
            (start + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end - start).days + 1)
        ]
        daily_values = [0 for _ in daily_labels]

    total_consumption = round(sum(daily_values), 2)
    total_consumption = round(sum(daily_values), 2)
    avg_daily = round(total_consumption / len(daily_values), 2) if daily_values else 0
    peak = max(daily_values) if daily_values else 0

    # Paginated items — group by meter
    meter_map: dict[int, dict] = {}
    for r in records:
        bucket = meter_map.setdefault(r.meter_id, {"total": 0, "days": 0})
        delta = float(r.delta) if r.delta else float(r.last_value) - float(r.first_value)
        bucket["total"] += delta
        bucket["days"] += 1

    total = len(meter_map)
    offset = (page - 1) * page_size
    meter_ids_page = list(meter_map.keys())[offset : offset + page_size]

    meter_names: dict[int, tuple] = {}
    if meter_ids_page:
        name_result = await db.execute(
            select(Meter.id, Meter.serial_number, Meter.meter_name).where(Meter.id.in_(meter_ids_page))
        )
        meter_names = {row[0]: (row[1], row[2]) for row in name_result.all()}

    items = [
        {
            "meter_id": mid,
            "serial_number": meter_names.get(mid, ("—",))[0],
            "meter_name": meter_names.get(mid, ("—", "—"))[1],
            "total_consumption": round(meter_map[mid]["total"], 2),
            "avg_daily": round(meter_map[mid]["total"] / meter_map[mid]["days"], 2) if meter_map[mid]["days"] else 0,
            "days_collected": meter_map[mid]["days"],
        }
        for mid in meter_ids_page
    ]

    return {
        "summary": {
            "total_consumption": total_consumption,
            "avg_daily": avg_daily,
            "peak_day": peak,
            "days": len(daily_labels),
            "demo": demo,
        },
        "charts": {
            "daily_trend": {
                "labels": daily_labels,
                "series": {"consumption": daily_values},
            },
        },
        "items": items,
        "total": total,
    }


# ── 10. R-11 On-Demand Read History ──────────────────────────────────────


async def get_ondemand_history(
    db: AsyncSession,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    start, end = _parse_date_range(date_from, date_to)

    # Tasks of type "once" (on-demand)
    stmt = (
        select(TaskLog, Task)
        .join(Task, TaskLog.task_id == Task.id)
        .where(
            Task.task_type == "once",
            TaskLog.start_time >= datetime.datetime.combine(start, datetime.time.min),
            TaskLog.start_time <= datetime.datetime.combine(end, datetime.time.max),
        )
    )

    result = await db.execute(stmt.order_by(TaskLog.start_time.desc()))
    rows = result.all()

    demo = len(rows) == 0

    total = len(rows)
    success = sum(1 for log, _ in rows if log.status == "completed")
    failed = sum(1 for log, _ in rows if log.status == "failed")

    if demo:
        total, success, failed = 0, 0, 0

    success_rate = round(success / total * 100, 1) if total else 0
    success_rate = round(success / total * 100, 1) if total else 0

    # Paginate
    offset = (page - 1) * page_size
    page_rows = rows[offset : offset + page_size]
    items = [
        {
            "id": log.id,
            "task_id": task.id,
            "task_name": task.task_name,
            "start_time": _fmt_dt(log.start_time),
            "end_time": _fmt_dt(log.end_time),
            "duration_ms": log.duration_ms,
            "total_devices": log.total_devices,
            "success_devices": log.success_devices,
            "failed_devices": log.failed_devices,
            "status": log.status,
            "error_message": log.error_message,
        }
        for log, task in page_rows
    ]

    # 构建 daily_trend 图表数据
    daily_map: dict[str, int] = {}
    for log, _ in rows:
        day = _fmt_date(log.start_time.date()) if log.start_time else None
        if day:
            daily_map[day] = daily_map.get(day, 0) + 1

    # 按日期排序
    sorted_days = sorted(daily_map.keys())
    trend_labels = sorted_days[-14:] if len(sorted_days) > 14 else sorted_days  # 最多显示14天
    trend_reads = [daily_map.get(d, 0) for d in trend_labels]

    return {
        "summary": {
            "total_reads": total,
            "success": success,
            "failed": failed,
            "success_rate": success_rate,
            "demo": demo,
        },
        "charts": {
            "daily_trend": {
                "labels": trend_labels,
                "series": {"reads": trend_reads},
            },
        },
        "items": items,
        "total": total,
    }
