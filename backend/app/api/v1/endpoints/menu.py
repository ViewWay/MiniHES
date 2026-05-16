from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.services.menu_service import get_user_menus

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("/all")
async def get_all_menus(user: CurrentUser, db: DbSession = ...):
    items = await get_user_menus(db, user.id)
    return success(items)
