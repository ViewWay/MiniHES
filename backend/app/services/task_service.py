from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.meter import Meter, MeterSnapshot
from app.models.meter_point import MeterReading
from app.models.task import DataQuality, Task, TaskDevice, TaskLog


def _compute_next_execute_time(task: Task) -> datetime | None:
    """根据 schedule_config 计算下次执行时间（从 ORM 对象读取）。"""
    return _compute_next_execute_time_from_data(
        task_type=task.task_type,
        schedule_config=task.schedule_config or {},
        is_enabled=task.is_enabled,
    )


def _compute_next_execute_time_from_data(
    task_type: str,
    schedule_config: dict,
    is_enabled: bool = True,
) -> datetime | None:
    """根据 schedule_config 计算下次执行时间（从原始数据读取）。

    支持 cron / interval / once 三种类型。
    """
    if not is_enabled:
        return None

    config = schedule_config or {}

    if task_type == "once":
        return None  # 一次性任务不重复

    if task_type == "interval":
        minutes = config.get("interval_minutes", 60)
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)

    if task_type == "cron":
        cron_expr = config.get("cron", "")
        return _parse_cron_next(cron_expr)

    # 默认 1 小时后
    return datetime.now(timezone.utc) + timedelta(hours=1)


def _parse_cron_next(cron_expr: str) -> datetime:
    """简单解析 cron 表达式并计算下次执行时间。

    支持 5 段格式: minute hour day month weekday
    仅处理基本场景（* / 数字 / */n），复杂的交给 APScheduler。
    """
    if not cron_expr:
        return datetime.now(timezone.utc) + timedelta(hours=1)

    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return datetime.now(timezone.utc) + timedelta(hours=1)

    now = datetime.now(timezone.utc)

    # 简化：如果有 */N 分钟，计算下一个 N 分钟
    minute_part = parts[0]
    if minute_part.startswith("*/"):
        try:
            n = int(minute_part[2:])
            next_minute = ((now.minute // n) + 1) * n
            return now.replace(second=0, microsecond=0) + timedelta(minutes=next_minute - now.minute)
        except ValueError:
            pass

    # 默认：1 小时后
    return now + timedelta(hours=1)


def _task_to_dict(t: Task) -> dict:
    """Convert a Task ORM object to a plain dict for API responses."""
    return {
        "id": t.id,
        "task_name": t.task_name,
        "task_type": t.task_type,
        "device_type": t.device_type,
        "task_category": t.task_category,
        "obis_template_id": t.obis_template_id,
        "schedule_config": t.schedule_config,
        "execution_content": t.execution_content,
        "filter_config": t.filter_config,
        "priority": t.priority,
        "retry_times": t.retry_times,
        "timeout": t.timeout,
        "is_enabled": t.is_enabled,
        "last_execute_time": t.last_execute_time.strftime("%Y-%m-%d %H:%M:%S") if t.last_execute_time else None,
        "next_execute_time": t.next_execute_time.strftime("%Y-%m-%d %H:%M:%S") if t.next_execute_time else None,
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
        "updated_at": t.updated_at.strftime("%Y-%m-%d %H:%M:%S") if t.updated_at else "",
    }


def _task_log_to_dict(log: TaskLog) -> dict:
    """Convert a TaskLog ORM object to a plain dict for API responses."""
    return {
        "id": log.id,
        "task_id": log.task_id,
        "start_time": log.start_time.strftime("%Y-%m-%d %H:%M:%S") if log.start_time else None,
        "end_time": log.end_time.strftime("%Y-%m-%d %H:%M:%S") if log.end_time else None,
        "duration_ms": log.duration_ms,
        "status": log.status,
        "total_devices": log.total_devices,
        "success_devices": log.success_devices,
        "failed_devices": log.failed_devices,
        "error_message": log.error_message or "",
    }


def _task_device_to_dict(d: TaskDevice) -> dict:
    """Convert a TaskDevice ORM object to a plain dict for API responses."""
    return {
        "id": d.id,
        "log_id": d.log_id,
        "task_id": d.task_id,
        "meter_id": d.meter_id,
        "status": d.status,
        "retry_count": d.retry_count,
        "error_code": d.error_code or "",
        "error_message": d.error_message or "",
        "start_time": d.start_time.strftime("%Y-%m-%d %H:%M:%S") if d.start_time else None,
        "end_time": d.end_time.strftime("%Y-%m-%d %H:%M:%S") if d.end_time else None,
        "duration_ms": d.duration_ms,
        "data_count": d.data_count,
    }


async def list_tasks(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    task_type: str | None = None,
    task_category: str | None = None,
    status: str | None = None,
    is_enabled: bool | None = None,
) -> dict:
    """Return paginated task list with total and running_count.

    支持 task_type / task_category / status / is_enabled 筛选。
    status 映射: enabled → is_enabled=True; disabled → is_enabled=False
    """
    stmt = select(Task)
    count_stmt = select(func.count()).select_from(Task)

    if task_type:
        stmt = stmt.where(Task.task_type == task_type)
        count_stmt = count_stmt.where(Task.task_type == task_type)
    if task_category:
        stmt = stmt.where(Task.task_category == task_category)
        count_stmt = count_stmt.where(Task.task_category == task_category)
    # status 筛选：映射到 is_enabled
    if status == "enabled":
        stmt = stmt.where(Task.is_enabled == True)  # noqa: E712
        count_stmt = count_stmt.where(Task.is_enabled == True)  # noqa: E712
    elif status == "disabled":
        stmt = stmt.where(Task.is_enabled == False)  # noqa: E712
        count_stmt = count_stmt.where(Task.is_enabled == False)  # noqa: E712
    if is_enabled is not None:
        stmt = stmt.where(Task.is_enabled == is_enabled)
        count_stmt = count_stmt.where(Task.is_enabled == is_enabled)

    total = (await db.execute(count_stmt)).scalar() or 0

    running_count_result = await db.execute(
        select(func.count()).select_from(Task).where(Task.is_enabled == True)  # noqa: E712
    )
    running_count = running_count_result.scalar() or 0

    result = await db.execute(stmt.order_by(Task.id).offset((page - 1) * page_size).limit(page_size))
    items = [_task_to_dict(t) for t in result.scalars().all()]
    return {"items": items, "total": total, "running_count": running_count}


async def get_task(db: AsyncSession, task_id: int) -> dict | None:
    """Return a single task by id, or None if not found."""
    t = await db.get(Task, task_id)
    if not t:
        return None
    return _task_to_dict(t)


def _validate_execution_config(data: dict) -> None:
    """如果 data 中有 device_type + task_category + execution_content，
    通过 ConfigRegistry 校验 execution_content 并写回校验后的值。

    未注册的组合或缺少 execution_content 时静默跳过（向后兼容）。
    """
    device_type = data.get("device_type")
    task_category = data.get("task_category")
    exec_content = data.get("execution_content")

    if not device_type or not task_category or not exec_content:
        return

    try:
        from app.services.collector.bootstrap import register_all
        from app.services.collector.registry import registry
        from app.services.collector.types import DeviceType, TaskCategory

        register_all()
        validated = registry.validate_config(DeviceType(device_type), TaskCategory(task_category), exec_content)
        # 写回校验 + 填充默认值后的 config
        data["execution_content"] = validated.model_dump(exclude_none=True)
    except (ValueError, KeyError):
        # 未知组合或校验失败时跳过（向后兼容旧任务）
        pass


async def create_task(db: AsyncSession, data: dict) -> dict:
    """Create a task and return its data dict."""
    _validate_execution_config(data)
    task = Task(**data)
    db.add(task)
    await db.flush()
    # 计算首次执行时间（使用 data 避免 lazy-load 触发 greenlet 问题）
    task.next_execute_time = _compute_next_execute_time_from_data(
        task_type=data.get("task_type", "cron"),
        schedule_config=data.get("schedule_config", {}),
        is_enabled=data.get("is_enabled", True),
    )
    await db.flush()
    # 刷新以获取 server_default 生成的 created_at/updated_at
    await db.refresh(task)
    return {"id": task.id, **_task_to_dict(task)}


async def update_task(db: AsyncSession, task_id: int, data: dict) -> dict | None:
    """Update a task. Returns None if task not found."""
    t = await db.get(Task, task_id)
    if not t:
        return None
    for key, value in data.items():
        if hasattr(t, key):
            setattr(t, key, value)
    return _task_to_dict(t)


async def delete_task(db: AsyncSession, task_id: int) -> None:
    """Delete a task. Raises 404 if not found."""
    t = await db.get(Task, task_id)
    if not t:
        raise BusinessException(code=404, message="任务不存在")
    await db.delete(t)


async def toggle_task(db: AsyncSession, task_id: int, is_enabled: bool) -> bool:
    """Toggle task enabled state. Returns False if task not found."""
    t = await db.get(Task, task_id)
    if not t:
        raise BusinessException(code=404, message="任务不存在")
    t.is_enabled = is_enabled
    return is_enabled


async def execute_task(db: AsyncSession, task_id: int) -> dict:
    """执行采集任务：解析目标电表 → 逐表采集 → 写读数 → 统计结果。

    流程：
      1. 创建 TaskLog(status="running")
      2. 从 filter_config 解析目标电表列表
      3. 对每个电表创建 TaskDevice，执行采集
      4. 更新 MeterSnapshot（含 eeprom_write_count/stack_usage）
      5. 写 DataQuality 统计
      6. 更新 TaskLog(status="completed", 真实统计)
    """
    t = await db.get(Task, task_id)
    if not t:
        raise BusinessException(code=404, message="任务不存在")

    start_time = datetime.now(timezone.utc)

    # 创建执行日志
    task_log = TaskLog(
        task_id=task_id,
        start_time=start_time,
        status="running",
        total_devices=0,
        success_devices=0,
        failed_devices=0,
    )
    db.add(task_log)
    await db.flush()

    # 解析目标电表
    target_meters = await _resolve_target_meters(db, t)

    success_count = 0
    failed_count = 0

    for meter in target_meters:
        device_start = datetime.now(timezone.utc)
        try:
            # 执行采集（模拟 DLMS 读取）
            readings = await _collect_meter_data(db, t, meter)

            # 评估告警规则（阈值 + 异常检测）
            from app.services.alarm_engine import evaluate_readings

            await evaluate_readings(db, meter.id, readings)

            # 构建采集文档并写入 MongoDB（PG-Mongo 双写）
            await _save_to_mongo(db, t, meter, readings)

            # 创建 TaskDevice 记录
            td = TaskDevice(
                log_id=task_log.id,
                task_id=task_id,
                meter_id=meter.id,
                status="success",
                retry_count=0,
                start_time=device_start,
                end_time=datetime.now(timezone.utc),
                duration_ms=int((datetime.now(timezone.utc) - device_start).total_seconds() * 1000),
                data_count=len(readings),
            )
            db.add(td)

            # 更新 MeterSnapshot
            await _update_meter_snapshot(db, meter.id)

            success_count += 1
        except Exception as e:
            # 采集失败
            td = TaskDevice(
                log_id=task_log.id,
                task_id=task_id,
                meter_id=meter.id,
                status="failed",
                error_message=str(e)[:500],
                start_time=device_start,
                end_time=datetime.now(timezone.utc),
            )
            db.add(td)
            failed_count += 1

    # 写 DataQuality 统计
    if target_meters:
        await _write_data_quality(db, task_id, target_meters, success_count)

    # 更新执行日志
    end_time = datetime.now(timezone.utc)
    task_log.end_time = end_time
    task_log.duration_ms = int((end_time - start_time).total_seconds() * 1000)
    task_log.status = "completed" if failed_count == 0 else "failed"
    task_log.total_devices = len(target_meters)
    task_log.success_devices = success_count
    task_log.failed_devices = failed_count
    task_log.error_message = "" if failed_count == 0 else f"{failed_count} 台设备采集失败"

    t.last_execute_time = end_time
    await db.flush()

    return {
        "success": True,
        "execution_id": task_log.id,
        "total_devices": len(target_meters),
        "success_devices": success_count,
        "failed_devices": failed_count,
        "duration_ms": task_log.duration_ms,
    }


async def _resolve_target_meters(db: AsyncSession, task: Task) -> list[Meter]:
    """从 filter_config 解析目标电表列表。

    filter_config 支持：
      - meter_ids: [int]  → 直接指定
      - project_id: int   → 按项目筛选
      - meter_type_id: int → 按类型筛选
      - line_type: str    → 按接线方式筛选
    """
    filt = task.filter_config or {}

    # 直接指定 meter_ids
    meter_ids = filt.get("meter_ids", [])
    if meter_ids:
        result = await db.execute(select(Meter).where(Meter.id.in_(meter_ids)))
        return list(result.scalars().all())

    # 按条件筛选
    stmt = select(Meter).where(Meter.current_status == "in_use")
    project_id = filt.get("project_id")
    if project_id:
        stmt = stmt.where(Meter.project_id == project_id)
    meter_type_id = filt.get("meter_type_id")
    if meter_type_id:
        stmt = stmt.where(Meter.meter_type_id == meter_type_id)
    line_type = filt.get("line_type")
    if line_type:
        stmt = stmt.where(Meter.line_type == line_type)

    result = await db.execute(stmt.limit(100))
    meters = list(result.scalars().all())

    # 如果没有匹配，取所有在用设备
    if not meters:
        result = await db.execute(select(Meter).where(Meter.current_status == "in_use").limit(20))
        meters = list(result.scalars().all())

    return meters


async def _collect_meter_data(db: AsyncSession, task: Task, meter: Meter) -> list[MeterReading]:
    """对单台电表执行采集——从 MongoDB 真实文档读取数据。

    流程：查 MongoDB 该电表最新采集文档 → 提取关键 OBIS 点值 → 写入 col_meter_reading。
    如果 MongoDB 无该电表数据（PG 电表不在 DCPP 数据范围内），跳过该电表。
    """
    from app.core.mongo import get_mongo_db
    from app.services.mongo_session_repo import MongoSessionRepo

    now = datetime.now(timezone.utc)
    readings = []

    # 从 MongoDB 读取该电表的最新真实采集文档
    try:
        mongo_db = get_mongo_db()
        repo = MongoSessionRepo(mongo_db)

        # 按序列号查找（PG 电表序列号可能不匹配 DCPP device_id）
        latest_doc = None
        # 尝试按 meter_id 查
        latest_doc = await repo.get_latest_by_meter(meter.id, projection={"key_value_pairs": 1, "_id": 0})
        # 如果没有，尝试按序列号查
        if not latest_doc and meter.serial_number:
            col = mongo_db["meter_sessions"]
            latest_doc = await col.find_one(
                {"meter_serial": meter.serial_number},
                sort=[("collected_at", -1)],
                projection={"key_value_pairs": 1, "_id": 0},
            )

        if not latest_doc:
            # 该电表在 MongoDB 中无数据，跳过（不生成假数据）
            return readings

        kvp = latest_doc.get("key_value_pairs", {})
    except Exception:
        # MongoDB 不可用时跳过采集，不生成假数据
        return readings

    # 从真实 key_value_pairs 中提取关键 OBIS 点
    # DCPP 键名格式: "Active energy import.value", "Instantaneous voltage L1.value" 等
    obis_map = [
        ("1.0.1.8.0.255", "positive_active_energy", lambda kvp: kvp.get("Active energy import.value")),
        ("1.0.2.8.0.255", "negative_active_energy", lambda kvp: kvp.get("Active energy export.value")),
        ("1.0.32.7.0.255", "voltage_l1", lambda kvp: kvp.get("Instantaneous voltage L1.value")),
        ("1.0.31.7.0.255", "current_l1", lambda kvp: kvp.get("Instantaneous current L1.value")),
    ]

    from app.models.meter_point import MeterPoint

    for obis_code, point_name, get_val in obis_map:
        value = get_val(kvp)
        if value is None:
            continue  # 该点在真实文档中不存在，跳过

        # 确保是数值
        try:
            numeric_value = float(value) if not isinstance(value, (int, float)) else value
        except (ValueError, TypeError):
            continue

        # 查找或创建测量点
        point_result = await db.execute(
            select(MeterPoint).where(MeterPoint.meter_id == meter.id).where(MeterPoint.obis_code == obis_code)
        )
        point = point_result.scalars().first()

        if not point:
            point = MeterPoint(
                meter_id=meter.id,
                obis_code=obis_code,
                point_name=point_name,
                module="auto",
            )
            db.add(point)
            await db.flush()

        reading = MeterReading(
            meter_id=meter.id,
            point_id=point.id,
            task_id=task.id,
            reading_value=numeric_value,
            reading_time=now,
            quality="good",
            source="auto",
        )
        db.add(reading)
        readings.append(reading)

    await db.flush()
    return readings


async def _save_to_mongo(db: AsyncSession, task: Task, meter: Meter, readings: list[MeterReading]):
    """将采集结果写入 MongoDB meter_sessions（通过 session_writer 双写）。

    从 MongoDB 该电表的最新真实文档获取原始 DLMS 结构，
    复制为新文档并更新采集时间和来源标记。
    """
    from app.core.mongo import get_mongo_db
    from app.services.mongo_session_repo import MongoSessionRepo

    try:
        mongo_db = get_mongo_db()
        repo = MongoSessionRepo(mongo_db)

        # 获取该电表最新真实文档作为基础
        latest = await repo.get_latest_by_meter(meter.id)
        if not latest and meter.serial_number:
            col = mongo_db["meter_sessions"]
            latest = await col.find_one(
                {"meter_serial": meter.serial_number},
                sort=[("collected_at", -1)],
            )

        if not latest:
            return  # 无基础文档可复制

        # 创建新文档（标记为 auto 采集，复用真实 DLMS 结构）
        now = datetime.now(timezone.utc)
        new_doc = {
            "session_id": 0,
            "meter_id": meter.id,
            "meter_serial": meter.serial_number,
            "project_id": meter.project_id,
            "project_name": "",
            "task_id": task.id,
            "collected_at": now,
            "imported_at": now,
            "source": "auto",
            "source_file": f"task_{task.id}",
            "connection_type": "HDLC",
            "status": "success",
            # 复制旧文档时保留其原始 total_points，不用 readings 数
            "total_points": latest.get("total_points", len(readings)),
            "success_points": latest.get("success_points", len(readings)),
            "failed_points": 0,
            "sheets": latest.get("sheets", {}),
            "key_value_pairs": latest.get("key_value_pairs", {}),
            "summary": latest.get(
                "summary",
                {
                    "total_read": len(readings),
                    "total_success": len(readings),
                    "total_failed": 0,
                    "sheet_count": len(latest.get("sheets", {})),
                },
            ),
            "schema_version": 1,
        }

        # 直接写入 Mongo（session_writer 需要 PG session 对象，
        # 此处简单直接写入，不创建 PG col_session 记录）
        # 使用递减 session_id 避免唯一约束冲突
        max_session_id_doc = await mongo_db["meter_sessions"].find_one(sort=[("session_id", 1)])
        min_session_id = (max_session_id_doc or {}).get("session_id", 0)
        if isinstance(min_session_id, int) and min_session_id < 0:
            new_doc["session_id"] = min_session_id - 1
        else:
            new_doc["session_id"] = -1

        await mongo_db["meter_sessions"].insert_one(new_doc)
    except Exception:
        # Mongo 写入失败不影响 PG 事务
        pass


async def _update_meter_snapshot(db: AsyncSession, meter_id: int):
    """更新电表快照——从 MongoDB 真实文档读取 EEPROM/stack/信号数据。"""
    from app.core.mongo import get_mongo_db

    result = await db.execute(select(MeterSnapshot).where(MeterSnapshot.meter_id == meter_id))
    snap = result.scalars().first()

    now = datetime.now(timezone.utc)

    # 从 MongoDB 真实文档读取诊断数据
    eeprom_count = None
    stack_usage = None
    try:
        mongo_db = get_mongo_db()
        col = mongo_db["meter_sessions"]
        # 查电表最新文档
        meter = await db.get(Meter, meter_id)
        query = {"meter_id": meter_id}
        if meter and meter.serial_number:
            query = {"$or": [{"meter_id": meter_id}, {"meter_serial": meter.serial_number}]}
        latest = await col.find_one(query, sort=[("collected_at", -1)])
        if latest:
            eeprom_times = latest.get("eeprom_write_times", [])
            # eeprom_write_times 是一个列表，第一个元素是十六进制时间戳
            # 实际写入次数从 list 长度推导
            if isinstance(eeprom_times, list):
                eeprom_count = sum(1 for e in eeprom_times if isinstance(e, (int, str)))

            stack_info = latest.get("stack_information", [])
            if isinstance(stack_info, list) and stack_info:
                # stack_information 通常包含使用率信息
                stack_usage = len(stack_info)
    except Exception:
        pass

    if snap:
        snap.online_status = True
        snap.last_comm_time = now
        snap.last_data_time = now
        # 使用真实 EEPROM 数据（如可获取）
        if eeprom_count is not None:
            snap.eeprom_write_count = eeprom_count
        if stack_usage is not None:
            snap.stack_usage = stack_usage
        snap.error_code = ""
    else:
        snap = MeterSnapshot(
            meter_id=meter_id,
            online_status=True,
            last_comm_time=now,
            last_data_time=now,
            eeprom_write_count=eeprom_count,
            stack_usage=stack_usage,
            firmware_version="",
            error_code="",
        )
        db.add(snap)

    await db.flush()


async def _write_data_quality(
    db: AsyncSession,
    task_id: int,
    meters: list[Meter],
    success_count: int,
    points_per_meter: int = 4,
):
    """写入数据质量统计（upsert：同一天同电表更新而非插入）。"""
    from datetime import date as date_type

    from sqlalchemy.dialects.postgresql import insert as pg_insert

    today = date_type.today()
    total_points = len(meters) * points_per_meter
    success_points = success_count * points_per_meter

    score = round(success_points / total_points * 100, 2) if total_points > 0 else 0
    now = datetime.now(timezone.utc)

    for meter in meters:
        stmt = pg_insert(DataQuality).values(
            meter_id=meter.id,
            task_id=task_id,
            stat_date=today,
            total_points=points_per_meter,
            success_points=points_per_meter if success_count > 0 else 0,
            failed_points=0 if success_count > 0 else points_per_meter,
            quality_score=score,
            abnormal_count=0,
            first_collect_time=now,
            last_collect_time=now,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_data_quality",
            set_={
                "task_id": stmt.excluded.task_id,
                "total_points": stmt.excluded.total_points,
                "success_points": stmt.excluded.success_points,
                "failed_points": stmt.excluded.failed_points,
                "quality_score": stmt.excluded.quality_score,
                "last_collect_time": stmt.excluded.last_collect_time,
            },
        )
        await db.execute(stmt)

    await db.flush()


async def get_task_logs(db: AsyncSession, task_id: int) -> dict:
    """Return all logs for a given task."""
    result = await db.execute(select(TaskLog).where(TaskLog.task_id == task_id).order_by(TaskLog.id.desc()))
    items = [_task_log_to_dict(log) for log in result.scalars().all()]
    return {"items": items, "total": len(items)}


async def get_task_device_log(
    db: AsyncSession,
    log_id: int,
    *,
    status: str | None = None,
) -> dict:
    """Return task device list for a given log, optionally filtered by status."""
    stmt = select(TaskDevice).where(TaskDevice.log_id == log_id)
    if status:
        stmt = stmt.where(TaskDevice.status == status)
    stmt = stmt.order_by(TaskDevice.id)

    result = await db.execute(stmt)
    devices = [_task_device_to_dict(d) for d in result.scalars().all()]

    total = len(devices)
    success_count = sum(1 for d in devices if d["status"] == "success")
    failed_count = sum(1 for d in devices if d["status"] == "failed")

    return {
        "log_id": log_id,
        "devices": devices,
        "total": total,
        "success_count": success_count,
        "failed_count": failed_count,
    }
