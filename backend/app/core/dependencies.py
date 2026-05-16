from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BusinessException
from app.core.security import decode_token
from app.models.user import User

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
