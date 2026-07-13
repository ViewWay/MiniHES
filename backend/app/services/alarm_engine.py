"""告警自动生成引擎。

在采集数据写入后评估 AlarmRule，自动生成 Alarm 记录。

condition_config 结构定义：
  threshold:
    {"operator": "gt|lt|gte|lte|eq", "value": 240.0}
  anomaly:
    {"deviation_sigma": 3.0}     # 偏离历史均值 N 个标准差
    {"change_pct": 50.0}         # 较上一次变化超 N%
  communication:
    {"offline_hours": 24}        # 离线超过 N 小时

集成点：
  - task_service._collect_meter_data 写入 readings 后调用 evaluate_readings
  - scheduler 定时调用 check_communication_alarms 扫描离线设备
"""

import datetime
import logging
import math
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alarm import Alarm, AlarmRule
from app.models.meter import Meter, MeterSnapshot
from app.models.meter_point import MeterReading

logger = logging.getLogger(__name__)

# 去重窗口：同一规则对同一电表的同一OBIS点，N小时内只告警一次
_DEDUP_HOURS = 1


async def evaluate_readings(db: AsyncSession, meter_id: int, readings: list[MeterReading]) -> list[Alarm]:
    """评估采集读数，生成阈值和异常类告警。

    在 task_service._collect_meter_data 之后调用。
    返回新生成的 Alarm 列表。
    """
    if not readings:
        return []

    # 查询所有启用的 threshold / anomaly 规则
    stmt = (
        select(AlarmRule)
        .where(AlarmRule.is_enabled == True)  # noqa: E712
        .where(AlarmRule.rule_type.in_(["threshold", "anomaly"]))
    )
    result = await db.execute(stmt)
    rules = result.scalars().all()

    if not rules:
        return []

    new_alarms: list[Alarm] = []

    for reading in readings:
        # 获取该读数对应的 OBIS 码
        point = reading.point
        if point is None:
            continue
        obis_code = point.obis_code
        value = float(reading.reading_value) if reading.reading_value is not None else None
        if value is None:
            continue

        for rule in rules:
            # 按 point_code 匹配（空 point_code 表示匹配所有点）
            if rule.point_code and rule.point_code != obis_code:
                continue

            config = rule.condition_config or {}
            triggered = False
            threshold_val: float | None = None
            alarm_msg = ""

            if rule.rule_type == "threshold":
                triggered, threshold_val, alarm_msg = _eval_threshold(value, config, rule.rule_name)
            elif rule.rule_type == "anomaly":
                triggered, threshold_val, alarm_msg = await _eval_anomaly(
                    db, meter_id, point.id, value, config, rule.rule_name
                )

            if not triggered:
                continue

            # 去重检查：同一规则+电表+N小时内是否已有告警
            if await _has_recent_alarm(db, meter_id, rule.id):
                continue

            alarm = Alarm(
                meter_id=meter_id,
                rule_id=rule.id,
                alarm_type=rule.rule_type,
                severity=rule.severity,
                alarm_message=alarm_msg,
                alarm_value=value,
                threshold_value=threshold_val,
                is_handled=False,
            )
            db.add(alarm)
            new_alarms.append(alarm)

    if new_alarms:
        await db.flush()
        # 通过 WebSocket 推送新告警
        await _broadcast_alarms(new_alarms, meter_id)

    return new_alarms


async def check_communication_alarms(db: AsyncSession) -> list[Alarm]:
    """扫描通信类告警（离线设备检测）。

    在 scheduler 中定时调用（建议每 15 分钟）。
    """
    # 查询启用的 communication 规则
    stmt = (
        select(AlarmRule)
        .where(AlarmRule.is_enabled == True)  # noqa: E712
        .where(AlarmRule.rule_type == "communication")
    )
    result = await db.execute(stmt)
    rules = result.scalars().all()

    if not rules:
        return []

    new_alarms: list[Alarm] = []
    now = datetime.datetime.now(datetime.timezone.utc)

    for rule in rules:
        config = rule.condition_config or {}
        offline_hours = config.get("offline_hours", 24)
        threshold_dt = now - datetime.timedelta(hours=offline_hours)

        # 查询所有在用电表的快照
        meter_stmt = (
            select(Meter, MeterSnapshot)
            .outerjoin(MeterSnapshot, MeterSnapshot.meter_id == Meter.id)
            .where(Meter.current_status == "in_use")
        )
        meter_result = await db.execute(meter_stmt)
        rows = meter_result.all()

        for meter, snap in rows:
            is_offline = False
            last_comm = None

            if snap:
                last_comm = snap.last_comm_time
                if snap.last_comm_time:
                    # 有通信记录但超时
                    if snap.last_comm_time < threshold_dt:
                        is_offline = True
                elif not snap.online_status:
                    # 无通信记录且离线
                    is_offline = True

            if not is_offline:
                continue

            # 去重
            if await _has_recent_alarm(db, meter.id, rule.id, hours=offline_hours):
                continue

            time_desc = ""
            if last_comm:
                elapsed = (now - last_comm).total_seconds() / 3600
                time_desc = f"，最后通信: {elapsed:.0f} 小时前"
            else:
                time_desc = "，无通信记录"

            alarm = Alarm(
                meter_id=meter.id,
                rule_id=rule.id,
                alarm_type="communication",
                severity=rule.severity,
                alarm_message=f"设备通信超时: {rule.rule_name}{time_desc}",
                alarm_value=None,
                threshold_value=float(offline_hours),
                is_handled=False,
            )
            db.add(alarm)
            new_alarms.append(alarm)

    if new_alarms:
        await db.flush()
        await _broadcast_alarms(new_alarms, None)

    return new_alarms


# ─── 阈值评估 ───


def _eval_threshold(value: float, config: dict[str, Any], rule_name: str) -> tuple[bool, float | None, str]:
    """评估阈值规则。

    config: {"operator": "gt|lt|gte|lte|eq", "value": number}
    返回: (是否触发, 阈值参考值, 告警消息)
    """
    operator = config.get("operator", "gt")
    threshold = config.get("value")

    if threshold is None:
        return False, None, ""

    threshold = float(threshold)

    triggered = False
    if operator == "gt" and value > threshold:
        triggered = True
    elif operator == "lt" and value < threshold:
        triggered = True
    elif operator == "gte" and value >= threshold:
        triggered = True
    elif operator == "lte" and value <= threshold:
        triggered = True
    elif operator == "eq" and math.isclose(value, threshold, rel_tol=1e-6):
        triggered = True

    if not triggered:
        return False, threshold, ""

    op_label = {"gt": ">", "lt": "<", "gte": "≥", "lte": "≤", "eq": "="}.get(operator, operator)
    msg = f"{rule_name}: 当前值 {value:.2f} {op_label} 阈值 {threshold:.2f}"
    return True, threshold, msg


# ─── 异常检测 ───


async def _eval_anomaly(
    db: AsyncSession,
    meter_id: int,
    point_id: int,
    value: float,
    config: dict[str, Any],
    rule_name: str,
) -> tuple[bool, float | None, str]:
    """评估异常检测规则。

    config 支持两种模式：
      - {"deviation_sigma": 3.0}: 偏离历史均值 N 个标准差
      - {"change_pct": 50.0}: 较上一次读数变化超 N%
    """
    # 模式 1: 标准差异常检测
    sigma_threshold = config.get("deviation_sigma")
    if sigma_threshold is not None:
        # 查最近 30 个读数作为基线
        baseline_stmt = (
            select(MeterReading.reading_value)
            .where(MeterReading.meter_id == meter_id)
            .where(MeterReading.point_id == point_id)
            .order_by(MeterReading.reading_time.desc())
            .limit(30)
        )
        result = await db.execute(baseline_stmt)
        values = [float(v) for v in result.scalars().all() if v is not None]

        if len(values) < 5:
            # 样本不足，跳过
            return False, None, ""

        # 均值和标准差（排除当前值——values[0] 就是当前值）
        baseline = values[1:]  # 排除当前值
        if len(baseline) < 4:
            return False, None, ""

        mean = sum(baseline) / len(baseline)
        variance = sum((x - mean) ** 2 for x in baseline) / len(baseline)
        std = math.sqrt(variance) if variance > 0 else 0

        if std == 0:
            return False, None, ""

        deviation = abs(value - mean) / std
        if deviation >= float(sigma_threshold):
            msg = (
                f"{rule_name}: 当前值 {value:.2f} 偏离均值 " f"{mean:.2f} 达 {deviation:.1f}σ (阈值 {sigma_threshold}σ)"
            )
            return True, mean, msg

    # 模式 2: 变化率异常检测
    change_pct_threshold = config.get("change_pct")
    if change_pct_threshold is not None:
        # 查上一个读数
        prev_stmt = (
            select(MeterReading.reading_value)
            .where(MeterReading.meter_id == meter_id)
            .where(MeterReading.point_id == point_id)
            .order_by(MeterReading.reading_time.desc())
            .offset(1)
            .limit(1)
        )
        result = await db.execute(prev_stmt)
        prev_val = result.scalar()

        if prev_val is None or float(prev_val) == 0:
            return False, None, ""

        prev_val = float(prev_val)
        change_pct = abs(value - prev_val) / abs(prev_val) * 100

        if change_pct >= float(change_pct_threshold):
            msg = (
                f"{rule_name}: 当前值 {value:.2f} 较上次 {prev_val:.2f} "
                f"变化 {change_pct:.1f}% (阈值 {change_pct_threshold}%)"
            )
            return True, prev_val, msg

    return False, None, ""


# ─── 去重 ───


async def _has_recent_alarm(db: AsyncSession, meter_id: int, rule_id: int, hours: int = _DEDUP_HOURS) -> bool:
    """检查同一规则对同一电表在指定小时内是否已有告警。"""
    threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    stmt = (
        select(func.count())
        .select_from(Alarm)
        .where(Alarm.meter_id == meter_id)
        .where(Alarm.rule_id == rule_id)
        .where(Alarm.created_at >= threshold)
    )
    count = (await db.execute(stmt)).scalar()
    return count > 0


# ─── WebSocket 推送 ───


async def _broadcast_alarms(alarms: list[Alarm], meter_id: int | None) -> None:
    """通过 WebSocket 推送新告警通知。"""
    try:
        from app.core.ws_manager import manager

        for alarm in alarms:
            await manager.broadcast(
                "alarm:new",
                "created",
                {
                    "id": alarm.id,
                    "meter_id": alarm.meter_id,
                    "alarm_type": alarm.alarm_type,
                    "severity": alarm.severity,
                    "alarm_message": alarm.alarm_message,
                    "alarm_value": float(alarm.alarm_value) if alarm.alarm_value else None,
                    "threshold_value": float(alarm.threshold_value) if alarm.threshold_value else None,
                    "created_at": alarm.created_at.isoformat() if alarm.created_at else None,
                },
            )
    except Exception as e:
        # WebSocket 推送失败不影响告警写入
        logger.warning("告警 WebSocket 推送失败: %s", e)
