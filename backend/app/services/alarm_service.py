from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.alarm import Alarm, AlarmRule


def _alarm_to_dict(a: Alarm) -> dict:
    """Convert an Alarm ORM object to a plain dict for API responses."""
    return {
        "id": a.id,
        "meter_id": a.meter_id,
        "rule_id": a.rule_id,
        "alarm_type": a.alarm_type,
        "severity": a.severity,
        "alarm_message": a.alarm_message,
        "alarm_value": float(a.alarm_value) if a.alarm_value is not None else None,
        "threshold_value": float(a.threshold_value) if a.threshold_value is not None else None,
        "is_handled": a.is_handled,
        "handled_by": a.handled_by,
        "handled_at": a.handled_at.strftime("%Y-%m-%d %H:%M:%S") if a.handled_at else None,
        "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else "",
    }


def _alarm_rule_to_dict(r: AlarmRule) -> dict:
    """Convert an AlarmRule ORM object to a plain dict for API responses."""
    return {
        "id": r.id,
        "rule_name": r.rule_name,
        "rule_type": r.rule_type,
        "point_code": r.point_code,
        "condition_config": r.condition_config,
        "severity": r.severity,
        "is_enabled": r.is_enabled,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
        "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else "",
    }


async def list_alarms(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    severity: str | None = None,
    alarm_type: str | None = None,
    is_handled: bool | None = None,
) -> dict:
    """Return paginated alarm list with total."""
    stmt = select(Alarm)
    count_stmt = select(func.count()).select_from(Alarm)

    if severity:
        stmt = stmt.where(Alarm.severity == severity)
        count_stmt = count_stmt.where(Alarm.severity == severity)
    if alarm_type:
        stmt = stmt.where(Alarm.alarm_type == alarm_type)
        count_stmt = count_stmt.where(Alarm.alarm_type == alarm_type)
    if is_handled is not None:
        stmt = stmt.where(Alarm.is_handled == is_handled)
        count_stmt = count_stmt.where(Alarm.is_handled == is_handled)

    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(stmt.order_by(Alarm.id.desc()).offset((page - 1) * page_size).limit(page_size))
    items = [_alarm_to_dict(a) for a in result.scalars().all()]
    return {"items": items, "total": total}


async def get_alarm_stats(db: AsyncSession) -> dict:
    """Return alarm statistics: total, unhandled, by severity, active count."""
    total_result = await db.execute(select(func.count()).select_from(Alarm))
    total = total_result.scalar() or 0

    unhandled_result = await db.execute(
        select(func.count()).select_from(Alarm).where(Alarm.is_handled == False)  # noqa: E712
    )
    unhandled_count = unhandled_result.scalar() or 0

    critical_result = await db.execute(select(func.count()).select_from(Alarm).where(Alarm.severity == "critical"))
    critical_count = critical_result.scalar() or 0

    warning_result = await db.execute(select(func.count()).select_from(Alarm).where(Alarm.severity == "warning"))
    warning_count = warning_result.scalar() or 0

    info_result = await db.execute(select(func.count()).select_from(Alarm).where(Alarm.severity == "info"))
    info_count = info_result.scalar() or 0

    active_result = await db.execute(
        select(func.count())
        .select_from(Alarm)
        .where(
            Alarm.is_handled == False,  # noqa: E712
            Alarm.severity.in_(["critical", "warning"]),
        )
    )
    active = active_result.scalar() or 0

    return {
        "total": total,
        "unhandled_count": unhandled_count,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "active": active,
    }


async def get_alarm(db: AsyncSession, alarm_id: int) -> dict | None:
    """Return a single alarm by id, or None if not found."""
    a = await db.get(Alarm, alarm_id)
    if not a:
        return None
    return _alarm_to_dict(a)


async def handle_alarm(db: AsyncSession, alarm_id: int, handled_by: int | None = None) -> dict:
    """Mark an alarm as handled."""
    from datetime import datetime, timezone

    a = await db.get(Alarm, alarm_id)
    if not a:
        raise BusinessException(code=404, message="告警记录不存在")

    a.is_handled = True
    a.handled_by = handled_by
    a.handled_at = datetime.now(timezone.utc)

    return _alarm_to_dict(a)


async def list_alarm_rules(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    rule_type: str | None = None,
) -> dict:
    """Return paginated alarm rule list with total."""
    stmt = select(AlarmRule)
    count_stmt = select(func.count()).select_from(AlarmRule)

    if rule_type:
        stmt = stmt.where(AlarmRule.rule_type == rule_type)
        count_stmt = count_stmt.where(AlarmRule.rule_type == rule_type)

    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(stmt.order_by(AlarmRule.id).offset((page - 1) * page_size).limit(page_size))
    items = [_alarm_rule_to_dict(r) for r in result.scalars().all()]
    return {"items": items, "total": total}


async def create_alarm_rule(db: AsyncSession, data: dict) -> int:
    """Create an alarm rule and return its id."""
    rule = AlarmRule(**data)
    db.add(rule)
    await db.flush()
    return rule.id


async def update_alarm_rule(db: AsyncSession, rule_id: int, data: dict) -> None:
    """Update an alarm rule. Raises 404 if not found."""
    r = await db.get(AlarmRule, rule_id)
    if not r:
        raise BusinessException(code=404, message="告警规则不存在")
    for key, value in data.items():
        if hasattr(r, key):
            setattr(r, key, value)


async def delete_alarm_rule(db: AsyncSession, rule_id: int) -> None:
    """Delete an alarm rule. Raises 404 if not found."""
    r = await db.get(AlarmRule, rule_id)
    if not r:
        raise BusinessException(code=404, message="告警规则不存在")
    await db.delete(r)


async def export_alarms_csv(
    db: AsyncSession,
    *,
    severity: str | None = None,
    alarm_type: str | None = None,
) -> list[dict]:
    """Return alarms for CSV export."""
    stmt = select(Alarm).order_by(Alarm.id.desc())
    if severity:
        stmt = stmt.where(Alarm.severity == severity)
    if alarm_type:
        stmt = stmt.where(Alarm.alarm_type == alarm_type)
    result = await db.execute(stmt)
    return [_alarm_to_dict(a) for a in result.scalars().all()]
