import logging

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentUser, DbSession, MongoDb
from app.core.exceptions import BusinessException
from app.core.response import success
from app.services import analysis_service
from app.services.analysis_mongo_service import AnalysisMongoService
from app.services.mongo_session_repo import MongoSessionRepo

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)


def _make_service(db: DbSession, mongo: MongoDb) -> AnalysisMongoService:
    """构造 AnalysisMongoService 实例。"""
    return AnalysisMongoService(db, MongoSessionRepo(mongo))


def _make_pg_service(db: DbSession) -> AnalysisMongoService:
    """构造纯 PG 查询的 AnalysisMongoService（data-quality/reports 不需要 Mongo）。"""
    svc = AnalysisMongoService.__new__(AnalysisMongoService)
    svc.db = db
    svc.mongo = None
    return svc


# ══════════════════════════════════════════════════════════════════════
# 基础分析 (Basic Analysis) — 从 MongoDB 真实数据查询
# ══════════════════════════════════════════════════════════════════════


@router.get("/daily")
async def daily_analysis(
    meter_id: int = Query(default=1),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: DbSession = ...,
    mongo: MongoDb = ...,
    _user: CurrentUser = ...,
):
    """日线分析：按日期范围查询电表采集数据。

    数据来源：MongoDB meter_sessions 中该电表在 date_from ~ date_to 范围内的采集文档。
    """
    try:
        service = _make_service(db, mongo)
        result = await service.daily_analysis(meter_id, date_from, date_to)
        if result is None:
            raise BusinessException(code=404, message=f"电表 {meter_id} 不存在")
        return success(result)
    except BusinessException:
        raise
    except Exception as e:
        logger.error("日线分析查询失败: %s", e)
        raise BusinessException(code=500, message=f"查询失败: {e}")


@router.get("/daily/meters")
async def daily_meters(
    project_id: int | None = Query(default=None),
    db: DbSession = ...,
    mongo: MongoDb = ...,
    _user: CurrentUser = ...,
):
    """获取项目下有采集数据的电表列表（供筛选下拉框用）。"""
    service = _make_service(db, mongo)
    meters = await service.get_project_meters(project_id)
    return success({"items": meters, "total": len(meters)})


@router.get("/daily/export")
async def export_daily_analysis(
    meter_id: int = Query(default=1),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    format: str = Query(default="csv", description="导出格式: csv 或 pdf"),
    db: DbSession = ...,
    mongo: MongoDb = ...,
    _user: CurrentUser = ...,
):
    """日线分析导出（支持 CSV 和 PDF 格式）。"""
    import csv as csv_mod
    import io

    try:
        service = _make_service(db, mongo)
        result = await service.daily_analysis(meter_id, date_from, date_to)
        if result is None:
            raise BusinessException(code=404, message=f"电表 {meter_id} 不存在")

        if format.lower() == "pdf":
            from app.services.pdf_export_service import generate_daily_analysis_pdf

            pdf_bytes = generate_daily_analysis_pdf(result)
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=daily_{meter_id}.pdf",
                },
            )

        # 默认 CSV 格式
        output = io.StringIO()
        writer = csv_mod.writer(output)
        writer.writerow(["电表", result.get("meter_name", "")])
        writer.writerow(["日期范围", f"{result.get('date_from','')} ~ {result.get('date_to','')}"])
        writer.writerow([])
        writer.writerow(["日期", "累计电能", "日增量", "L1电压", "L1电流", "总功率", "完整率", "状态"])
        for r in result.get("daily_records", []):
            writer.writerow(
                [
                    r.get("date", ""),
                    r.get("total_energy", 0),
                    r.get("daily_increase", 0),
                    r.get("voltage_l1", ""),
                    r.get("current_l1", ""),
                    r.get("power_total", ""),
                    r.get("completeness", 0),
                    r.get("status", ""),
                ]
            )
        csv_bytes = output.getvalue().encode("utf-8-sig")
    except BusinessException:
        raise
    except Exception as e:
        logger.warning("日线分析导出失败: %s", e)
        csv_bytes = f"导出失败: {e}".encode("utf-8-sig")

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=daily_{meter_id}.csv",
        },
    )


@router.post("/compare")
async def compare_analysis(
    body: dict,
    db: DbSession = ...,
    mongo: MongoDb = ...,
    _user: CurrentUser = ...,
):
    """多表对比分析。

    数据来源：MongoDB 各电表的 Energy + Instantaneous + Daily Billing。
    """
    meter_ids = body.get("meter_ids", [])
    start_date = body.get("start_date")
    end_date = body.get("end_date")

    if not meter_ids or len(meter_ids) < 2:
        raise BusinessException(code=400, message="请选择至少 2 个设备进行对比")

    try:
        service = _make_service(db, mongo)
        result = await service.compare_meters(meter_ids, start_date, end_date)
        return success(result)
    except BusinessException:
        raise
    except Exception as e:
        logger.error("对比分析查询失败: %s", e)
        raise BusinessException(code=500, message=f"查询失败: {e}")


@router.get("/consistency")
async def get_consistency(
    project_id: int | None = Query(default=None),
    db: DbSession = ...,
    mongo: MongoDb = ...,
    _user: CurrentUser = ...,
):
    """PG col_session vs MongoDB 文档一致性检查。"""
    try:
        service = _make_service(db, mongo)
        result = await service.get_consistency(project_id)
        return success(result)
    except Exception as e:
        logger.error("一致性检查失败: %s", e)
        raise BusinessException(code=500, message=f"查询失败: {e}")


@router.post("/consistency/check")
async def trigger_consistency_check(
    db: DbSession = ...,
    mongo: MongoDb = ...,
    _user: CurrentUser = ...,
):
    """触发一致性检查（重新扫描 PG vs Mongo）。"""
    try:
        service = _make_service(db, mongo)
        result = await service.trigger_consistency_check()
        return success(result)
    except Exception as e:
        logger.error("一致性检查失败: %s", e)
        raise BusinessException(code=500, message=f"检查失败: {e}")


@router.get("/data-quality")
async def data_quality(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    meter_id: int | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    min_score: float | None = Query(default=None),
    project_id: int | None = Query(default=None),
    db: DbSession = ...,
    _user: CurrentUser = ...,
):
    """数据质量分析（来源 PG col_data_quality）。"""
    service = _make_pg_service(db)
    result = await service.get_data_quality(
        page=page,
        page_size=page_size,
        meter_id=meter_id,
        start_date=start_date,
        end_date=end_date,
        min_score=min_score,
        project_id=project_id,
    )
    return success(result)


@router.get("/data-quality/export")
async def export_data_quality(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    meter_id: int | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    min_score: float | None = Query(default=None),
    project_id: int | None = Query(default=None),
    db: DbSession = ...,
    _user: CurrentUser = ...,
):
    """数据质量 CSV 导出。"""
    import io

    service = _make_pg_service(db)
    result = await service.get_data_quality(
        page=page,
        page_size=page_size,
        meter_id=meter_id,
        start_date=start_date,
        end_date=end_date,
        min_score=min_score,
        project_id=project_id,
    )
    csv_bytes = service.export_data_quality_csv(result)

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data_quality.csv"},
    )


@router.get("/reports")
async def list_reports(
    project_id: int | None = Query(default=None),
    db: DbSession = ...,
    _user: CurrentUser = ...,
):
    """分析报告列表（来源 PG lab_test_report）。"""
    service = _make_pg_service(db)
    result = await service.get_reports(project_id)
    return success(result)


@router.get("/reports/{report_id}/export")
async def export_report(report_id: int, db: DbSession = ..., _user: CurrentUser = ...):
    """分析报告 CSV 导出（从 PG lab_test_report 真实数据生成）。"""
    import csv
    import io

    from app.models.test import TestReport

    report = await db.get(TestReport, report_id)
    if not report:
        return success({"error": f"报告 {report_id} 不存在"})

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["分析报告"])
    writer.writerow(["报告ID", report.id])
    writer.writerow(["报告名称", report.report_name or ""])
    writer.writerow(["项目ID", report.project_id or ""])
    writer.writerow(["状态", report.status or ""])
    writer.writerow(["创建时间", report.created_at.strftime("%Y-%m-%d %H:%M:%S") if report.created_at else ""])
    writer.writerow([])
    writer.writerow(["测试项目", "结果", "备注"])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"},
    )


# ══════════════════════════════════════════════════════════════════════
# 运维报表 (Operation Reports) — 10 个新报表，数据来自真实查询 + mock 兜底
# ══════════════════════════════════════════════════════════════════════


# ── R-01 通信成功率 ──────────────────────────────────────────────────────
@router.get("/comm-success-rate")
async def comm_success_rate(
    db: DbSession,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    project_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await analysis_service.get_comm_success_rate(
        db,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        page=page,
        page_size=page_size,
    )
    return success(data)


# ── UC-8 未通信设备 ──────────────────────────────────────────────────────
@router.get("/non-comm-devices")
async def non_comm_devices(
    db: DbSession,
    hours_min: int = Query(default=24, ge=1),
    project_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await analysis_service.get_non_comm_devices(
        db,
        hours_min=hours_min,
        project_id=project_id,
        page=page,
        page_size=page_size,
    )
    return success(data)


# ── R-07 抄表完整率 ──────────────────────────────────────────────────────
@router.get("/read-completeness")
async def read_completeness(
    db: DbSession,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    project_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await analysis_service.get_read_completeness(
        db,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        page=page,
        page_size=page_size,
    )
    return success(data)


# ── R-10 重试分析 ────────────────────────────────────────────────────────
@router.get("/retry-analysis")
async def retry_analysis(
    db: DbSession,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    project_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await analysis_service.get_retry_analysis(
        db,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        page=page,
        page_size=page_size,
    )
    return success(data)


# ── R-12 未确认告警报表 ──────────────────────────────────────────────────
@router.get("/open-alarms-report")
async def open_alarms_report(
    db: DbSession,
    severity: str | None = Query(default=None),
    alarm_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await analysis_service.get_open_alarms_report(
        db,
        severity=severity,
        alarm_type=alarm_type,
        page=page,
        page_size=page_size,
    )
    return success(data)


# ── R-13 告警趋势 ────────────────────────────────────────────────────────
@router.get("/alarm-trend")
async def alarm_trend(
    db: DbSession,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await analysis_service.get_alarm_trend(
        db,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return success(data)


# ── R-16 设备健康 ────────────────────────────────────────────────────────
@router.get("/device-health")
async def device_health(
    db: DbSession,
    project_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await analysis_service.get_device_health(
        db,
        project_id=project_id,
        page=page,
        page_size=page_size,
    )
    return success(data)


# ── R-18 信号老化 ────────────────────────────────────────────────────────
@router.get("/signal-aging")
async def signal_aging(
    db: DbSession,
    project_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await analysis_service.get_signal_aging(
        db,
        project_id=project_id,
        page=page,
        page_size=page_size,
    )
    return success(data)


# ── R-30 负荷曲线 ────────────────────────────────────────────────────────
@router.get("/consumption-trend")
async def consumption_trend(
    db: DbSession,
    meter_id: int | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await analysis_service.get_consumption_trend(
        db,
        meter_id=meter_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return success(data)


# ── R-11 按需抄表历史 ────────────────────────────────────────────────────
@router.get("/ondemand-history")
async def ondemand_history(
    db: DbSession,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await analysis_service.get_ondemand_history(
        db,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return success(data)
