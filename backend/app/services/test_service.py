from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.test import Defect, TestReport, TestTask


def _test_to_dict(t: TestTask) -> dict:
    """Convert a TestTask ORM object to a plain dict for API responses."""
    return {
        "id": t.id,
        "test_name": t.test_name,
        "test_type": t.test_type,
        "project_id": t.project_id,
        "status": t.status,
        "description": t.description,
        "start_time": t.start_time.strftime("%Y-%m-%d %H:%M:%S") if t.start_time else None,
        "expected_end_time": t.expected_end_time.strftime("%Y-%m-%d %H:%M:%S") if t.expected_end_time else None,
        "created_by": t.created_by,
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else None,
        "updated_at": t.updated_at.strftime("%Y-%m-%d %H:%M:%S") if t.updated_at else None,
    }


def _report_to_dict(r: TestReport) -> dict:
    """Convert a TestReport ORM object to a plain dict for API responses."""
    return {
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
        "generated_by": r.generated_by,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
        "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None,
    }


async def list_tests(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    project_id: int | None = None,
    test_type: str | None = None,
    status: str | None = None,
) -> dict:
    """Return paginated test task list."""
    stmt = select(TestTask)
    count_stmt = select(func.count()).select_from(TestTask)

    if project_id is not None:
        stmt = stmt.where(TestTask.project_id == project_id)
        count_stmt = count_stmt.where(TestTask.project_id == project_id)
    if test_type:
        stmt = stmt.where(TestTask.test_type == test_type)
        count_stmt = count_stmt.where(TestTask.test_type == test_type)
    if status:
        stmt = stmt.where(TestTask.status == status)
        count_stmt = count_stmt.where(TestTask.status == status)

    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(
        stmt.order_by(TestTask.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = [_test_to_dict(t) for t in result.scalars().all()]
    return {"items": items, "total": total}


async def get_test(db: AsyncSession, test_id: int) -> dict | None:
    """Return a single test task by id, or None if not found."""
    t = await db.get(TestTask, test_id)
    if not t:
        return None
    return _test_to_dict(t)


async def create_test(db: AsyncSession, data: dict) -> dict:
    """Create a test task and return the dict with id."""
    test = TestTask(**data)
    db.add(test)
    await db.flush()
    return _test_to_dict(test)


async def get_test_report(db: AsyncSession, test_id: int) -> dict | None:
    """Return the report for a given test, or None if not found."""
    result = await db.execute(
        select(TestReport).where(TestReport.test_id == test_id)
    )
    r = result.scalar_one_or_none()
    if not r:
        return None
    return _report_to_dict(r)


async def create_test_report(db: AsyncSession, test_id: int, data: dict) -> int:
    """Create a test report. Returns the report id."""
    # Verify the test exists
    test = await db.get(TestTask, test_id)
    if not test:
        raise BusinessException(code=404, message="测试任务不存在")

    # Check if a report already exists for this test
    existing = await db.execute(
        select(TestReport).where(TestReport.test_id == test_id)
    )
    if existing.scalar_one_or_none():
        raise BusinessException(code=409, message="该测试任务已存在报告")

    data["test_id"] = test_id
    report = TestReport(**data)
    db.add(report)
    await db.flush()
    return report.id


async def update_test_report(db: AsyncSession, test_id: int, data: dict) -> int | None:
    """Update the report for a given test. Returns the report id or None if not found."""
    result = await db.execute(
        select(TestReport).where(TestReport.test_id == test_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        return None

    for key, value in data.items():
        if hasattr(report, key) and value is not None:
            setattr(report, key, value)
    await db.flush()
    return report.id
