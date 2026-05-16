import csv
import io

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BusinessException
from app.models.meter import (
    Meter,
    MeterComm,
    MeterSnapshot,
    MeterStatusHistory,
)

# Legal status transitions: current_status -> set of allowed next statuses
STATUS_TRANSITIONS: dict[str, set[str]] = {
    "in_stock": {"in_use", "repair", "scrapped"},
    "in_use": {"in_stock", "repair", "scrapped"},
    "repair": {"in_stock", "scrapped"},
    "scrapped": set(),  # terminal state
}

VALID_STATUSES = {"in_stock", "in_use", "repair", "scrapped"}


def _meter_to_dict(m: Meter) -> dict:
    """Convert a Meter ORM object to a plain dict for API responses."""
    return {
        "id": m.id,
        "serial_number": m.serial_number,
        "meter_name": m.meter_name,
        "meter_type_id": m.meter_type_id,
        "project_id": m.project_id,
        "protocol": m.protocol,
        "line_type": m.line_type,
        "manufacturer": m.manufacturer,
        "model": m.model,
        "firmware_version": m.firmware_version,
        "hardware_version": m.hardware_version,
        "frame_number": m.frame_number,
        "location": m.location,
        "status": m.current_status,
        "factory_date": str(m.factory_date) if m.factory_date else None,
        "purchase_date": str(m.purchase_date) if m.purchase_date else None,
        "warranty_date": str(m.warranty_date) if m.warranty_date else None,
        "notes": m.notes,
        "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else None,
        "updated_at": m.updated_at.strftime("%Y-%m-%d %H:%M:%S") if m.updated_at else None,
    }


def _comm_to_dict(c: MeterComm | None) -> dict | None:
    if c is None:
        return None
    return {
        "id": c.id,
        "meter_id": c.meter_id,
        "protocol": c.protocol,
        "connection_type": c.connection_type,
        "host": c.host,
        "port": c.port,
        "device_address": c.device_address,
        "baud_rate": c.baud_rate,
        "parity": c.parity,
        "data_bits": c.data_bits,
        "stop_bits": c.stop_bits,
        "timeout": c.timeout,
        "retry_times": c.retry_times,
        "is_enabled": c.is_enabled,
    }


def _snapshot_to_dict(s: MeterSnapshot | None) -> dict | None:
    if s is None:
        return None
    return {
        "id": s.id,
        "meter_id": s.meter_id,
        "online_status": s.online_status,
        "last_comm_time": s.last_comm_time.strftime("%Y-%m-%d %H:%M:%S") if s.last_comm_time else None,
        "signal_strength": s.signal_strength,
        "firmware_version": s.firmware_version,
        "error_code": s.error_code,
    }


async def list_meters(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    project_id: int | None = None,
    status: str | None = None,
    keyword: str | None = None,
) -> dict:
    """Return paginated meter list with total and online_count."""
    stmt = select(Meter)
    count_stmt = select(func.count()).select_from(Meter)

    if project_id is not None:
        stmt = stmt.where(Meter.project_id == project_id)
        count_stmt = count_stmt.where(Meter.project_id == project_id)
    if status:
        stmt = stmt.where(Meter.current_status == status)
        count_stmt = count_stmt.where(Meter.current_status == status)
    if keyword:
        kw = f"%{keyword}%"
        cond = or_(
            Meter.meter_name.ilike(kw),
            Meter.serial_number.ilike(kw),
            Meter.manufacturer.ilike(kw),
        )
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    online_count_result = await db.execute(
        select(func.count()).select_from(Meter).where(Meter.current_status == "in_use")
    )
    online_count = online_count_result.scalar() or 0

    stmt = stmt.order_by(Meter.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    meters = result.scalars().all()

    items = [_meter_to_dict(m) for m in meters]
    return {"items": items, "total": total, "online_count": online_count}


async def get_meter(db: AsyncSession, meter_id: int) -> dict | None:
    """Return detailed meter info including comm and snapshot."""
    stmt = select(Meter).options(selectinload(Meter.comm), selectinload(Meter.snapshot)).where(Meter.id == meter_id)
    result = await db.execute(stmt)
    m = result.scalar_one_or_none()
    if not m:
        return None
    data = _meter_to_dict(m)
    data["comm"] = _comm_to_dict(m.comm)
    data["snapshot"] = _snapshot_to_dict(m.snapshot)
    return data


async def create_meter(db: AsyncSession, data: dict, user_id: int | None = None) -> dict:
    """Create a new meter record."""
    # Check serial_number uniqueness
    existing = await db.execute(select(Meter).where(Meter.serial_number == data.get("serial_number", "")))
    if existing.scalar_one_or_none():
        raise BusinessException(code=409, message="序列号已存在")

    if user_id:
        data["created_by"] = user_id
    meter = Meter(**data)
    db.add(meter)
    await db.flush()

    # Create default comm record
    comm = MeterComm(meter_id=meter.id)
    db.add(comm)
    await db.flush()

    return {"id": meter.id, **_meter_to_dict(meter)}


async def update_meter(db: AsyncSession, meter_id: int, data: dict) -> dict | None:
    """Update meter fields. Returns None if meter not found."""
    m = await db.get(Meter, meter_id)
    if not m:
        raise BusinessException(code=404, message="样机不存在")

    # If serial_number is being changed, check uniqueness
    new_sn = data.get("serial_number")
    if new_sn and new_sn != m.serial_number:
        existing = await db.execute(select(Meter).where(Meter.serial_number == new_sn))
        if existing.scalar_one_or_none():
            raise BusinessException(code=409, message="序列号已存在")

    for key, value in data.items():
        if value is not None and hasattr(m, key):
            setattr(m, key, value)
    return _meter_to_dict(m)


async def delete_meter(db: AsyncSession, meter_id: int) -> bool:
    """Delete a meter. Returns True if deleted, False if not found."""
    m = await db.get(Meter, meter_id)
    if not m:
        raise BusinessException(code=404, message="样机不存在")
    await db.delete(m)
    return True


async def change_status(
    db: AsyncSession,
    meter_id: int,
    new_status: str,
    reason: str = "",
    user_id: int | None = None,
) -> dict:
    """Change meter status with state machine validation."""
    if new_status not in VALID_STATUSES:
        raise BusinessException(code=400, message=f"无效的状态: {new_status}")

    m = await db.get(Meter, meter_id)
    if not m:
        raise BusinessException(code=404, message="样机不存在")

    allowed = STATUS_TRANSITIONS.get(m.current_status, set())
    if new_status not in allowed:
        raise BusinessException(
            code=400,
            message=f"不允许从 [{m.current_status}] 变更为 [{new_status}]",
        )

    history = MeterStatusHistory(
        meter_id=meter_id,
        old_status=m.current_status,
        new_status=new_status,
        reason=reason,
        changed_by=user_id,
    )
    db.add(history)
    m.current_status = new_status
    await db.flush()
    return {"success": True, "old_status": history.old_status, "new_status": new_status}


async def get_status_history(db: AsyncSession, meter_id: int) -> list[dict]:
    """Get status change history for a meter."""
    result = await db.execute(
        select(MeterStatusHistory).where(MeterStatusHistory.meter_id == meter_id).order_by(MeterStatusHistory.id.desc())
    )
    return [
        {
            "id": h.id,
            "old_status": h.old_status,
            "new_status": h.new_status,
            "reason": h.reason,
            "created_at": h.created_at.strftime("%Y-%m-%d %H:%M:%S") if h.created_at else "",
        }
        for h in result.scalars().all()
    ]


async def update_communication(db: AsyncSession, meter_id: int, data: dict) -> dict:
    """Update or create the comm config for a meter."""
    m = await db.get(Meter, meter_id)
    if not m:
        raise BusinessException(code=404, message="样机不存在")

    result = await db.execute(select(MeterComm).where(MeterComm.meter_id == meter_id))
    comm = result.scalar_one_or_none()

    if comm is None:
        data["meter_id"] = meter_id
        comm = MeterComm(**data)
        db.add(comm)
    else:
        for key, value in data.items():
            if value is not None and hasattr(comm, key):
                setattr(comm, key, value)

    await db.flush()
    return _comm_to_dict(comm)


async def export_csv(
    db: AsyncSession,
    *,
    project_id: int | None = None,
    status: str | None = None,
) -> str:
    """Export meters as CSV string."""
    stmt = select(Meter).order_by(Meter.id)
    if project_id:
        stmt = stmt.where(Meter.project_id == project_id)
    if status:
        stmt = stmt.where(Meter.current_status == status)
    result = await db.execute(stmt)
    meters = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "序列号", "名称", "类型ID", "项目ID", "制造商", "型号", "状态", "位置"])
    for m in meters:
        writer.writerow(
            [
                m.id,
                m.serial_number,
                m.meter_name,
                m.meter_type_id,
                m.project_id,
                m.manufacturer,
                m.model,
                m.current_status,
                m.location,
            ]
        )
    return output.getvalue()


async def import_csv(db: AsyncSession, csv_text: str, user_id: int | None = None) -> dict:
    """Import meters from CSV text. Returns count of created records."""
    reader = csv.DictReader(io.StringIO(csv_text))
    created = 0
    errors: list[str] = []

    for row_num, row in enumerate(reader, start=2):
        serial = row.get("序列号", "").strip()
        name = row.get("名称", "").strip()
        if not serial or not name:
            errors.append(f"第{row_num}行: 序列号和名称不能为空")
            continue

        existing = await db.execute(select(Meter).where(Meter.serial_number == serial))
        if existing.scalar_one_or_none():
            errors.append(f"第{row_num}行: 序列号 {serial} 已存在")
            continue

        meter = Meter(
            serial_number=serial,
            meter_name=name,
            manufacturer=row.get("制造商", ""),
            model=row.get("型号", ""),
            location=row.get("位置", ""),
            created_by=user_id,
        )
        db.add(meter)
        created += 1

    await db.flush()
    return {"created": created, "errors": errors}
