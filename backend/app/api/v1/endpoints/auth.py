from fastapi import APIRouter, Cookie, Response

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import BusinessException
from app.core.response import success
from app.schemas.auth import LoginRequest
from app.services.auth_service import (
    authenticate,
    get_user_permission_codes,
    refresh_access_token,
    revoke_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest, response: Response, db: DbSession):
    result = await authenticate(db, body.username, body.password)
    refresh_token = result.pop("refreshToken")
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=7 * 24 * 3600,
        samesite="lax",
    )
    return success(result)


@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: DbSession = ...,
):
    if not refresh_token:
        raise BusinessException(code=401, message="缺少刷新令牌")
    new_access = await refresh_access_token(db, refresh_token)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=7 * 24 * 3600,
        samesite="lax",
    )
    return success(new_access)


@router.post("/logout")
async def logout(response: Response, user: CurrentUser):
    revoke_refresh_token(user.username)
    response.delete_cookie("refresh_token")
    return success(None)


@router.get("/codes")
async def get_access_codes(user: CurrentUser, db: DbSession):
    codes = await get_user_permission_codes(db, user.id)
    return success(codes)
