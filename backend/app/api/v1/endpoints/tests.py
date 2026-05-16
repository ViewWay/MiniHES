from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.schemas.test import TestTaskCreate, TestReportCreate, TestReportUpdate, DefectCreate
from app.services import test_service, defect_service

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("")
async def list_tests(
    db: DbSession = ...,
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    project_id: int = Query(default=None),
    test_type: str = Query(default=None),
    status: str = Query(default=None),
):
    data = await test_service.list_tests(
        db, page=page, page_size=page_size,
        project_id=project_id, test_type=test_type, status=status,
    )
    return success(data)


@router.post("")
async def create_test(body: TestTaskCreate, db: DbSession = ..., _user: CurrentUser = ...):
    data = await test_service.create_test(db, body.model_dump())
    return success(data)


@router.get("/{test_id}")
async def get_test(test_id: int, db: DbSession = ...):
    data = await test_service.get_test(db, test_id)
    return success(data)


@router.post("/{test_id}/defects")
async def create_defect(test_id: int, body: DefectCreate, db: DbSession = ..., _user: CurrentUser = ...):
    defect_id = await defect_service.create_defect(db, test_id, body.model_dump())
    return success({"id": defect_id})


@router.get("/{test_id}/report")
async def get_test_report(test_id: int, db: DbSession = ...):
    data = await test_service.get_test_report(db, test_id)
    return success(data)


@router.post("/{test_id}/report")
async def create_test_report(test_id: int, body: TestReportCreate, db: DbSession = ..., _user: CurrentUser = ...):
    report_id = await test_service.create_test_report(db, test_id, body.model_dump())
    return success({"id": report_id})


@router.put("/{test_id}/report")
async def update_test_report(test_id: int, body: TestReportUpdate, db: DbSession = ..., _user: CurrentUser = ...):
    report_id = await test_service.update_test_report(db, test_id, body.model_dump(exclude_unset=True))
    return success({"id": report_id})


@router.get("/{test_id}/report/export")
async def export_test_report(test_id: int, _user: CurrentUser = ...):
    return success({"message": "报告导出功能待实现"})


@router.post("/{test_id}/report/distribute")
async def distribute_report(test_id: int, body: dict, _user: CurrentUser = ...):
    return success({"success": True, "message": "报告已分发"})
