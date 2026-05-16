from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    id: int
    username: str
    name: str
    roles: list[str]
    accessToken: str


class RefreshResponse(BaseModel):
    accessToken: str
