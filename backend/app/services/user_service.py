from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.core.security import get_password_hash
from app.models.user import Role, RolePermission, User, UserRole


async def list_users(
    db: AsyncSession, *, page: int = 1, page_size: int = 20,
    keyword: str | None = None, role: str | None = None,
) -> dict:
    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)

    if keyword:
        kw = f"%{keyword}%"
        cond = or_(User.name.ilike(kw), User.username.ilike(kw))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    if role:
        stmt = stmt.join(UserRole).join(Role).where(Role.code == role)
        count_stmt = count_stmt.join(UserRole).join(Role).where(Role.code == role)

    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(stmt.order_by(User.id).offset((page - 1) * page_size).limit(page_size))
    users = result.scalars().all()

    items = []
    for u in users:
        r_result = await db.execute(select(Role).join(UserRole).where(UserRole.user_id == u.id))
        roles = r_result.scalars().all()
        items.append({
            "id": u.id, "username": u.username, "name": u.name,
            "email": u.email, "phone": u.phone, "avatar": u.avatar,
            "department_id": u.department_id,
            "role_ids": [r.id for r in roles],
            "roles": [r.code for r in roles],
            "status": "active" if u.is_active else "inactive",
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else "",
        })
    return {"items": items, "total": total}


async def create_user(db: AsyncSession, data: dict) -> int:
    existing = await db.execute(select(User).where(User.username == data["username"]))
    if existing.scalar_one_or_none():
        raise BusinessException(code=409, message="用户名已存在")

    role_ids = data.pop("role_ids", [])
    password = data.pop("password", "123456")
    data["password_hash"] = get_password_hash(password)
    data.pop("is_active", None)  # Use default

    user = User(**data)
    db.add(user)
    await db.flush()

    for rid in role_ids:
        db.add(UserRole(user_id=user.id, role_id=rid))
    return user.id


async def update_user(db: AsyncSession, user_id: int, data: dict) -> None:
    user = await db.get(User, user_id)
    if not user:
        raise BusinessException(code=404, message="用户不存在")

    role_ids = data.pop("role_ids", None)
    password = data.pop("password", None)

    for key, value in data.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    if password:
        user.password_hash = get_password_hash(password)

    if role_ids is not None:
        await db.execute(UserRole.__table__.delete().where(UserRole.user_id == user_id))
        for rid in role_ids:
            db.add(UserRole(user_id=user_id, role_id=rid))


async def delete_user(db: AsyncSession, user_id: int) -> None:
    user = await db.get(User, user_id)
    if not user:
        raise BusinessException(code=404, message="用户不存在")
    await db.execute(UserRole.__table__.delete().where(UserRole.user_id == user_id))
    await db.delete(user)


async def reset_password(db: AsyncSession, user_id: int) -> None:
    user = await db.get(User, user_id)
    if not user:
        raise BusinessException(code=404, message="用户不存在")
    user.password_hash = get_password_hash("123456")


async def get_user_info(db: AsyncSession, user_id: int) -> dict:
    """Return user info with roles and permission ids."""
    user = await db.get(User, user_id)
    if not user:
        raise BusinessException(code=404, message="用户不存在")

    # Query roles via UserRole join
    role_result = await db.execute(
        select(Role).join(UserRole).where(UserRole.user_id == user_id)
    )
    roles = role_result.scalars().all()

    role_ids = [r.id for r in roles]

    # Query permission ids via RolePermission
    perm_result = await db.execute(
        select(RolePermission.permission_id).where(RolePermission.role_id.in_(role_ids))
    )
    permission_ids = [row[0] for row in perm_result.all()] if role_ids else []

    return {
        "id": user.id,
        "username": user.username,
        "realName": user.name,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "avatar": user.avatar,
        "roles": [r.code for r in roles],
        "roleIds": role_ids,
        "permissions": permission_ids,
    }
