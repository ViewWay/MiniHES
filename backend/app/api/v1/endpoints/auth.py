from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel, Field

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import BusinessException
from app.core.response import success
from app.schemas.auth import LoginRequest
from app.services.auth_service import (
    authenticate,
    get_user_permission_codes,
    refresh_access_token,
    request_password_reset,
    reset_password,
    revoke_refresh_token,
)
from app.services.email_service import send_password_reset_email

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
async def logout(response: Response, user: CurrentUser, db: DbSession):
    await revoke_refresh_token(db, user.username)
    response.delete_cookie("refresh_token")
    return success(None)


@router.get("/codes")
async def get_access_codes(user: CurrentUser, db: DbSession):
    codes = await get_user_permission_codes(db, user.id)
    return success(codes)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="注册邮箱")


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: DbSession):
    """请求密码重置。用户不存在时静默成功，避免邮箱枚举。"""
    reset_token = await request_password_reset(db, body.email)
    if reset_token:
        # 有匹配用户时发送邮件（失败仅记日志，不影响响应）
        await send_password_reset_email(body.email, reset_token, username=body.email)
    return success(None, message="如该邮箱已注册，重置邮件已发送")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="密码重置令牌")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")


@router.post("/reset-password")
async def reset_password_endpoint(body: ResetPasswordRequest, db: DbSession):
    await reset_password(db, body.token, body.new_password)
    return success(None, message="密码重置成功")
