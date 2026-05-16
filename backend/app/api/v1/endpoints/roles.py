from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select

from app.core.auth import get_current_user
from app.core.database import AsyncSessionLocal as async_session
from app.core.response import success
from app.models.user import Role, RolePermission, UserRole

router = APIRouter(prefix="/system/role", tags=["role"])


@router.get("/list")
async def list_roles(
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    _=Depends(get_current_user),
):
    async with async_session() as session:
        stmt = select(Role)
        if name:
            stmt = stmt.where(Role.name.ilike(f"%{name}%"))
        if status:
            stmt = stmt.where(Role.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Role.sort_order).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
        roles = result.scalars().all()

        items = []
        for r in roles:
            user_count = (
                await session.execute(
                    select(func.count()).select_from(UserRole).where(UserRole.role_id == r.id)
                )
            ).scalar() or 0

            perm_ids = [
                p[0]
                for p in (
                    await session.execute(
                        select(RolePermission.permission_id).where(RolePermission.role_id == r.id)
                    )
                ).all()
            ]

            items.append({
                "id": r.id,
                "name": r.name,
                "code": r.code,
                "description": r.description,
                "sortOrder": r.sort_order,
                "status": r.status,
                "permissions": perm_ids,
                "userCount": user_count,
                "remark": r.description,
                "createTime": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            })
        return success({"items": items, "total": total})
