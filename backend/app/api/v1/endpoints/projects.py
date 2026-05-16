from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
async def api_list_projects(keyword: str = Query(default=None), _user: CurrentUser = None, db: DbSession = ...):
    result = await list_projects(db, keyword=keyword)
    return success(result)


@router.post("")
async def api_create_project(body: ProjectCreate, _user: CurrentUser = None, db: DbSession = ...):
    result = await create_project(db, body.model_dump())
    return success(result)


@router.get("/{project_id}")
async def api_get_project(project_id: int, db: DbSession = ...):
    result = await get_project(db, project_id)
    return success(result)


@router.put("/{project_id}")
async def api_update_project(project_id: int, body: ProjectUpdate, _user: CurrentUser = None, db: DbSession = ...):
    result = await update_project(db, project_id, body.model_dump(exclude_unset=True))
    return success(result)


@router.delete("/{project_id}")
async def api_delete_project(project_id: int, _user: CurrentUser = None, db: DbSession = ...):
    await delete_project(db, project_id)
    return success({"success": True})
