from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Permission, RolePermission, UserRole


def _perm_to_menu(p: Permission) -> dict:
    """Convert a Permission ORM object to a menu dict for API responses."""
    return {
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "type": p.type,
        "parent_id": p.parent_id,
        "path": p.path,
        "icon": p.icon,
        "sortOrder": p.sort_order,
        "status": 1 if p.status == "active" else 0,
        "createTime": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else None,
    }


async def list_menus(db: AsyncSession) -> list[dict]:
    """Return all permissions as menu items ordered by sort_order."""
    result = await db.execute(select(Permission).order_by(Permission.sort_order))
    return [_perm_to_menu(p) for p in result.scalars().all()]


async def check_name_exists(db: AsyncSession, name: str, id: int | None = None) -> bool:
    """Check if a permission name already exists, excluding a given id."""
    stmt = select(Permission).where(Permission.name == name)
    if id is not None:
        stmt = stmt.where(Permission.id != id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def check_path_exists(db: AsyncSession, path: str, id: int | None = None) -> bool:
    """Check if a permission path already exists, excluding a given id."""
    stmt = select(Permission).where(Permission.path == path)
    if id is not None:
        stmt = stmt.where(Permission.id != id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_user_menus(db: AsyncSession, user_id: int) -> list[dict]:
    """Return menu items for a user based on their role-permission assignments."""
    # Get role ids for the user
    role_result = await db.execute(
        select(UserRole.role_id).where(UserRole.user_id == user_id)
    )
    role_ids = [row[0] for row in role_result.all()]

    if not role_ids:
        return []

    # Get permission ids for those roles
    perm_result = await db.execute(
        select(RolePermission.permission_id).where(RolePermission.role_id.in_(role_ids))
    )
    perm_ids = [row[0] for row in perm_result.all()]

    if not perm_ids:
        return []

    # Get permission objects
    result = await db.execute(
        select(Permission)
        .where(Permission.id.in_(perm_ids), Permission.status == "active")
        .order_by(Permission.sort_order)
    )
    permissions = result.scalars().all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "path": p.path,
            "type": p.type,
            "icon": p.icon,
            "sort_order": p.sort_order,
            "parent_id": p.parent_id,
            "status": 1 if p.status == "active" else 0,
        }
        for p in permissions
    ]
