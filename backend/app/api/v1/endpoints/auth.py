from fastapi import APIRouter, HTTPException, Response, Cookie, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.core.auth import get_current_user
from app.core.response import success, error
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.database import AsyncSessionLocal as async_session
from app.models.user import User, UserRole, Role, RolePermission, Permission

router = APIRouter(prefix="/auth", tags=["auth"])

_refresh_tokens: dict[str, str] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    if not body.username or not body.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.username == body.username)
        )
        user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=403, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.username, "id": user.id})
    refresh_token = create_refresh_token({"sub": user.username, "id": user.id})
    _refresh_tokens[user.username] = refresh_token

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=7 * 24 * 3600,
        samesite="lax",
    )

    async with async_session() as session:
        result = await session.execute(
            select(Role).join(UserRole).where(UserRole.user_id == user.id)
        )
        roles = result.scalars().all()
        role_codes = [r.code for r in roles]

    return success({
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "roles": role_codes,
        "accessToken": access_token,
    })


@router.post("/refresh")
async def refresh(response: Response, refresh_token: str | None = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(status_code=403, detail="No refresh token")

    payload = decode_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=403, detail="Invalid refresh token")

    username = payload.get("sub")
    stored = _refresh_tokens.get(username)
    if stored != refresh_token:
        raise HTTPException(status_code=403, detail="Token mismatch")

    new_access = create_access_token({"sub": username, "id": payload.get("id")})
    new_refresh = create_refresh_token({"sub": username, "id": payload.get("id")})
    _refresh_tokens[username] = new_refresh

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        max_age=7 * 24 * 3600,
        samesite="lax",
    )

    return success(new_access)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return success(None)


@router.get("/codes")
async def get_access_codes(current_user: dict = Depends(get_current_user)):
    username = current_user.get("sub")
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        if not user:
            return success([])

        role_result = await session.execute(
            select(Role).join(UserRole).where(UserRole.user_id == user.id)
        )
        roles = role_result.scalars().all()

        perm_codes = set()
        for r in roles:
            rp_result = await session.execute(
                select(RolePermission.permission_id).where(RolePermission.role_id == r.id)
            )
            for (perm_id,) in rp_result.all():
                p_result = await session.execute(
                    select(Permission).where(Permission.id == perm_id)
                )
                perm = p_result.scalar_one_or_none()
                if perm:
                    perm_codes.add(perm.code)

        return success(list(perm_codes))
