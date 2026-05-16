import csv
import io
from datetime import datetime

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.models.alarm import Alarm
from app.services import alarm_service

router = APIRouter(prefix="/alarms", tags=["alarms"])


@router.get("/stats")
async def alarm_stats(db: DbSession = ...):
    data = await alarm_service.get_alarm_stats(db)
    return success(data)


@router.get("")
async def list_alarms(
    db: DbSession = ...,
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    severity: str = Query(default=None),
    alarm_type: str = Query(default=None),
    is_handled: str = Query(default=None),
    start_date: str = Query(default=None),
    end_date: str = Query(default=None),
):
    data = await alarm_service.list_alarms(
        db, page=page, page_size=page_size,
        severity=severity, alarm_type=alarm_type, is_handled=is_handled,
    )
    return success(data)


@router.get("/export")
async def export_alarms(
    db: DbSession = ...,
    _user: CurrentUser = ...,
    severity: str = Query(default=None),
    alarm_type: str = Query(default=None),
):
    stmt = select(Alarm).order_by(Alarm.id.desc())
    if severity:
        stmt = stmt.where(Alarm.severity == severity)
    if alarm_type:
        stmt = stmt.where(Alarm.alarm_type == alarm_type)
    result = await db.execute(stmt)
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
async def get_alarm(alarm_id: int, db: DbSession = ...):
    data = await alarm_service.get_alarm(db, alarm_id)
    return success(data)


@router.post("/{alarm_id}/handle")
async def handle_alarm(alarm_id: int, body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    data = await alarm_service.handle_alarm(db, alarm_id, handled_by=body.get("handled_by"))
    return success(data)
