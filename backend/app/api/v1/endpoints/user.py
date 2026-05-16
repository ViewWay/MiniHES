from fastapi import APIRouter
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.models.user import Role, RolePermission, UserRole

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/info")
async def get_user_info(user: CurrentUser, db: DbSession = ...):
    role_result = await db.execute(
        select(Role).join(UserRole).where(UserRole.user_id == user.id)
    )
    roles = role_result.scalars().all()

    perm_ids = []
    for r in roles:
        rp_result = await db.execute(
            select(RolePermission.permission_id).where(RolePermission.role_id == r.id)
        )
        perm_ids.extend(p[0] for p in rp_result.all())

    return success({
        "id": user.id,
        "username": user.username,
        "realName": user.name,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "avatar": user.avatar,
        "roles": [r.code for r in roles],
        "roleIds": [r.id for r in roles],
        "permissions": perm_ids,
    })
