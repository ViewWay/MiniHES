from datetime import datetime, timezone

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.models.system import DataArchive
from app.schemas.system import (
    DataArchiveCreate,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)
from app.services.audit_service import export_audit_logs_csv, list_audit_logs
from app.services.role_service import create_role, delete_role, get_permission_tree, list_roles, update_role
from app.services.user_service import create_user, delete_user, list_users, reset_password, update_user

router = APIRouter(prefix="/system", tags=["system"])


# ── Users ──


@router.get("/users")
async def api_list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str = Query(default=None),
    role: str = Query(default=None),
    _user: CurrentUser = None,
    db: DbSession = ...,
):
    result = await list_users(db, page=page, page_size=page_size, keyword=keyword, role=role)
    return success(result)


@router.post("/users")
async def api_create_user(body: UserCreate, _user: CurrentUser = None, db: DbSession = ...):
    uid = await create_user(db, body.model_dump())
    return success({"id": uid})


@router.put("/users/{user_id}")
async def api_update_user(user_id: int, body: UserUpdate, _user: CurrentUser = None, db: DbSession = ...):
    await update_user(db, user_id, body.model_dump(exclude_unset=True))
    return success(None)


@router.delete("/users/{user_id}")
async def api_delete_user(user_id: int, _user: CurrentUser = None, db: DbSession = ...):
    await delete_user(db, user_id)
    return success(None)


@router.post("/users/{user_id}/reset-password")
async def api_reset_password(user_id: int, _user: CurrentUser = None, db: DbSession = ...):
    await reset_password(db, user_id)
    return success(None)


# ── Roles ──


@router.get("/roles")
async def api_list_roles(_user: CurrentUser = None, db: DbSession = ...):
    result = await list_roles(db)
    return success(result)


@router.post("/roles")
async def api_create_role(body: RoleCreate, _user: CurrentUser = None, db: DbSession = ...):
    rid = await create_role(db, body.model_dump())
    return success({"id": rid})


@router.put("/roles/{role_id}")
async def api_update_role(role_id: int, body: RoleUpdate, _user: CurrentUser = None, db: DbSession = ...):
    await update_role(db, role_id, body.model_dump(exclude_unset=True))
    return success(None)


@router.delete("/roles/{role_id}")
async def api_delete_role(role_id: int, _user: CurrentUser = None, db: DbSession = ...):
    await delete_role(db, role_id)
    return success(None)


@router.get("/permissions/tree")
async def api_permission_tree(_user: CurrentUser = None, db: DbSession = ...):
    items = await get_permission_tree(db)
    return success(items)


# ── Health ──


@router.get("/health")
async def system_health():
    return success(
        {
            "status": "healthy",
            "version": "1.0.0",
            "services": {
                "api": {"status": "running"},
                "dlms_engine": {"status": "running"},
                "scheduler": {"status": "running"},
            },
        }
    )


# ── Audit Logs ──


@router.get("/audit-logs")
async def api_list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: int = Query(default=None),
    operation_type: str = Query(default=None),
    _user: CurrentUser = None,
    db: DbSession = ...,
):
    result = await list_audit_logs(db, page=page, page_size=page_size, user_id=user_id, operation_type=operation_type)
    return success(result)


@router.get("/audit-logs/export")
async def api_export_audit_logs(
    user_id: int = Query(default=None),
    operation_type: str = Query(default=None),
    _user: CurrentUser = None,
    db: DbSession = ...,
):
    return await export_audit_logs_csv(db, user_id=user_id, operation_type=operation_type)


# ── DB Monitor ──


@router.get("/db-monitor")
async def db_monitor():
    return success(
        {
            "postgresql": {"status": "running"},
            "redis": {"status": "stopped"},
            "influxdb": {"status": "stopped"},
        }
    )


# ── Data Archive ──


@router.get("/data-archive")
async def api_list_data_archives(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _user: CurrentUser = None,
    db: DbSession = ...,
):
    from sqlalchemy import func, select

    total = (await db.execute(select(func.count()).select_from(DataArchive))).scalar() or 0
    result = await db.execute(
        select(DataArchive).order_by(DataArchive.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = [
        {
            "id": a.id,
            "archive_type": a.archive_type,
            "table_name": a.table_name,
            "start_time": a.start_time.strftime("%Y-%m-%d %H:%M:%S") if a.start_time else "",
            "end_time": a.end_time.strftime("%Y-%m-%d %H:%M:%S") if a.end_time else "",
            "record_count": a.record_count,
            "status": a.archive_status,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else "",
        }
        for a in result.scalars().all()
    ]
    return success({"items": items, "total": total})


@router.post("/data-archive")
async def api_create_data_archive(body: DataArchiveCreate, _user: CurrentUser = None, db: DbSession = ...):
    archive = DataArchive(
        archive_type=body.archive_type,
        table_name=body.table_name,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        record_count=0,
        archive_status="pending",
    )
    db.add(archive)
    return success({"id": archive.id})
