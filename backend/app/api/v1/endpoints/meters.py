import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select

from app.core.auth import get_current_user
from app.core.database import AsyncSessionLocal as async_session
from app.core.response import success, fail
from app.models.meter import (
    Meter, MeterType, WireType,
    MeterStatusHistory, MeterAttachment, MeterBorrow, MeterRepair,
)

router = APIRouter(prefix="/meters", tags=["meters"])


@router.get("")
async def list_meters(
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    project_id: int = Query(default=None),
    status: str = Query(default=None),
    keyword: str = Query(default=None),
):
    async with async_session() as session:
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
            stmt = stmt.where(
                or_(Meter.meter_name.ilike(kw), Meter.serial_number.ilike(kw), Meter.manufacturer.ilike(kw))
            )
            count_stmt = count_stmt.where(
                or_(Meter.meter_name.ilike(kw), Meter.serial_number.ilike(kw), Meter.manufacturer.ilike(kw))
            )

        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        online_count_result = await session.execute(
            select(func.count()).select_from(Meter).where(Meter.current_status.in_(["online", "in_use"]))
        )
        online_count = online_count_result.scalar() or 0

        stmt = stmt.order_by(Meter.id).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
        meters = result.scalars().all()

        items = [_meter_to_dict(m) for m in meters]
        return success({"items": items, "total": total, "online_count": online_count})


@router.post("")
async def create_meter(body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        m = Meter(**body)
        session.add(m)
        await session.commit()
        await session.refresh(m)
        return success({"id": m.id, **_meter_to_dict(m)})


@router.get("/borrows")
async def list_borrows(
    meter_id: int = Query(default=None),
    status: str = Query(default=None),
):
    async with async_session() as session:
        stmt = select(MeterBorrow).order_by(MeterBorrow.id.desc())
        if meter_id:
            stmt = stmt.where(MeterBorrow.meter_id == meter_id)
        if status:
            stmt = stmt.where(MeterBorrow.approval_status == status)

        result = await session.execute(stmt)
        items = [
            {
                "id": b.id,
                "meter_id": b.meter_id,
                "borrower_id": b.borrower_id,
                "borrow_reason": b.borrow_reason,
                "expected_return_date": str(b.expected_return_date) if b.expected_return_date else None,
                "actual_return_date": str(b.actual_return_date) if b.actual_return_date else None,
                "approval_status": b.approval_status,
                "created_at": b.created_at.strftime("%Y-%m-%d %H:%M:%S") if b.created_at else "",
            }
            for b in result.scalars().all()
        ]
        return success({"items": items, "total": len(items)})


@router.post("/borrows")
async def create_borrow_request(body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        borrow = MeterBorrow(
            meter_id=body.get("meter_id"),
            borrower_id=body.get("borrower_id"),
            borrow_reason=body.get("borrow_reason", ""),
            expected_return_date=body.get("expected_return_date"),
            dept_approver_id=body.get("department_approver"),
            approval_status="pending_department",
        )
        session.add(borrow)
        await session.commit()
        return success({"id": borrow.id})


@router.get("/repairs")
async def list_repairs(
    meter_id: int = Query(default=None),
    status: str = Query(default=None),
    start_date: str = Query(default=None),
    end_date: str = Query(default=None),
):
    async with async_session() as session:
        stmt = select(MeterRepair).order_by(MeterRepair.id.desc())
        if meter_id:
            stmt = stmt.where(MeterRepair.meter_id == meter_id)
        if status:
            stmt = stmt.where(MeterRepair.status == status)

        result = await session.execute(stmt)
        items = [
            {
                "id": r.id,
                "meter_id": r.meter_id,
                "description": r.description,
                "cost": r.cost,
                "status": r.status,
                "repaired_by": r.repaired_by,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            }
            for r in result.scalars().all()
        ]
        return success({"items": items, "total": len(items)})


@router.post("/repairs")
async def create_repair(body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        repair = MeterRepair(
            meter_id=body.get("meter_id"),
            description=body.get("description", ""),
            cost=body.get("cost", 0),
        )
        session.add(repair)
        await session.commit()
        return success({"id": repair.id})


@router.get("/export")
async def export_meters(
    project_id: int = Query(default=None),
    status: str = Query(default=None),
    _=Depends(get_current_user),
):
    async with async_session() as session:
        stmt = select(Meter).order_by(Meter.id)
        if project_id:
            stmt = stmt.where(Meter.project_id == project_id)
        if status:
            stmt = stmt.where(Meter.current_status == status)
        result = await session.execute(stmt)
        meters = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "序列号", "名称", "类型ID", "项目ID", "制造商", "型号", "状态", "位置"])
    for m in meters:
        writer.writerow([m.id, m.serial_number, m.meter_name, m.meter_type_id, m.project_id, m.manufacturer, m.model, m.current_status, m.location])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=meters_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


@router.post("/import")
async def import_meters(body: dict, _=Depends(get_current_user)):
    return success({"success": True, "message": "导入功能待实现"})


@router.get("/{meter_id}")
async def get_meter(meter_id: int):
    async with async_session() as session:
        result = await session.execute(select(Meter).where(Meter.id == meter_id))
        m = result.scalar_one_or_none()
        if not m:
            return success(None)
        return success(_meter_to_dict(m))


@router.put("/{meter_id}")
async def update_meter(meter_id: int, body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(Meter).where(Meter.id == meter_id))
        m = result.scalar_one_or_none()
        if not m:
            return success(None)
        for key, value in body.items():
            if hasattr(m, key):
                setattr(m, key, value)
        await session.commit()
        return success(_meter_to_dict(m))


@router.post("/{meter_id}/status")
async def change_meter_status(meter_id: int, body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(Meter).where(Meter.id == meter_id))
        m = result.scalar_one_or_none()
        if not m:
            return success(None)
        history = MeterStatusHistory(
            meter_id=meter_id,
            old_status=m.current_status,
            new_status=body.get("status", ""),
            reason=body.get("reason", ""),
        )
        session.add(history)
        m.current_status = body.get("status", m.current_status)
        await session.commit()
        return success({"success": True})


@router.post("/{meter_id}/borrow")
async def borrow_meter(meter_id: int, body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        borrow = MeterBorrow(
            meter_id=meter_id,
            borrower_id=body.get("borrower_id"),
            borrow_reason=body.get("borrow_reason", ""),
            expected_return_date=body.get("expected_return_date"),
            dept_approver_id=body.get("department_approver"),
            approval_status="pending_department",
        )
        session.add(borrow)
        await session.commit()
        return success({"id": borrow.id})


@router.get("/{meter_id}/status-history")
async def get_status_history(meter_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(MeterStatusHistory).where(MeterStatusHistory.meter_id == meter_id).order_by(MeterStatusHistory.id)
        )
        items = [
            {
                "old_status": h.old_status,
                "new_status": h.new_status,
                "reason": h.reason,
                "created_at": h.created_at.strftime("%Y-%m-%d %H:%M:%S") if h.created_at else "",
            }
            for h in result.scalars().all()
        ]
        return success(items)


@router.put("/{meter_id}/communication")
async def update_communication(meter_id: int, body: dict, _=Depends(get_current_user)):
    return success({"success": True})


@router.get("/{meter_id}/attachments")
async def get_attachments(meter_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(MeterAttachment).where(MeterAttachment.meter_id == meter_id).order_by(MeterAttachment.id)
        )
        items = [
            {
                "id": a.id,
                "filename": a.filename,
                "size": a.size,
                "uploaded_by": a.uploaded_by,
                "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else "",
            }
            for a in result.scalars().all()
        ]
        return success(items)


@router.post("/{meter_id}/attachments")
async def upload_meter_attachment(meter_id: int, body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        attachment = MeterAttachment(
            meter_id=meter_id,
            filename=body.get("filename", ""),
            file_path=body.get("file_path", ""),
            size=body.get("size", 0),
            uploaded_by=body.get("uploaded_by"),
        )
        session.add(attachment)
        await session.commit()
        return success({"id": attachment.id})


def _meter_to_dict(m: Meter) -> dict:
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
        "factory_date": str(m.factory_date) if m.factory_date else "",
        "purchase_date": str(m.purchase_date) if m.purchase_date else "",
        "warranty_date": str(m.warranty_date) if m.warranty_date else "",
        "notes": m.notes,
    }
