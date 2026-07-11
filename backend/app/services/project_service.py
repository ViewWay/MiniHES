from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.project import Project


def _project_to_dict(p: Project) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "test_lead_id": p.test_lead_id,
        "dev_lead_id": p.dev_lead_id,
        "start_date": str(p.start_date) if p.start_date else None,
        "end_date": str(p.end_date) if p.end_date else None,
        "status": p.status,
        "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "",
        "updated_at": p.updated_at.strftime("%Y-%m-%d %H:%M:%S") if p.updated_at else "",
    }


async def list_projects(db: AsyncSession, keyword: str | None = None) -> dict:
    stmt = select(Project)
    if keyword:
        stmt = stmt.where(Project.name.ilike(f"%{keyword}%"))
    stmt = stmt.order_by(Project.id)
    result = await db.execute(stmt)
    projects = result.scalars().all()

    # 批量查询各项目的设备数和在线数
    from sqlalchemy import func

    from app.models.meter import Meter

    count_stmt = (
        select(
            Meter.project_id,
            func.count(Meter.id).label("total"),
            func.count(Meter.id).filter(Meter.current_status.in_(["in_use", "online"])).label("online"),
        )
        .where(Meter.project_id.isnot(None))
        .group_by(Meter.project_id)
    )
    count_result = await db.execute(count_stmt)
    counts = {r[0]: {"total": r[1], "online": r[2]} for r in count_result}

    items = []
    for p in projects:
        d = _project_to_dict(p)
        c = counts.get(p.id, {"total": 0, "online": 0})
        d["device_count"] = c["total"]
        d["online_count"] = c["online"]
        items.append(d)
    return {"items": items, "total": len(items)}


async def get_project(db: AsyncSession, project_id: int) -> dict | None:
    p = await db.get(Project, project_id)
    if not p:
        return None
    return _project_to_dict(p)


async def create_project(db: AsyncSession, data: dict) -> dict:
    project = Project(**data)
    db.add(project)
    await db.flush()
    return {"id": project.id, **_project_to_dict(project)}


async def update_project(db: AsyncSession, project_id: int, data: dict) -> dict | None:
    p = await db.get(Project, project_id)
    if not p:
        raise BusinessException(code=404, message="项目不存在")
    for key, value in data.items():
        if hasattr(p, key):
            setattr(p, key, value)
    return {"id": project_id, **_project_to_dict(p)}


async def delete_project(db: AsyncSession, project_id: int) -> None:
    p = await db.get(Project, project_id)
    if p:
        await db.delete(p)
