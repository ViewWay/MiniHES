from datetime import datetime

from pydantic import BaseModel, Field


# ── Users ──

class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(default="123456", max_length=128)
    email: str = Field(default="", max_length=100)
    phone: str = Field(default="", max_length=20)
    avatar: str = Field(default="", max_length=500)
    department_id: int | None = None
    is_active: bool = True
    role_ids: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    department_id: int | None = None
    is_active: bool | None = None
    password: str | None = None
    role_ids: list[int] | None = None


class UserItem(BaseModel):
    id: int
    username: str
    name: str
    email: str
    phone: str
    avatar: str
    department_id: int | None
    role_ids: list[int]
    roles: list[str]
    status: str
    created_at: str

    model_config = {"from_attributes": True}


class UserListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    keyword: str | None = None
    role: str | None = None


# ── Roles ──

class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=500)
    sort_order: int = 0
    permission_ids: list[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None
    permission_ids: list[int] | None = None


class RoleItem(BaseModel):
    id: int
    name: str
    code: str
    description: str
    sort_order: int
    permission_ids: list[int]
    user_count: int

    model_config = {"from_attributes": True}


# ── Departments ──

class DeptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    parent_id: int | None = None
    sort_order: int = 0
    leader: str = Field(default="", max_length=50)


class DeptUpdate(BaseModel):
    name: str | None = None
    sort_order: int | None = None
    leader: str | None = None
    status: str | None = None


class DeptItem(BaseModel):
    id: int
    name: str
    code: str
    parent_id: int | None
    sort_order: int
    leader: str
    status: str
    created_at: str

    model_config = {"from_attributes": True}


# ── Permissions ──

class PermissionItem(BaseModel):
    id: int
    name: str
    code: str
    type: str
    parent_id: int | None
    path: str
    icon: str
    sort_order: int
    status: str

    model_config = {"from_attributes": True}


# ── Audit Logs ──

class AuditLogQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    user_id: int | None = None
    operation_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class AuditLogItem(BaseModel):
    id: int
    user_id: int
    username: str
    operation_type: str
    resource_type: str
    resource_id: int
    ip_address: str
    created_at: str

    model_config = {"from_attributes": True}


# ── Data Archive ──

class DataArchiveCreate(BaseModel):
    archive_type: str = Field(default="postgresql")
    table_name: str = Field(..., min_length=1)


class DataArchiveItem(BaseModel):
    id: int
    archive_type: str
    table_name: str
    start_time: str
    end_time: str
    record_count: int
    status: str
    created_at: str

    model_config = {"from_attributes": True}
