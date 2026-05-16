from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import Permission, Role, RolePermission, User, UserRole

_refresh_tokens: dict[str, str] = {}


async def authenticate(db: AsyncSession, username: str, password: str) -> dict:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise BusinessException(code=401, message="用户名或密码错误")
    if not user.is_active:
        raise BusinessException(code=403, message="用户已被禁用")

    access_token = create_access_token({"sub": user.username, "id": user.id})
    refresh_token = create_refresh_token({"sub": user.username, "id": user.id})
    _refresh_tokens[user.username] = refresh_token

    roles = await _get_user_roles(db, user.id)

    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "roles": roles,
        "accessToken": access_token,
        "refreshToken": refresh_token,
    }


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> str:
    payload = decode_token(refresh_token)
    if payload is None:
        raise BusinessException(code=401, message="刷新令牌无效或已过期")

    username = payload.get("sub")
    stored = _refresh_tokens.get(username)
    if stored != refresh_token:
        raise BusinessException(code=401, message="刷新令牌不匹配")

    new_access = create_access_token({"sub": username, "id": payload.get("id")})
    new_refresh = create_refresh_token({"sub": username, "id": payload.get("id")})
    _refresh_tokens[username] = new_refresh

    return new_access


def revoke_refresh_token(username: str) -> None:
    _refresh_tokens.pop(username, None)


async def get_user_permission_codes(db: AsyncSession, user_id: int) -> list[str]:
    result = await db.execute(
        select(Role).join(UserRole).where(UserRole.user_id == user_id)
    )
    roles = result.scalars().all()
    if not roles:
        return []

    perm_codes: set[str] = set()
    for role in roles:
        rp_result = await db.execute(
            select(RolePermission.permission_id).where(RolePermission.role_id == role.id)
        )
        for (perm_id,) in rp_result.all():
            p_result = await db.execute(select(Permission).where(Permission.id == perm_id))
            perm = p_result.scalar_one_or_none()
            if perm:
                perm_codes.add(perm.code)

    return list(perm_codes)


async def _get_user_roles(db: AsyncSession, user_id: int) -> list[str]:
    result = await db.execute(
        select(Role).join(UserRole).where(UserRole.user_id == user_id)
    )
    return [r.code for r in result.scalars().all()]
