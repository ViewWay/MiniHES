from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=128, description="密码")


class LoginResponse(BaseModel):
    id: int
    username: str
    name: str
    roles: list[str]
    accessToken: str  # noqa: N815

    model_config = {"from_attributes": True}


class RefreshResponse(BaseModel):
    accessToken: str  # noqa: N815


class TokenPayload(BaseModel):
    sub: str
    id: int
    exp: int | None = None


class AccessCodesResponse(BaseModel):
    codes: list[str]
