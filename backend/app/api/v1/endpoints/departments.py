from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.core.auth import get_current_user
from app.core.database import AsyncSessionLocal as async_session
from app.core.response import success, fail
from app.models.user import Department, User

router = APIRouter(prefix="/system/dept", tags=["department"])


class DepartmentCreate(BaseModel):
    name: str
    code: str
    pid: int | None = None
    sort_order: int | None = None
    leader: str | None = None
    status: int = 1


class DepartmentUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    pid: int | None = None
    sort_order: int | None = None
    leader: str | None = None
    status: int | None = None


def _dept_to_dict(d: Department) -> dict:
    return {
        "id": d.id,
        "pid": d.parent_id or 0,
        "name": d.name,
        "code": d.code,
        "status": 1 if d.status == "active" else 0,
        "sortOrder": d.sort_order,
        "leader": d.leader,
        "createTime": d.created_at.strftime("%Y-%m-%d %H:%M:%S") if d.created_at else "",
    }


@router.get("/list")
async def list_departments(_=get_current_user):
    async with async_session() as session:
        result = await session.execute(
            select(Department).order_by(Department.sort_order)
        )
        depts = result.scalars().all()

        dept_map = {d.id: _dept_to_dict(d) for d in depts}
        tree = []
        for d in depts:
            item = dept_map[d.id]
            if d.parent_id and d.parent_id in dept_map:
                parent = dept_map[d.parent_id]
                parent.setdefault("children", []).append(item)
            else:
                tree.append(item)
        return success(tree)


@router.post("")
async def create_department(body: DepartmentCreate, _=get_current_user):
    async with async_session() as session:
        existing = await session.execute(
            select(Department).where(Department.code == body.code)
        )
        if existing.scalar_one_or_none():
            return fail(code=10001, message="部门编码已存在", status=400)
        dept = Department(
            name=body.name,
            code=body.code,
            parent_id=body.pid,
            sort_order=body.sort_order or 0,
            leader=body.leader or "",
            status="active" if body.status == 1 else "inactive",
        )
        session.add(dept)
        await session.commit()
        await session.refresh(dept)
        return success(_dept_to_dict(dept))


@router.put("/{dept_id}")
async def update_department(dept_id: int, body: DepartmentUpdate, _=get_current_user):
    async with async_session() as session:
        result = await session.execute(
            select(Department).where(Department.id == dept_id)
        )
        dept = result.scalar_one_or_none()
        if not dept:
            return fail(code=10001, message="部门不存在", status=404)
        if body.name is not None:
            dept.name = body.name
        if body.code is not None:
            dept.code = body.code
        if body.pid is not None:
            dept.parent_id = body.pid
        if body.sort_order is not None:
            dept.sort_order = body.sort_order
        if body.leader is not None:
            dept.leader = body.leader
        if body.status is not None:
            dept.status = "active" if body.status == 1 else "inactive"
        await session.commit()
        return success(None)


@router.delete("/{dept_id}")
async def delete_department(dept_id: int, _=get_current_user):
    async with async_session() as session:
        result = await session.execute(
            select(Department).where(Department.id == dept_id)
        )
        dept = result.scalar_one_or_none()
        if not dept:
            return fail(code=10001, message="部门不存在", status=404)

        child_count = await session.execute(
            select(Department).where(Department.parent_id == dept_id)
        )
        if child_count.scalars().first():
            return fail(code=10002, message="存在子部门，无法删除", status=400)

        user_count = await session.execute(
            select(User).where(User.department_id == dept_id)
        )
        if user_count.scalars().first():
            return fail(code=10003, message="部门下存在用户，无法删除", status=400)

        await session.delete(dept)
        await session.commit()
        return success(None)
