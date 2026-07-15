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


# ══════════════════════════════════════════════════════════════════════
# 电表详情看板
# ══════════════════════════════════════════════════════════════════════


@router.get("/meter-detail")
async def meter_detail(
    meter_id: int | None = Query(default=None),
    db_name: str | None = Query(default=None, alias="db"),
    collection: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    db: DbSession = ...,
    mongo: MongoDb = ...,
    _user: CurrentUser = ...,
):
    """电表详情看板：解析 MongoDB DLMS 文档为完整数据结构。"""
    from datetime import datetime, timezone

    from app.services.mongo_session_repo import MongoSessionRepo

    repo = MongoSessionRepo(mongo)
    doc = None
    if meter_id:
        doc = await repo.get_latest_by_meter(meter_id, projection={})
    elif db_name and collection:
        col = mongo[collection]
        doc = await col.find_one({}, sort=[("collected_at", -1)])

    if not doc:
        raise BusinessException(code=404, message="未找到采集数据")

    kvp = doc.get("key_value_pairs", {})

    def _kvp_get(*keys):
        for k in keys:
            v = kvp.get(k)
            if v is not None and v != "ObjectUndefined":
                return v
        return None

    device_id = _kvp_get("Device ID.value")
    logical_name = _kvp_get("LogicalName.value")
    clock_time = _kvp_get("Clock.time", "Clock.Clock.Time")
    has_l2 = _kvp_get("Instantaneous voltage L2.value") is not None
    meter_type = "three" if has_l2 else "single"
    phase_count = 3 if has_l2 else 1
    connection = {
        "app1_version": doc.get("app1_version", ""),
        "app2_version": doc.get("app2_version", ""),
    }

    instantaneous = {}
    for key, value in kvp.items():
        if key.endswith(".value") and value is not None and value != "ObjectUndefined":
            kl = key.lower()
            if any(w in kl for w in ["voltage", "current", "power", "frequency"]):
                instantaneous[key.replace(".value", "").strip()] = value

    energy = {
        "cumulative_positive": _kvp_get("Active energy import.value", "Energy.Cumulative A Positive.Value"),
        "cumulative_negative": _kvp_get("Active energy export.value", "Energy.Cumulative A Negative.Value"),
    }

    event_buckets = {
        "standard": [],
        "fraud": [],
        "quality": [],
        "communication": [],
        "disconnector": [],
        "other": [],
    }
    for key, value in kvp.items():
        if not key.endswith(".Buffer") or not isinstance(value, dict):
            continue
        items = []
        for _idx, entry in value.items():
            if isinstance(entry, list) and len(entry) >= 2:
                items.append(
                    {
                        "t": str(entry[0])[:19] if entry[0] else "",
                        "code": str(entry[1]) if len(entry) > 1 else "",
                    }
                )
        kl = key.lower()
        if "fraud" in kl:
            event_buckets["fraud"].extend(items)
        elif "quality" in kl:
            event_buckets["quality"].extend(items)
        elif "communication" in kl or "comm" in kl:
            event_buckets["communication"].extend(items)
        elif "standard" in kl:
            event_buckets["standard"].extend(items)
        elif "disconnector" in kl:
            event_buckets["disconnector"].extend(items)
        elif items:
            event_buckets["other"].extend(items)

    # 电能质量
    pq_buf = kvp.get("PowerQualityProfile1.buffer", {})
    pq_points = []
    sag_count = 0
    swell_count = 0
    if isinstance(pq_buf, dict):
        for idx in sorted(pq_buf.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            entry = pq_buf[idx]
            if isinstance(entry, list) and len(entry) >= 2:
                ts = str(entry[0])[:16] if entry[0] else f"#{idx}"
                vals = entry[1] if isinstance(entry[1], list) else [entry[1]]
                vmin = vals[0] if len(vals) > 0 else 0
                vmax = vals[1] if len(vals) > 1 else vmin
                vavg = vals[2] if len(vals) > 2 else (vmin + vmax) / 2
                if vavg and vavg < 198:
                    sag_count += 1
                if vavg and vavg > 242:
                    swell_count += 1
                pq_points.append({"t": ts, "vmin": vmin, "vmax": vmax, "vavg": vavg})
    pq_total = len(pq_points)
    pq_pass = pq_total - sag_count - swell_count
    power_quality = {
        "points": pq_points,
        "total": pq_total,
        "sag_count": sag_count,
        "swell_count": swell_count,
        "pass_rate": round(pq_pass / pq_total * 100, 1) if pq_total > 0 else 0,
    }

    # 负荷曲线
    lp_buf = kvp.get("Load profile with period 1.buffer") or kvp.get("Load Profile.Energy Profile.Buffer") or {}
    load_profile = []
    if isinstance(lp_buf, dict):
        for idx in sorted(lp_buf.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            entry = lp_buf[idx]
            if isinstance(entry, list) and len(entry) >= 3:
                i = int(idx) if idx.isdigit() else 0
                load_profile.append(
                    {
                        "index": i,
                        "time_slot": f"{i * 15 // 60:02d}:{i * 15 % 60:02d}",
                        "raw_timestamp": str(entry[0]),
                        "cumulative_energy": entry[2],
                    }
                )

    # 硬件诊断
    eeprom_raw = doc.get("eeprom_write_times")
    stack_raw = doc.get("stack_information")
    stack_segments = {}
    eeprom_top = []
    eeprom_max = 0
    eeprom_total = 0
    if isinstance(stack_raw, list) and len(stack_raw) >= 4:
        for m in stack_raw[2] if isinstance(stack_raw[2], list) else []:
            if isinstance(m, list) and len(m) >= 5:
                name = m[0] if isinstance(m[0], str) else f"task_{len(stack_segments)}"
                stack_segments[name] = {"used": m[3] or 0, "size": m[1] or 0}
    if isinstance(eeprom_raw, list) and len(eeprom_raw) >= 4:
        writes = eeprom_raw[3] if isinstance(eeprom_raw[3], list) else []
        eeprom_total = sum(writes)
        eeprom_max = max(writes) if writes else 0
        indexed = sorted([(i, w) for i, w in enumerate(writes)], key=lambda x: x[1], reverse=True)
        eeprom_top = [{"idx": i, "val": w} for i, w in indexed[:15] if w > 0]

    collected_at = doc.get("collected_at", datetime.now(timezone.utc))
    t_str = collected_at.strftime("%Y-%m-%d %H:%M") if hasattr(collected_at, "strftime") else str(collected_at)[:16]
    hardware_timeline = [
        {
            "t": t_str,
            "stack": {"segments": stack_segments},
            "flash": {},
            "eeprom": {"top": eeprom_top, "max": eeprom_max, "total": eeprom_total},
        }
    ]
    for key, value in kvp.items():
        if "flash" in key.lower() and isinstance(value, (int, float)):
            hardware_timeline[0]["flash"][key.split(".")[0][-2:]] = value

    return success(
        {
            "device_meta": {
                "device_id": str(device_id) if device_id else "",
                "logical_name": str(logical_name) if logical_name else "",
                "clock_time": str(clock_time) if clock_time else "",
            },
            "meter_type": meter_type,
            "phase_count": phase_count,
            "connection": connection,
            "mongo_db": doc.get("project_name", ""),
            "mongo_collection": "meter_sessions",
            "instantaneous": instantaneous,
            "energy": energy,
            "events": {"buckets": event_buckets},
            "power_quality": power_quality,
            "load_profile": load_profile,
            "hardware": {"timeline": hardware_timeline},
            "warning": None,
        }
    )
