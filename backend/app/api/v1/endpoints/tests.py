import io

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.schemas.test import DefectCreate, TestReportCreate, TestReportUpdate, TestTaskCreate
from app.services import defect_service, test_service

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
        db,
        page=page,
        page_size=page_size,
        project_id=project_id,
        test_type=test_type,
        status=status,
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
async def export_test_report(test_id: int, db: DbSession = ..., _user: CurrentUser = ...):
    """导出测试报告为 CSV（从 PG lab_test_task + lab_defect 真实数据生成）。"""
    import csv
    import io as _io

    # 查测试任务
    test = await test_service.get_test(db, test_id)
    if not test:
        return success({"error": "测试任务不存在"})

    # 查缺陷
    defects = await defect_service.list_defects(db, test_id=test_id)

    output = _io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["测试报告"])
    writer.writerow(["任务ID", test.get("id", test_id)])
    writer.writerow(["任务名称", test.get("task_name", "")])
    writer.writerow(["设备", test.get("meter_name", "")])
    writer.writerow(["状态", test.get("status", "")])
    writer.writerow(["开始时间", test.get("start_time", "")])
    writer.writerow(["完成时间", test.get("end_time", "")])
    writer.writerow([])
    writer.writerow(["缺陷列表"])
    writer.writerow(["序号", "描述", "严重程度", "状态", "发现时间"])
    for i, d in enumerate(defects.get("items", []), 1):
        writer.writerow(
            [i, d.get("description", ""), d.get("severity", ""), d.get("status", ""), d.get("found_at", "")]
        )

    csv_bytes = output.getvalue().encode("utf-8-sig")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=test_report_{test_id}.csv"},
    )


@router.post("/{test_id}/report/distribute")
async def distribute_report(test_id: int, body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    """分发测试报告（更新报告状态）。"""
    from app.models.test import TestTask

    recipients = body.get("recipients", [])
    test_task = await db.get(TestTask, test_id)
    if test_task:
        test_task.status = "distributed"
        await db.commit()

    return success(
        {
            "success": True,
            "message": f"报告已分发给 {len(recipients)} 人",
            "test_id": test_id,
            "recipients": recipients,
        }
    )
