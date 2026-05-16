from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.auth import get_current_user
from app.core.database import AsyncSessionLocal as async_session
from app.core.response import success
from app.models.user import Permission, RolePermission, UserRole, User

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("/all")
async def get_all_menus(current_user: dict = Depends(get_current_user)):
    username = current_user.get("sub")
    async with async_session() as session:
        u_result = await session.execute(
            select(User).where(User.username == username)
        )
        user = u_result.scalar_one_or_none()
        if not user:
            return success([])

        role_ids_result = await session.execute(
            select(UserRole.role_id).where(UserRole.user_id == user.id)
        )
        role_ids = [r[0] for r in role_ids_result.all()]

        perm_ids = set()
        for rid in role_ids:
            rp_result = await session.execute(
                select(RolePermission.permission_id).where(RolePermission.role_id == rid)
            )
            for (pid,) in rp_result.all():
                perm_ids.add(pid)

        perm_result = await session.execute(
            select(Permission).order_by(Permission.sort_order)
        )
        perms = perm_result.scalars().all()

        items = [
            {
                "id": p.id,
                "name": p.name,
                "path": p.path,
                "type": p.type,
                "icon": p.icon,
                "sort_order": p.sort_order,
                "parent_id": p.parent_id,
                "status": p.status,
            }
            for p in perms
            if p.id in perm_ids
        ]
        return success(items)
