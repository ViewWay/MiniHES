import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from app.core.auth import get_current_user
from app.core.database import AsyncSessionLocal as async_session
from app.core.response import success, fail
from app.models.alarm import Alarm, AlarmRule

router = APIRouter(prefix="/alarms", tags=["alarms"])


@router.get("/stats")
async def alarm_stats():
    async with async_session() as session:
        total_result = await session.execute(select(func.count()).select_from(Alarm))
        total = total_result.scalar() or 0

        unhandled_result = await session.execute(
            select(func.count()).select_from(Alarm).where(Alarm.is_handled == False)
        )
        unhandled_count = unhandled_result.scalar() or 0

        critical_result = await session.execute(
            select(func.count()).select_from(Alarm).where(Alarm.severity == "critical")
        )
        critical_count = critical_result.scalar() or 0

        warning_result = await session.execute(
            select(func.count()).select_from(Alarm).where(Alarm.severity == "warning")
        )
        warning_count = warning_result.scalar() or 0

        info_result = await session.execute(
            select(func.count()).select_from(Alarm).where(Alarm.severity == "info")
        )
        info_count = info_result.scalar() or 0

        return success({
            "total": total,
            "unhandled_count": unhandled_count,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "active": unhandled_count,
        })


@router.get("")
async def list_alarms(
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    severity: str = Query(default=None),
    alarm_type: str = Query(default=None),
    is_handled: str = Query(default=None),
    start_date: str = Query(default=None),
    end_date: str = Query(default=None),
):
    async with async_session() as session:
        stmt = select(Alarm)
        count_stmt = select(func.count()).select_from(Alarm)

        if severity:
            stmt = stmt.where(Alarm.severity == severity)
            count_stmt = count_stmt.where(Alarm.severity == severity)
        if alarm_type:
            stmt = stmt.where(Alarm.alarm_type == alarm_type)
            count_stmt = count_stmt.where(Alarm.alarm_type == alarm_type)
        if is_handled is not None:
            handled = is_handled.lower() == "true"
            stmt = stmt.where(Alarm.is_handled == handled)
            count_stmt = count_stmt.where(Alarm.is_handled == handled)

        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.order_by(Alarm.id.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
        alarms = result.scalars().all()

        items = [_alarm_to_dict(a) for a in alarms]
        return success({"items": items, "total": total})


@router.get("/export")
async def export_alarms(
    severity: str = Query(default=None),
    alarm_type: str = Query(default=None),
    _=Depends(get_current_user),
):
    async with async_session() as session:
        stmt = select(Alarm).order_by(Alarm.id.desc())
        if severity:
            stmt = stmt.where(Alarm.severity == severity)
        if alarm_type:
            stmt = stmt.where(Alarm.alarm_type == alarm_type)
        result = await session.execute(stmt)
        alarms = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "设备ID", "告警类型", "严重程度", "告警信息", "是否已处理", "时间"])
    for a in alarms:
        writer.writerow([
            a.id, a.meter_id, a.alarm_type, a.severity, a.alarm_message,
            "是" if a.is_handled else "否",
            a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=alarms_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


@router.get("/{alarm_id}")
async def get_alarm(alarm_id: int):
    async with async_session() as session:
        result = await session.execute(select(Alarm).where(Alarm.id == alarm_id))
        a = result.scalar_one_or_none()
        if not a:
            return success(None)
        return success(_alarm_to_dict(a))


@router.post("/{alarm_id}/handle")
async def handle_alarm(alarm_id: int, body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(Alarm).where(Alarm.id == alarm_id))
        a = result.scalar_one_or_none()
        if not a:
            return success(None)
        a.is_handled = True
        a.handled_by = body.get("handled_by")
        a.handled_at = datetime.now(timezone.utc)
        await session.commit()
        return success({"success": True})


def _alarm_to_dict(a: Alarm) -> dict:
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
