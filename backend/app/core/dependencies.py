from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BusinessException
from app.core.mongo import get_mongo
from app.core.security import decode_token
from app.models.user import User
from app.services.auth_service import get_user_permission_codes, get_user_role_codes

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise BusinessException(code=401, message="登录已过期，请重新登录")
    user_id = payload.get("id")
    if not user_id:
        raise BusinessException(code=401, message="无效的认证信息")
    user = await db.get(User, user_id)
    if user is None:
        raise BusinessException(code=401, message="用户不存在")
    if not user.is_active:
        raise BusinessException(code=403, message="用户已被禁用")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
MongoDb = Annotated[AsyncIOMotorDatabase, Depends(get_mongo)]


def require_permission(*permission_codes: str):
    """菜单级权限校验依赖工厂。

    用法：
        # 单接口
        def handler(db: DbSession, user: CurrentUser, _=Depends(require_permission("devices"))): ...
        # 批量（推荐，在 api.py 的 include_router 上挂）
        api_router.include_router(meters.router, dependencies=[Depends(require_permission("devices"))])

    super 角色豁免（拥有所有权限）。权限不足抛 BusinessException(code=403)。
    """

    async def _check_permission(
        user: CurrentUser,
        db: DbSession,
    ):
        role_codes = await get_user_role_codes(db, user.id)
        if "super" in role_codes:
            return  # 超管豁免
        user_perms = set(await get_user_permission_codes(db, user.id))
        if not user_perms.intersection(permission_codes):
            raise BusinessException(
                code=403,
                message=f"权限不足，需要以下权限之一: {', '.join(permission_codes)}",
            )

    return _check_permission
