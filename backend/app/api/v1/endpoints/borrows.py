from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.schemas.meter import BorrowApproval
from app.services import borrow_service

router = APIRouter(prefix="/borrows", tags=["borrows"])


@router.post("/{borrow_id}/approve")
async def approve_borrow(
    db: DbSession,
    borrow_id: int,
    body: BorrowApproval,
    user: CurrentUser,
):
    data = await borrow_service.approve_borrow(
        db,
        borrow_id=borrow_id,
        approved=body.approved,
        approver_id=user.id,
    )
    return success(data)


@router.post("/{borrow_id}/return")
async def return_borrow(db: DbSession, borrow_id: int, _user: CurrentUser):
    data = await borrow_service.return_borrow(db, borrow_id=borrow_id)
    return success(data)
