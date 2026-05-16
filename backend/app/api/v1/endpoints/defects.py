from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.schemas.test import DefectUpdate
from app.services import defect_service

router = APIRouter(prefix="/defects", tags=["defects"])


@router.get("")
async def list_defects(
    db: DbSession = ...,
    test_id: int = Query(default=None),
    severity: str = Query(default=None),
    status: str = Query(default=None),
):
    data = await defect_service.list_defects(db, test_id=test_id, severity=severity, status=status)
    return success(data)


@router.put("/{defect_id}")
async def update_defect(defect_id: int, body: DefectUpdate, db: DbSession = ..., _user: CurrentUser = ...):
    data = await defect_service.update_defect(db, defect_id, body.model_dump(exclude_unset=True))
    return success(data)
