from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.user import Department, User


async def list_departments(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Department).order_by(Department.sort_order))
    depts = result.scalars().all()

    dept_map = {}
    for d in depts:
        dept_map[d.id] = {
            "id": d.id,
            "pid": d.parent_id or 0,
            "name": d.name,
            "code": d.code,
            "status": 1 if d.status == "active" else 0,
            "sortOrder": d.sort_order,
            "leader": d.leader,
            "createTime": d.created_at.strftime("%Y-%m-%d %H:%M:%S") if d.created_at else "",
        }

    tree = []
    for d in depts:
        item = dept_map[d.id]
        if d.parent_id and d.parent_id in dept_map:
            dept_map[d.parent_id].setdefault("children", []).append(item)
        else:
            tree.append(item)
    return tree


async def create_department(db: AsyncSession, data: dict) -> dict:
    existing = await db.execute(select(Department).where(Department.code == data["code"]))
    if existing.scalar_one_or_none():
        raise BusinessException(code=409, message="部门编码已存在")

    data["status"] = "active" if data.pop("status", 1) == 1 else "inactive"
    data["parent_id"] = data.pop("pid", None)
    dept = Department(**data)
    db.add(dept)
    await db.flush()
    return {
        "id": dept.id,
        "pid": dept.parent_id or 0,
        "name": dept.name,
        "code": dept.code,
        "status": 1 if dept.status == "active" else 0,
        "sortOrder": dept.sort_order,
        "leader": dept.leader,
    }


async def update_department(db: AsyncSession, dept_id: int, data: dict) -> None:
    dept = await db.get(Department, dept_id)
    if not dept:
        raise BusinessException(code=404, message="部门不存在")

    mapping = {"pid": "parent_id"}
    for key, value in data.items():
        attr = mapping.get(key, key)
        if value is not None:
            if attr == "status":
                value = "active" if value == 1 else "inactive"
            setattr(dept, attr, value)


async def delete_department(db: AsyncSession, dept_id: int) -> None:
    dept = await db.get(Department, dept_id)
    if not dept:
        raise BusinessException(code=404, message="部门不存在")

    child = await db.execute(select(Department).where(Department.parent_id == dept_id))
    if child.scalars().first():
        raise BusinessException(code=400, message="存在子部门，无法删除")

    users = await db.execute(select(User).where(User.department_id == dept_id))
    if users.scalars().first():
        raise BusinessException(code=400, message="部门下存在用户，无法删除")

    await db.delete(dept)
