from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.models.test import TestTask, Defect, TestReport

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
    stmt = select(TestTask)
    count_stmt = select(func.count()).select_from(TestTask)

    if project_id:
        stmt = stmt.where(TestTask.project_id == project_id)
        count_stmt = count_stmt.where(TestTask.project_id == project_id)
    if test_type:
        stmt = stmt.where(TestTask.test_type == test_type)
        count_stmt = count_stmt.where(TestTask.test_type == test_type)
    if status:
        stmt = stmt.where(TestTask.status == status)
        count_stmt = count_stmt.where(TestTask.status == status)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = stmt.order_by(TestTask.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    tests = result.scalars().all()

    items = [_test_to_dict(t) for t in tests]
    return success({"items": items, "total": total})


@router.post("")
async def create_test(body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    t = TestTask(**body)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return success({"id": t.id, **_test_to_dict(t)})


@router.get("/{test_id}")
async def get_test(test_id: int, db: DbSession = ...):
    result = await db.execute(select(TestTask).where(TestTask.id == test_id))
    t = result.scalar_one_or_none()
    if not t:
        return success(None)
    return success(_test_to_dict(t))


@router.post("/{test_id}/defects")
async def create_defect(test_id: int, body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    d = Defect(test_id=test_id, **body)
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return success({"id": d.id, **body})


@router.get("/{test_id}/report")
async def get_test_report(test_id: int, db: DbSession = ...):
    result = await db.execute(
        select(TestReport).where(TestReport.test_id == test_id)
    )
    r = result.scalar_one_or_none()
    if not r:
        return success(None)
    return success({
        "id": r.id,
        "test_id": r.test_id,
        "report_number": r.report_number,
        "test_type": r.test_type,
        "test_environment": r.test_environment,
        "test_duration_days": r.test_duration_days,
        "firmware_version": r.firmware_version,
        "hardware_version": r.hardware_version,
        "conclusion": r.conclusion,
        "notes": r.notes,
    })


@router.post("/{test_id}/report")
async def create_test_report(test_id: int, body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    r = TestReport(test_id=test_id, **body)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return success({"id": r.id, **body})


@router.put("/{test_id}/report")
async def update_test_report(test_id: int, body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    result = await db.execute(
        select(TestReport).where(TestReport.test_id == test_id)
    )
    r = result.scalar_one_or_none()
    if not r:
        return success(None)
    for key, value in body.items():
        if hasattr(r, key):
            setattr(r, key, value)
    await db.commit()
    return success({"id": r.id})


@router.get("/{test_id}/report/export")
async def export_test_report(test_id: int, _user: CurrentUser = ...):
    return success({"message": "报告导出功能待实现"})


@router.post("/{test_id}/report/distribute")
async def distribute_report(test_id: int, body: dict, _user: CurrentUser = ...):
    return success({"success": True, "message": "报告已分发"})


def _test_to_dict(t: TestTask) -> dict:
    return {
        "id": t.id,
        "test_name": t.test_name,
        "project_id": t.project_id,
        "test_type": t.test_type,
        "status": t.status,
        "description": t.description,
        "start_time": t.start_time.strftime("%Y-%m-%d %H:%M:%S") if t.start_time else None,
        "expected_end_time": t.expected_end_time.strftime("%Y-%m-%d %H:%M:%S") if t.expected_end_time else None,
    }
