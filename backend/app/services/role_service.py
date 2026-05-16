from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.user import Permission, Role, RolePermission, UserRole


async def list_roles(db: AsyncSession) -> dict:
    result = await db.execute(select(Role).order_by(Role.id))
    roles = result.scalars().all()
    items = []
    for r in roles:
        count_r = await db.execute(select(func.count()).select_from(UserRole).where(UserRole.role_id == r.id))
        user_count = count_r.scalar() or 0

        perm_r = await db.execute(select(RolePermission.permission_id).where(RolePermission.role_id == r.id))
        permission_ids = [p[0] for p in perm_r.all()]

        items.append({
            "id": r.id, "name": r.name, "code": r.code,
            "description": r.description, "sort_order": r.sort_order,
            "permission_ids": permission_ids, "user_count": user_count,
        })
    return {"items": items, "total": len(items)}


async def create_role(db: AsyncSession, data: dict) -> int:
    existing = await db.execute(select(Role).where(Role.code == data["code"]))
    if existing.scalar_one_or_none():
        raise BusinessException(code=409, message="角色编码已存在")

    perm_ids = data.pop("permission_ids", [])
    role = Role(**data)
    db.add(role)
    await db.flush()

    for pid in perm_ids:
        db.add(RolePermission(role_id=role.id, permission_id=pid))
    return role.id


async def update_role(db: AsyncSession, role_id: int, data: dict) -> None:
    role = await db.get(Role, role_id)
    if not role:
        raise BusinessException(code=404, message="角色不存在")

    perm_ids = data.pop("permission_ids", None)
    for key, value in data.items():
        if hasattr(role, key) and value is not None:
            setattr(role, key, value)

    if perm_ids is not None:
        await db.execute(RolePermission.__table__.delete().where(RolePermission.role_id == role_id))
        for pid in perm_ids:
            db.add(RolePermission(role_id=role_id, permission_id=pid))


async def delete_role(db: AsyncSession, role_id: int) -> None:
    role = await db.get(Role, role_id)
    if not role:
        raise BusinessException(code=404, message="角色不存在")

    count_r = await db.execute(select(func.count()).select_from(UserRole).where(UserRole.role_id == role_id))
    if (count_r.scalar() or 0) > 0:
        raise BusinessException(code=400, message="角色下存在用户，无法删除")

    await db.execute(RolePermission.__table__.delete().where(RolePermission.role_id == role_id))
    await db.delete(role)


async def get_permission_tree(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Permission).order_by(Permission.sort_order))
    return [
        {
            "id": p.id, "name": p.name, "code": p.code, "type": p.type,
            "parent_id": p.parent_id, "path": p.path, "icon": p.icon,
            "sort_order": p.sort_order, "status": p.status,
        }
        for p in result.scalars().all()
    ]
