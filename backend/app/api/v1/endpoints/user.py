from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.auth import get_current_user
from app.core.database import AsyncSessionLocal as async_session
from app.core.response import success
from app.models.user import User, UserRole, Role, RolePermission

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/info")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    username = current_user.get("sub")
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        if not user:
            return success(None)

        role_result = await session.execute(
            select(Role).join(UserRole).where(UserRole.user_id == user.id)
        )
        roles = role_result.scalars().all()

        perm_ids = []
        for r in roles:
            rp_result = await session.execute(
                select(RolePermission.permission_id).where(RolePermission.role_id == r.id)
            )
            perm_ids.extend(p[0] for p in rp_result.all())

        return success({
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "avatar": user.avatar,
            "roles": [r.code for r in roles],
            "roleIds": [r.id for r in roles],
            "permissions": perm_ids,
        })
