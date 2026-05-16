from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.auth import get_current_user
from app.core.database import AsyncSessionLocal as async_session
from app.core.response import success, fail
from app.models.meter import MeterBorrow

router = APIRouter(prefix="/borrows", tags=["borrows"])


@router.post("/{borrow_id}/approve")
async def approve_borrow(borrow_id: int, body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(MeterBorrow).where(MeterBorrow.id == borrow_id))
        borrow = result.scalar_one_or_none()
        if not borrow:
            return fail(code=10001, message="借出记录不存在", status=404)

        approved = body.get("approved", True)
        if approved:
            if borrow.approval_status == "pending_department":
                borrow.approval_status = "pending_lab"
            elif borrow.approval_status == "pending_lab":
                borrow.approval_status = "approved"
        else:
            borrow.approval_status = "rejected"

        await session.commit()
        return success({"id": borrow.id, "approval_status": borrow.approval_status})


@router.post("/{borrow_id}/return")
async def return_borrow(borrow_id: int, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(MeterBorrow).where(MeterBorrow.id == borrow_id))
        borrow = result.scalar_one_or_none()
        if not borrow:
            return fail(code=10001, message="借出记录不存在", status=404)

        borrow.actual_return_date = date.today()
        borrow.approval_status = "returned"
        await session.commit()
        return success({"id": borrow.id})
