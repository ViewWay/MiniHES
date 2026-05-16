from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.services.user_service import get_user_info

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/info")
async def get_user_info_endpoint(user: CurrentUser, db: DbSession = ...):
    data = await get_user_info(db, user.id)
    return success(data)
