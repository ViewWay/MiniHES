import io
from datetime import datetime

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.schemas.meter import (
    AttachmentUpload,
    BorrowCreate,
    MeterCommUpdate,
    MeterCreate,
    MeterStatusChange,
    MeterUpdate,
    RepairCreate,
    RepairUpdate,
)
from app.services import borrow_service, meter_service, repair_service, upload_service

router = APIRouter(prefix="/meters", tags=["meters"])


# ---------- Meter CRUD ----------


@router.get("")
async def list_meters(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    project_id: int = Query(default=None),
    status: str = Query(default=None),
    keyword: str = Query(default=None),
):
    data = await meter_service.list_meters(
        db,
        page=page,
        page_size=page_size,
        project_id=project_id,
        status=status,
        keyword=keyword,
    )
    return success(data)


@router.post("")
async def create_meter(db: DbSession, body: MeterCreate, user: CurrentUser):
    data = await meter_service.create_meter(db, body.model_dump(exclude_unset=True), user_id=user.id)
    return success(data)


@router.get("/export")
async def export_meters(
    db: DbSession,
    _user: CurrentUser,
    project_id: int = Query(default=None),
    status: str = Query(default=None),
):
    csv_text = await meter_service.export_csv(db, project_id=project_id, status=status)
    return StreamingResponse(
        io.BytesIO(csv_text.encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=meters_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


@router.post("/import")
async def import_meters(db: DbSession, body: dict, _user: CurrentUser):
    csv_text = body.get("csv_text", "")
    if not csv_text:
        from app.core.exceptions import BusinessException

        raise BusinessException(code=400, message="csv_text 不能为空")
    data = await meter_service.import_csv(db, csv_text=csv_text, user_id=_user.id)
    return success(data)


@router.get("/borrows")
async def list_borrows(
    db: DbSession,
    meter_id: int = Query(default=None),
    status: str = Query(default=None),
):
    data = await borrow_service.list_borrows(db, meter_id=meter_id, status=status)
    return success(data)


@router.post("/borrows")
async def create_borrow_request(db: DbSession, body: BorrowCreate, user: CurrentUser):
    data = await borrow_service.create_borrow(
        db,
        meter_id=body.meter_id,
        borrower_id=user.id,
        borrow_reason=body.borrow_reason,
        expected_return_date=body.expected_return_date,
        dept_approver_id=body.dept_approver_id,
    )
    return success(data)


@router.get("/repairs")
async def list_repairs(
    db: DbSession,
    meter_id: int = Query(default=None),
    status: str = Query(default=None),
):
    data = await repair_service.list_repairs(db, meter_id=meter_id, status=status)
    return success(data)


@router.post("/repairs")
async def create_repair(db: DbSession, body: RepairCreate, user: CurrentUser):
    data = await repair_service.create_repair(
        db,
        meter_id=body.meter_id,
        description=body.description,
        cost=body.cost,
        user_id=user.id,
    )
    return success(data)


@router.put("/repairs/{repair_id}")
async def update_repair(db: DbSession, repair_id: int, body: RepairUpdate, _user: CurrentUser):
    data = await repair_service.update_repair(
        db,
        repair_id,
        description=body.description,
        cost=body.cost,
        status=body.status,
    )
    return success(data)


@router.get("/{meter_id}")
async def get_meter(db: DbSession, meter_id: int):
    data = await meter_service.get_meter(db, meter_id)
    if data is None:
        return success(None)
    return success(data)


@router.put("/{meter_id}")
async def update_meter(db: DbSession, meter_id: int, body: MeterUpdate, _user: CurrentUser):
    data = await meter_service.update_meter(db, meter_id, body.model_dump(exclude_none=True))
    return success(data)


@router.delete("/{meter_id}")
async def delete_meter(db: DbSession, meter_id: int, _user: CurrentUser):
    await meter_service.delete_meter(db, meter_id)
    return success({"deleted": True})


@router.post("/{meter_id}/status")
async def change_meter_status(db: DbSession, meter_id: int, body: MeterStatusChange, user: CurrentUser):
    data = await meter_service.change_status(db, meter_id, body.status, body.reason, user_id=user.id)
    return success(data)


@router.post("/{meter_id}/borrow")
async def borrow_meter(db: DbSession, meter_id: int, body: BorrowCreate, user: CurrentUser):
    data = await borrow_service.create_borrow(
        db,
        meter_id=meter_id,
        borrower_id=user.id,
        borrow_reason=body.borrow_reason,
        expected_return_date=body.expected_return_date,
        dept_approver_id=body.dept_approver_id,
    )
    return success(data)


@router.get("/{meter_id}/status-history")
async def get_status_history(db: DbSession, meter_id: int):
    data = await meter_service.get_status_history(db, meter_id)
    return success(data)


@router.put("/{meter_id}/communication")
async def update_communication(db: DbSession, meter_id: int, body: MeterCommUpdate, _user: CurrentUser):
    data = await meter_service.update_communication(db, meter_id, body.model_dump(exclude_none=True))
    return success(data)


@router.get("/{meter_id}/attachments")
async def get_attachments(db: DbSession, meter_id: int):
    data = await upload_service.list_attachments(db, meter_id)
    return success(data)


@router.post("/{meter_id}/attachments")
async def upload_meter_attachment(db: DbSession, meter_id: int, body: AttachmentUpload, user: CurrentUser):
    data = await upload_service.upload_file(
        db,
        meter_id=meter_id,
        filename=body.filename,
        file_path=body.file_path,
        size=body.size,
        uploaded_by=user.id,
    )
    return success(data)


@router.delete("/{meter_id}/attachments/{attachment_id}")
async def delete_attachment(db: DbSession, meter_id: int, attachment_id: int, _user: CurrentUser):
    await upload_service.delete_attachment(db, attachment_id)
    return success({"deleted": True})
