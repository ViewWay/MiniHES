import csv
import io
from datetime import datetime

from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import AuditLog


async def list_audit_logs(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    user_id: int | None = None,
    operation_type: str | None = None,
) -> dict:
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)

    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
        count_stmt = count_stmt.where(AuditLog.user_id == user_id)
    if operation_type:
        stmt = stmt.where(AuditLog.operation_type == operation_type)
        count_stmt = count_stmt.where(AuditLog.operation_type == operation_type)

    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(stmt.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size))
    items = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "operation_type": log.operation_type,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
        }
        for log in result.scalars().all()
    ]
    return {"items": items, "total": total}


async def export_audit_logs_csv(
    db: AsyncSession,
    *,
    user_id: int | None = None,
    operation_type: str | None = None,
) -> StreamingResponse:
    stmt = select(AuditLog).order_by(AuditLog.id.desc())
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if operation_type:
        stmt = stmt.where(AuditLog.operation_type == operation_type)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "用户", "操作类型", "资源类型", "资源ID", "IP地址", "时间"])
    for log in logs:
        writer.writerow(
            [
                log.id,
                log.username,
                log.operation_type,
                log.resource_type,
                log.resource_id,
                log.ip_address,
                log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
            ]
        )

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


async def create_audit_log(
    db: AsyncSession,
    *,
    user_id: int,
    username: str,
    operation_type: str,
    resource_type: str = "",
    resource_id: int = 0,
    ip_address: str = "",
) -> None:
    log = AuditLog(
        user_id=user_id,
        username=username,
        operation_type=operation_type,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
    )
    db.add(log)
