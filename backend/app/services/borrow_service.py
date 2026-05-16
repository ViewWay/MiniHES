from datetime import date
from datetime import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.meter import Meter, MeterBorrow

# Approval flow: current_status -> next status on approve
APPROVAL_FLOW: dict[str, str] = {
    "pending_department": "pending_lab",
    "pending_lab": "approved",
}

VALID_BORROW_STATUSES = {
    "pending_department",
    "pending_lab",
    "approved",
    "rejected",
    "returned",
}


def _borrow_to_dict(b: MeterBorrow) -> dict:
    """Convert a MeterBorrow ORM object to a plain dict."""
    return {
        "id": b.id,
        "meter_id": b.meter_id,
        "borrower_id": b.borrower_id,
        "borrow_reason": b.borrow_reason,
        "expected_return_date": str(b.expected_return_date) if b.expected_return_date else None,
        "actual_return_date": str(b.actual_return_date) if b.actual_return_date else None,
        "dept_approver_id": b.dept_approver_id,
        "lab_approver_id": b.lab_approver_id,
        "approval_status": b.approval_status,
        "created_at": b.created_at.strftime("%Y-%m-%d %H:%M:%S") if b.created_at else None,
        "updated_at": b.updated_at.strftime("%Y-%m-%d %H:%M:%S") if b.updated_at else None,
    }


async def list_borrows(
    db: AsyncSession,
    *,
    meter_id: int | None = None,
    status: str | None = None,
) -> dict:
    """List borrow records with optional filters."""
    stmt = select(MeterBorrow).order_by(MeterBorrow.id.desc())
    if meter_id:
        stmt = stmt.where(MeterBorrow.meter_id == meter_id)
    if status:
        stmt = stmt.where(MeterBorrow.approval_status == status)

    result = await db.execute(stmt)
    items = [_borrow_to_dict(b) for b in result.scalars().all()]
    return {"items": items, "total": len(items)}


async def create_borrow(
    db: AsyncSession,
    *,
    meter_id: int,
    borrower_id: int | None = None,
    borrow_reason: str = "",
    expected_return_date: str | None = None,
    dept_approver_id: int | None = None,
) -> dict:
    """Create a new borrow request. Meter must be in_stock or in_use."""
    # Verify meter exists and is available
    meter = await db.get(Meter, meter_id)
    if not meter:
        raise BusinessException(code=404, message="样机不存在")

    if meter.current_status not in ("in_stock", "in_use"):
        raise BusinessException(code=400, message="当前样机状态不可借出")

    # Parse date string to date object
    parsed_date = None
    if expected_return_date:
        if isinstance(expected_return_date, str):
            parsed_date = dt.strptime(expected_return_date, "%Y-%m-%d").date()
        elif isinstance(expected_return_date, date):
            parsed_date = expected_return_date

    borrow = MeterBorrow(
        meter_id=meter_id,
        borrower_id=borrower_id,
        borrow_reason=borrow_reason,
        expected_return_date=parsed_date,
        dept_approver_id=dept_approver_id,
        approval_status="pending_department",
    )
    db.add(borrow)
    await db.flush()
    return {"id": borrow.id, **_borrow_to_dict(borrow)}


async def approve_borrow(
    db: AsyncSession,
    borrow_id: int,
    approved: bool = True,
    approver_id: int | None = None,
) -> dict:
    """Approve or reject a borrow request, advancing through approval flow."""
    result = await db.execute(select(MeterBorrow).where(MeterBorrow.id == borrow_id))
    borrow = result.scalar_one_or_none()
    if not borrow:
        raise BusinessException(code=404, message="借用记录不存在")

    if borrow.approval_status not in ("pending_department", "pending_lab"):
        raise BusinessException(code=400, message="当前状态不可审批")

    if not approved:
        borrow.approval_status = "rejected"
    else:
        next_status = APPROVAL_FLOW.get(borrow.approval_status)
        if not next_status:
            raise BusinessException(code=400, message="无下一步审批状态")
        borrow.approval_status = next_status

        # Track the approver
        if borrow.approval_status == "pending_lab":
            borrow.dept_approver_id = approver_id or borrow.dept_approver_id
        elif borrow.approval_status == "approved":
            borrow.lab_approver_id = approver_id

    await db.flush()
    return {"id": borrow.id, "approval_status": borrow.approval_status}


async def return_borrow(
    db: AsyncSession,
    borrow_id: int,
) -> dict:
    """Mark a borrow as returned."""
    result = await db.execute(select(MeterBorrow).where(MeterBorrow.id == borrow_id))
    borrow = result.scalar_one_or_none()
    if not borrow:
        raise BusinessException(code=404, message="借用记录不存在")

    if borrow.approval_status != "approved":
        raise BusinessException(code=400, message="仅已批准的借用可归还")

    borrow.actual_return_date = date.today()
    borrow.approval_status = "returned"
    await db.flush()
    return {"id": borrow.id, "approval_status": "returned"}
