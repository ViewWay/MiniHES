from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal as async_session
from app.core.response import success
from app.models.project import Project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
async def list_projects(keyword: str = Query(default=None)):
    async with async_session() as session:
        stmt = select(Project)
        if keyword:
            stmt = stmt.where(Project.name.ilike(f"%{keyword}%"))
        stmt = stmt.order_by(Project.id)
        result = await session.execute(stmt)
        projects = result.scalars().all()
        items = [_project_to_dict(p) for p in projects]
        return success({"items": items, "total": len(items)})


@router.post("")
async def create_project(body: dict):
    async with async_session() as session:
        p = Project(**body)
        session.add(p)
        await session.commit()
        await session.refresh(p)
        return success({"id": p.id, **_project_to_dict(p)})


@router.get("/{project_id}")
async def get_project(project_id: int):
    async with async_session() as session:
        result = await session.execute(select(Project).where(Project.id == project_id))
        p = result.scalar_one_or_none()
        if not p:
            return success(None)
        return success(_project_to_dict(p))


@router.put("/{project_id}")
async def update_project(project_id: int, body: dict):
    async with async_session() as session:
        result = await session.execute(select(Project).where(Project.id == project_id))
        p = result.scalar_one_or_none()
        if not p:
            return success(None)
        for key, value in body.items():
            setattr(p, key, value)
        await session.commit()
        return success({"id": project_id, **_project_to_dict(p)})


@router.delete("/{project_id}")
async def delete_project(project_id: int):
    async with async_session() as session:
        result = await session.execute(select(Project).where(Project.id == project_id))
        p = result.scalar_one_or_none()
        if p:
            await session.delete(p)
            await session.commit()
        return success({"success": True})


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
