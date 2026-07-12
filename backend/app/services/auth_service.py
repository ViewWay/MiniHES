import datetime
import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.auth import RefreshToken
from app.models.user import Permission, Role, RolePermission, User, UserRole

# 内存缓存：username -> refresh_token（快速校验路径）
_refresh_tokens: dict[str, str] = {}


def _hash_token(token: str) -> str:
    """SHA256 哈希 refresh_token，避免明文入库。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def authenticate(db: AsyncSession, username: str, password: str) -> dict:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise BusinessException(code=401, message="用户名或密码错误")
    if not user.is_active:
        raise BusinessException(code=403, message="用户已被禁用")

    access_token = create_access_token({"sub": user.username, "id": user.id})
    refresh_token = create_refresh_token({"sub": user.username, "id": user.id})
    # 内存缓存（快速路径）
    _refresh_tokens[user.username] = refresh_token
    # 持久化存储（带哈希）
    await _store_refresh_token(db, user.id, refresh_token)

    roles = await _get_user_roles(db, user.id)

    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "roles": roles,
        "accessToken": access_token,
        "refreshToken": refresh_token,
    }


async def _store_refresh_token(db: AsyncSession, user_id: int, token: str) -> None:
    """将 refresh token 的 SHA256 哈希写入数据库。

    如果 sys_refresh_token 表不存在（迁移未执行），降级为仅内存缓存，
    不影响登录流程。

    使用独立 session 写入，避免 flush 失败导致主事务 session 进入
    PendingRollback 状态。
    """
    import logging

    from app.core.database import AsyncSessionLocal

    logger = logging.getLogger(__name__)

    payload = decode_token(token)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    if payload and payload.get("exp"):
        expires_at = datetime.datetime.fromtimestamp(payload["exp"], tz=datetime.timezone.utc)

    try:
        async with AsyncSessionLocal() as session:
            db_token = RefreshToken(
                user_id=user_id,
                token_hash=_hash_token(token),
                expires_at=expires_at,
                revoked=False,
            )
            session.add(db_token)
            await session.commit()
    except Exception as e:
        logger.warning("refresh_token 持久化失败（降级为内存模式）: %s", e)


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> str:
    payload = decode_token(refresh_token)
    if payload is None:
        raise BusinessException(code=401, message="刷新令牌无效或已过期")

    username = payload.get("sub")
    token_hash = _hash_token(refresh_token)

    # 快速路径：内存缓存命中
    stored = _refresh_tokens.get(username)
    if stored != refresh_token:
        # 缓存未命中，回退到数据库校验
        try:
            result = await db.execute(
                select(RefreshToken)
                .where(RefreshToken.token_hash == token_hash, RefreshToken.revoked.is_(False))
                .order_by(RefreshToken.created_at.desc())
                .limit(1)
            )
            db_token = result.scalar_one_or_none()
            if db_token is None:
                raise BusinessException(code=401, message="刷新令牌无效或已撤销")
            if db_token.expires_at <= datetime.datetime.now(db_token.expires_at.tzinfo):
                raise BusinessException(code=401, message="刷新令牌已过期")
        except BusinessException:
            raise
        except Exception:
            # 表不存在或其他 DB 错误时，仅信任内存缓存
            if stored != refresh_token:
                raise BusinessException(code=401, message="刷新令牌不匹配")

    new_access = create_access_token({"sub": username, "id": payload.get("id")})
    new_refresh = create_refresh_token({"sub": username, "id": payload.get("id")})
    _refresh_tokens[username] = new_refresh
    await _store_refresh_token(db, payload.get("id"), new_refresh)

    return new_access


async def revoke_refresh_token(db: AsyncSession, username: str) -> None:
    """撤销用户所有持久化 refresh token 并清除内存缓存。"""
    _refresh_tokens.pop(username, None)

    try:
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.user_id.in_(select(User.id).where(User.username == username)))
        )
        for db_token in result.scalars().all():
            db_token.revoked = True
        await db.flush()
    except Exception:
        # 表不存在时仅清内存
        pass


async def request_password_reset(db: AsyncSession, email: str) -> str:
    """根据邮箱查找用户并生成密码重置令牌。

    用户不存在时返回空字符串而非抛错，避免泄露邮箱是否注册。
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        # 防枚举：静默返回，让端点给出一致响应
        return ""

    reset_token = create_access_token(
        {"sub": user.username, "id": user.id, "type": "password_reset"},
        expires_delta=datetime.timedelta(minutes=30),
    )
    return reset_token


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    """校验密码重置令牌并更新用户密码。"""
    payload = decode_token(token)
    if payload is None:
        raise BusinessException(code=401, message="密码重置令牌无效或已过期")
    if payload.get("type") != "password_reset":
        raise BusinessException(code=401, message="无效的密码重置令牌")

    user_id = payload.get("id")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise BusinessException(code=404, message="用户不存在")

    user.password_hash = get_password_hash(new_password)
    await db.flush()


async def get_user_permission_codes(db: AsyncSession, user_id: int) -> list[str]:
    """查用户权限码列表（单条 4 表 join，无 N+1）。

    Permission → RolePermission → Role → UserRole，按 user_id 过滤。
    """
    result = await db.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    return list(result.scalars().all())


async def _get_user_roles(db: AsyncSession, user_id: int) -> list[str]:
    """查用户角色码列表（向后兼容别名）。"""
    return await get_user_role_codes(db, user_id)


async def get_user_role_codes(db: AsyncSession, user_id: int) -> list[str]:
    """查用户角色码列表（单条 2 表 join）。供 RBAC super 豁免判断用。"""
    result = await db.execute(
        select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
    )
    return list(result.scalars().all())
