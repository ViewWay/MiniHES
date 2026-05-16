import io
import csv
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from app.core.auth import get_current_user
from app.core.database import AsyncSessionLocal as async_session
from app.core.response import success, fail
from app.core.security import get_password_hash
from app.models.system import AuditLog, DataArchive
from app.models.user import User, UserRole, Role, RolePermission, Permission

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/users")
async def list_users(
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    keyword: str = Query(default=None),
    role: str = Query(default=None),
    _=Depends(get_current_user),
):
    async with async_session() as session:
        stmt = select(User)
        count_stmt = select(func.count()).select_from(User)

        if keyword:
            kw = f"%{keyword}%"
            stmt = stmt.where(User.name.ilike(kw) | User.username.ilike(kw))
            count_stmt = count_stmt.where(User.name.ilike(kw) | User.username.ilike(kw))

        total = (await session.execute(count_stmt)).scalar() or 0

        result = await session.execute(
            stmt.order_by(User.id).offset((page - 1) * page_size).limit(page_size)
        )
        users = result.scalars().all()

        items = []
        for u in users:
            role_result = await session.execute(
                select(Role).join(UserRole).where(UserRole.user_id == u.id)
            )
            roles = role_result.scalars().all()
            items.append({
                "id": u.id,
                "username": u.username,
                "name": u.name,
                "email": u.email,
                "phone": u.phone,
                "avatar": u.avatar,
                "department_id": u.department_id,
                "role_ids": [r.id for r in roles],
                "roles": [r.code for r in roles],
                "status": "active" if u.is_active else "inactive",
                "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else "",
            })
        return success({"items": items, "total": total})


@router.post("/users")
async def create_user(body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        existing = await session.execute(
            select(User).where(User.username == body.get("username"))
        )
        if existing.scalar_one_or_none():
            return fail(code=10001, message="用户名已存在", status=400)

        password = body.pop("password", "123456")
        role_ids = body.pop("role_ids", [])

        user = User(
            username=body.get("username", ""),
            password_hash=get_password_hash(password),
            name=body.get("name", ""),
            email=body.get("email", ""),
            phone=body.get("phone", ""),
            avatar=body.get("avatar", ""),
            department_id=body.get("department_id"),
            is_active=body.get("is_active", True),
        )
        session.add(user)
        await session.flush()

        for rid in role_ids:
            session.add(UserRole(user_id=user.id, role_id=rid))
        await session.commit()
        await session.refresh(user)
        return success({"id": user.id})


@router.put("/users/{user_id}")
async def update_user(user_id: int, body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return fail(code=10001, message="用户不存在", status=404)

        role_ids = body.pop("role_ids", None)
        password = body.pop("password", None)

        for key, value in body.items():
            if hasattr(user, key):
                setattr(user, key, value)
        if password:
            user.password_hash = get_password_hash(password)

        if role_ids is not None:
            await session.execute(
                UserRole.__table__.delete().where(UserRole.user_id == user_id)
            )
            for rid in role_ids:
                session.add(UserRole(user_id=user_id, role_id=rid))

        await session.commit()
        return success(None)


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return fail(code=10001, message="用户不存在", status=404)
        await session.execute(
            UserRole.__table__.delete().where(UserRole.user_id == user_id)
        )
        await session.delete(user)
        await session.commit()
        return success(None)


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(user_id: int, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return fail(code=10001, message="用户不存在", status=404)
        user.password_hash = get_password_hash("123456")
        await session.commit()
        return success(None)


@router.get("/roles")
async def list_roles(_=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(Role).order_by(Role.id))
        roles = result.scalars().all()
        items = []
        for r in roles:
            count_result = await session.execute(
                select(func.count()).select_from(UserRole).where(UserRole.role_id == r.id)
            )
            user_count = count_result.scalar() or 0

            perm_result = await session.execute(
                select(RolePermission.permission_id).where(RolePermission.role_id == r.id)
            )
            permission_ids = [p[0] for p in perm_result.all()]

            items.append({
                "id": r.id,
                "name": r.name,
                "code": r.code,
                "description": r.description,
                "sort_order": r.sort_order,
                "permission_ids": permission_ids,
                "user_count": user_count,
            })
        return success({"items": items, "total": len(items)})


@router.post("/roles")
async def create_role(body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        existing = await session.execute(
            select(Role).where(Role.code == body.get("code"))
        )
        if existing.scalar_one_or_none():
            return fail(code=10001, message="角色编码已存在", status=400)

        perm_ids = body.pop("permission_ids", [])
        role = Role(
            name=body.get("name", ""),
            code=body.get("code", ""),
            description=body.get("description", ""),
            sort_order=body.get("sort_order", 0),
        )
        session.add(role)
        await session.flush()

        for pid in perm_ids:
            session.add(RolePermission(role_id=role.id, permission_id=pid))
        await session.commit()
        return success({"id": role.id})


@router.put("/roles/{role_id}")
async def update_role(role_id: int, body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            return fail(code=10001, message="角色不存在", status=404)

        perm_ids = body.pop("permission_ids", None)
        for key, value in body.items():
            if hasattr(role, key):
                setattr(role, key, value)

        if perm_ids is not None:
            await session.execute(
                RolePermission.__table__.delete().where(RolePermission.role_id == role_id)
            )
            for pid in perm_ids:
                session.add(RolePermission(role_id=role_id, permission_id=pid))

        await session.commit()
        return success(None)


@router.delete("/roles/{role_id}")
async def delete_role(role_id: int, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            return fail(code=10001, message="角色不存在", status=404)

        user_count = (
            await session.execute(
                select(func.count()).select_from(UserRole).where(UserRole.role_id == role_id)
            )
        ).scalar() or 0
        if user_count > 0:
            return fail(code=10002, message="角色下存在用户，无法删除", status=400)

        await session.execute(
            RolePermission.__table__.delete().where(RolePermission.role_id == role_id)
        )
        await session.delete(role)
        await session.commit()
        return success(None)


@router.get("/permissions/tree")
async def get_permission_tree(_=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(
            select(Permission).order_by(Permission.sort_order)
        )
        perms = result.scalars().all()
        items = [_perm_to_dict(p) for p in perms]
        return success(items)


@router.get("/health")
async def system_health():
    return success({
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "api": {"status": "running"},
            "dlms_engine": {"status": "running"},
            "scheduler": {"status": "running"},
        },
    })


@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    user_id: int = Query(default=None),
    operation_type: str = Query(default=None),
    start_date: str = Query(default=None),
    end_date: str = Query(default=None),
    _=Depends(get_current_user),
):
    async with async_session() as session:
        stmt = select(AuditLog)
        count_stmt = select(func.count()).select_from(AuditLog)

        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
            count_stmt = count_stmt.where(AuditLog.user_id == user_id)
        if operation_type:
            stmt = stmt.where(AuditLog.operation_type == operation_type)
            count_stmt = count_stmt.where(AuditLog.operation_type == operation_type)

        total = (await session.execute(count_stmt)).scalar() or 0

        result = await session.execute(
            stmt.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        items = [
            {
                "id": l.id,
                "user_id": l.user_id,
                "username": l.username,
                "operation_type": l.operation_type,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "ip_address": l.ip_address,
                "created_at": l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else "",
            }
            for l in result.scalars().all()
        ]
        return success({"items": items, "total": total})


@router.get("/audit-logs/export")
async def export_audit_logs(
    user_id: int = Query(default=None),
    operation_type: str = Query(default=None),
    _=Depends(get_current_user),
):
    async with async_session() as session:
        stmt = select(AuditLog).order_by(AuditLog.id.desc())
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if operation_type:
            stmt = stmt.where(AuditLog.operation_type == operation_type)

        result = await session.execute(stmt)
        logs = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "用户", "操作类型", "资源类型", "资源ID", "IP地址", "时间"])
    for l in logs:
        writer.writerow([
            l.id, l.username, l.operation_type, l.resource_type,
            l.resource_id, l.ip_address,
            l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


@router.get("/db-monitor")
async def db_monitor():
    return success({
        "postgresql": {"status": "running"},
        "redis": {"status": "stopped"},
        "influxdb": {"status": "stopped"},
    })


@router.get("/data-archive")
async def data_archive(
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    _=Depends(get_current_user),
):
    async with async_session() as session:
        count_result = await session.execute(select(func.count()).select_from(DataArchive))
        total = count_result.scalar() or 0

        result = await session.execute(
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
async def create_data_archive(body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        archive = DataArchive(
            archive_type=body.get("archive_type", "postgresql"),
            table_name=body.get("table_name", ""),
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            record_count=0,
            archive_status="pending",
        )
        session.add(archive)
        await session.commit()
        return success({"id": archive.id})


def _perm_to_dict(p: Permission) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "type": p.type,
        "parent_id": p.parent_id,
        "path": p.path,
        "icon": p.icon,
        "sort_order": p.sort_order,
        "status": p.status,
    }
