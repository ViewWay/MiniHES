"""数据分析业务逻辑层（MongoDB 版）。

从 PostgreSQL（元数据 + 汇总统计）和 MongoDB（原始采集文档）
联合查询，为 analysis API 前 9 个路由提供真实数据。

重要约束：此文件不修改或覆盖 analysis_service.py 中已有的 10 个运维报表函数。
"""

import csv
import io
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meter import Meter
from app.models.session import CollectionSession
from app.models.task import DataQuality
from app.services.mongo_session_repo import MongoSessionRepo

logger = logging.getLogger(__name__)


class AnalysisMongoService:
    """分析服务：PG 元数据 + Mongo 原始数据联合查询。

    服务于 analysis.py 基础分析路由：
      - daily / daily/export
      - compare
      - consistency / consistency/check
      - data-quality / data-quality/export
      - reports / reports/{id}/export
    """

    def __init__(self, db: AsyncSession, mongo_repo: MongoSessionRepo):
        self.db = db
        self.mongo = mongo_repo

    # ═════════════════════════════════════════════════════════════════════
    #  1. 日线分析 GET /analysis/daily
    # ═════════════════════════════════════════════════════════════════════

    async def daily_analysis(
        self,
        meter_id: int,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict | None:
        """日线分析：按日期范围查询电表采集数据。

        流程：项目→设备→日期范围。
        从 MongoDB 查询该电表在 date_from ~ date_to 范围内的所有采集文档，
        生成每日采集记录列表和趋势图。
        """
        from datetime import timedelta as td

        meter = await self.db.get(Meter, meter_id)
        if not meter:
            return None

        # 解析日期范围（默认最近 30 天）
        end_date = datetime.now(timezone.utc) if not date_to else datetime.fromisoformat(date_to)
        start_date = end_date - td(days=30) if not date_from else datetime.fromisoformat(date_from)

        # 从 MongoDB 查询范围内的所有采集文档（只取有真实数据的 >=50 点）
        sessions = await self.mongo.get_sessions_by_date_range(
            meter_id,
            start_date,
            end_date,
            limit=100,
        )
        # 过滤掉 execute_task 写入的空壳文档
        sessions = [s for s in sessions if (s.get("total_points") or 0) >= 50]

        # 按日期分组，构建每日记录
        daily_records = []
        for doc in sessions:
            collected_at = doc.get("collected_at")
            day_str = collected_at.strftime("%Y-%m-%d") if hasattr(collected_at, "strftime") else str(collected_at)[:10]

            kvp = doc.get("key_value_pairs", {})
            total_points = doc.get("total_points", 0) or 0
            success_points = doc.get("success_points", 0) or 0

            energy_val = (
                kvp.get("Energy.Cumulative A Positive.Value")
                if kvp.get("Energy.Cumulative A Positive.Value") is not None
                else kvp.get("Active energy import.value")
            )
            voltage_val = (
                kvp.get("Instantaneous Data.Instantaneous Voltage L1.Value")
                if kvp.get("Instantaneous Data.Instantaneous Voltage L1.Value") is not None
                else kvp.get("Instantaneous voltage L1.value")
            )
            current_val = (
                kvp.get("Instantaneous Data.Instantaneous Current L1.Value")
                if kvp.get("Instantaneous Data.Instantaneous Current L1.Value") is not None
                else kvp.get("Instantaneous current L1.value")
            )
            power_val = (
                kvp.get("Instantaneous Data.Instantaneous active power (+P) Total")
                if kvp.get("Instantaneous Data.Instantaneous active power (+P) Total") is not None
                else kvp.get("Instantaneous active import power.value")
            )

            completeness = round(success_points / total_points * 100, 1) if total_points > 0 else 0

            daily_records.append(
                {
                    "date": day_str,
                    "collected_at": (
                        collected_at.strftime("%Y-%m-%d %H:%M:%S")
                        if hasattr(collected_at, "strftime")
                        else str(collected_at)
                    ),
                    "total_energy": float(energy_val) if energy_val is not None else 0,
                    "voltage_l1": float(voltage_val) if voltage_val is not None else None,
                    "current_l1": float(current_val) if current_val is not None else None,
                    "power_total": float(power_val) if power_val is not None else None,
                    "total_points": total_points,
                    "success_points": success_points,
                    "completeness": completeness,
                    "status": doc.get("status", ""),
                }
            )

        # 按日期排序（旧→新）
        daily_records.sort(key=lambda x: x["date"])

        # 计算每日增量
        for i in range(len(daily_records)):
            if i > 0:
                prev_energy = daily_records[i - 1]["total_energy"]
                curr_energy = daily_records[i]["total_energy"]
                daily_records[i]["daily_increase"] = round(curr_energy - prev_energy, 2)
            else:
                daily_records[i]["daily_increase"] = 0

        # 趋势图数据
        trend_labels = [r["date"] for r in daily_records]
        trend_values = [r["daily_increase"] for r in daily_records]
        energy_values = [r["total_energy"] for r in daily_records]

        # 汇总
        increases = [r["daily_increase"] for r in daily_records if r["daily_increase"] > 0]
        avg_increase = round(sum(increases) / len(increases), 2) if increases else 0
        total_increase = round(sum(increases), 2) if increases else 0
        demo = len(daily_records) == 0

        # 获取最新一条的详细信息
        latest_energy = {}
        latest_instantaneous = {}
        latest_clock = {}
        latest_events = []
        latest_profiles = []
        if not demo:
            latest_energy = await self.mongo.get_energy(meter_id)
            latest_instantaneous = await self.mongo.get_instantaneous(meter_id)
            latest_clock = await self.mongo.get_clock_status(meter_id)
            latest_events = await self.mongo.get_events(meter_id)
            latest_profiles = await self.mongo.get_profile_completeness(meter_id)

        return {
            "meter_id": meter_id,
            "meter_name": meter.meter_name,
            "serial_number": meter.serial_number,
            "date_from": start_date.strftime("%Y-%m-%d"),
            "date_to": end_date.strftime("%Y-%m-%d"),
            "daily_records": daily_records,
            "energy_trend": {
                "labels": trend_labels,
                "increases": trend_values,
                "cumulative": energy_values,
            },
            "summary": {
                "days_collected": len(daily_records),
                "avg_daily_increase": avg_increase,
                "total_increase": total_increase,
                "latest_energy": float(latest_energy.get("cumulative_positive", 0)) if latest_energy else 0,
                "demo": demo,
            },
            "latest": {
                "instantaneous": latest_instantaneous,
                "clock": latest_clock,
                "events_count": len(latest_events),
                "profiles": [
                    {
                        "name": p["name"],
                        "completeness": p["completeness"],
                        "expected": p["expected"],
                        "actual": p["actual"],
                    }
                    for p in latest_profiles
                ],
            },
        }

    async def get_project_meters(self, project_id: int | None = None) -> list[dict]:
        """获取项目下有采集数据的电表列表。

        从 MongoDB 查找有采集文档的 meter_id，
        用 MongoDB 中的真实序列号覆盖 PG 的占位序列号。
        """
        from app.models.project import Project

        match: dict = {"total_points": {"$gte": 50}}
        if project_id is not None:
            match["project_id"] = project_id

        # 从 Mongo 获取 meter_id → 真实序列号映射
        cursor = self.mongo.col.find(match, {"meter_id": 1, "meter_serial": 1, "_id": 0})
        docs = await cursor.to_list(length=500)

        meter_serials: dict[int, str] = {}
        for doc in docs:
            mid = doc.get("meter_id")
            if mid and isinstance(mid, int) and mid > 0:
                serial = doc.get("meter_serial")
                if serial and mid not in meter_serials:
                    meter_serials[mid] = str(serial)

        if not meter_serials:
            return []

        result = await self.db.execute(select(Meter).where(Meter.id.in_(meter_serials.keys())).order_by(Meter.id))
        meters = result.scalars().all()

        projects: dict[int, str] = {}
        if meters:
            proj_result = await self.db.execute(select(Project))
            projects = {p.id: p.name for p in proj_result.scalars()}

        return [
            {
                "id": m.id,
                "meter_name": m.meter_name,
                "serial_number": meter_serials.get(m.id, m.serial_number),
                "project_id": m.project_id,
                "project_name": projects.get(m.project_id, ""),
                "status": m.current_status,
            }
            for m in meters
        ]

    @staticmethod
    def _aggregate_to_hourly(load_profile: list[dict]) -> list[float]:
        """将 96 点（15min）负荷曲线聚合为 24h 用电。"""
        hourly = [0.0] * 24
        for point in load_profile:
            hour = point.get("index", 0) * 15 // 60
            if 0 <= hour < 24:
                hourly[hour] += point.get("interval_delta", 0)
        return hourly

    @staticmethod
    def _count_events(events: list[dict]) -> dict:
        """统计事件分类数。"""
        counts = {"standard": 0, "theft": 0, "communication": 0, "prepayment": 0}
        for e in events:
            name = e.get("name", "").lower()
            if "theft" in name or "tamper" in name or "magnet" in name:
                counts["theft"] += 1
            elif "comm" in name or "timeout" in name or "disconnect" in name:
                counts["communication"] += 1
            elif "prepay" in name or "credit" in name or "recharge" in name:
                counts["prepayment"] += 1
            else:
                counts["standard"] += 1
        return counts

    @staticmethod
    def _extract_abnormal(events: list[dict], profiles: list[dict]) -> list[dict]:
        """提取异常数据列表。"""
        abnormal = []
        for e in events:
            name = e.get("name", "")
            name_lower = name.lower()
            severity = (
                "critical" if any(k in name_lower for k in ["theft", "tamper", "magnet", "power_down"]) else "warning"
            )
            abnormal.append(
                {
                    "time": e.get("timestamp", ""),
                    "type": name,
                    "description": f"事件码: {e.get('code', 'N/A')}",
                    "severity": severity,
                }
            )
        # 检查 profile 完整性异常
        for p in profiles:
            if p["completeness"] < 95:
                abnormal.append(
                    {
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "type": p["name"],
                        "description": f"完整率 {p['completeness']}%，缺失 {p['expected'] - p['actual']} 条",
                        "severity": "warning",
                    }
                )
        return abnormal

    # ═════════════════════════════════════════════════════════════════════
    #  2. 多表对比 POST /analysis/compare
    # ═════════════════════════════════════════════════════════════════════

    async def compare_meters(
        self,
        meter_ids: list[int],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """多表对比分析。"""
        series = []
        metrics = []
        all_energies = []
        x_axis_ref = []

        for meter_id in meter_ids:
            meter = await self.db.get(Meter, meter_id)
            if not meter:
                continue

            energy = await self.mongo.get_energy(meter_id)
            instantaneous = await self.mongo.get_instantaneous(meter_id)
            daily_billing = await self.mongo.get_daily_billing(meter_id, days=7)
            profile_completeness = await self.mongo.get_profile_completeness(meter_id)

            cumulative = energy.get("cumulative_positive")
            total_energy = float(cumulative) if cumulative is not None else 0
            all_energies.append(total_energy)

            # 从 daily_billing 提取趋势数据
            trend_data = [d["cumulative_energy"] or 0 for d in reversed(daily_billing)]
            if not x_axis_ref and daily_billing:
                x_axis_ref = [
                    d["raw_timestamp"].split(" ")[0] if d.get("raw_timestamp") else f"Day {i+1}"
                    for i, d in enumerate(reversed(daily_billing))
                ]

            series.append({"name": meter.meter_name, "data": trend_data})

            # 完整性
            avg_completeness = (
                sum(p["completeness"] for p in profile_completeness) / len(profile_completeness)
                if profile_completeness
                else 100
            )

            # 最大需量（从瞬时量取）
            max_demand = 0
            for key, val in instantaneous.items():
                if "power" in key.lower() and "total" in key.lower():
                    if isinstance(val, (int, float)):
                        max_demand = max(max_demand, val)

            daily_avg = total_energy / 7 if total_energy > 0 else 0

            # 异常标记
            anomaly_flags = []
            if avg_completeness < 95:
                anomaly_flags.append("数据不完整")
            clock = await self.mongo.get_clock_status(meter_id)
            if isinstance(clock.get("deviation"), (int, float)) and abs(clock["deviation"]) >= 60:
                anomaly_flags.append("时钟偏差")
            anomaly_str = "、".join(anomaly_flags) if anomaly_flags else "无"

            metrics.append(
                {
                    "meter_name": meter.meter_name,
                    "total_energy": round(total_energy, 2),
                    "daily_avg": round(daily_avg, 2),
                    "max_demand": round(max_demand, 2),
                    "deviation_rate": 0,  # 下方计算
                    "completeness": round(avg_completeness, 1),
                    "anomaly_flags": anomaly_str,
                }
            )

        # 计算偏差率（相对于平均值）
        avg_energy = sum(all_energies) / len(all_energies) if all_energies else 0
        for m in metrics:
            if avg_energy > 0:
                m["deviation_rate"] = round((m["total_energy"] - avg_energy) / avg_energy * 100, 2)

        # x_axis
        if not x_axis_ref:
            x_axis_ref = [f"Day {i+1}" for i in range(7)]

        today_total = sum(all_energies)
        # 从 daily_billing 数据计算真实的昨日总电能
        yesterday_total = 0
        for meter_id in meter_ids:
            daily = await self.mongo.get_daily_billing(meter_id, days=2)
            if len(daily) >= 2:
                yesterday_total += float(daily[1].get("cumulative_energy", 0) or 0)
        dev_rate = round((today_total - yesterday_total) / yesterday_total * 100, 2) if yesterday_total > 0 else 0

        return {
            "summary": {
                "today_total": round(today_total, 2),
                "yesterday_total": round(yesterday_total, 2),
                "deviation_rate": dev_rate,
                "anomaly_count": sum(1 for m in metrics if m["anomaly_flags"] != "无"),
            },
            "series": series,
            "x_axis": x_axis_ref,
            "metrics": metrics,
        }

    # ═════════════════════════════════════════════════════════════════════
    #  3. 一致性检查 GET /analysis/consistency
    # ═════════════════════════════════════════════════════════════════════

    async def get_consistency(self, project_id: int | None = None) -> dict:
        """PG col_session vs MongoDB 文档一致性检查。"""
        # 查 PG 中所有有采集记录的电表
        stmt = (
            select(
                CollectionSession.meter_id,
                Meter.serial_number,
                Meter.meter_name,
                func.count(CollectionSession.id).label("pg_count"),
                func.max(CollectionSession.started_at).label("last_pg_time"),
            )
            .join(Meter, CollectionSession.meter_id == Meter.id)
            .group_by(CollectionSession.meter_id, Meter.serial_number, Meter.meter_name)
        )
        if project_id is not None:
            stmt = stmt.where(CollectionSession.project_id == project_id)

        result = await self.db.execute(stmt)
        pg_rows = result.all()

        items = []
        for row in pg_rows:
            meter_id = row[0]
            serial = row[1] or ""
            meter_name = row[2] or ""
            pg_count = row[3] or 0

            # 统计 Mongo 中该电表的文档数
            try:
                mongo_count = await self.mongo.count_sessions(meter_id=meter_id)
            except Exception:
                mongo_count = 0

            # 计算缺失（PG 有记录但 Mongo 缺文档）
            missing = max(0, pg_count - mongo_count)

            items.append(
                {
                    "serial_number": serial,
                    "device_name": meter_name,
                    "project_name": "",  # 可后续填充
                    "pg_task_days": pg_count,
                    "influxdb_data_days": mongo_count,  # 前端字段名保持兼容（实际是 Mongo）
                    "missing_days": missing,
                    "last_check_time": row[4].strftime("%Y-%m-%d %H:%M:%S") if row[4] else None,
                }
            )

        return {"items": items, "total": len(items)}

    async def trigger_consistency_check(self, project_id: int | None = None) -> dict:
        """触发一致性检查（重新扫描）。"""
        result = await self.get_consistency(project_id)
        total = result["total"]
        missing = sum(1 for i in result["items"] if i["missing_days"] > 0)
        return {
            "success": True,
            "message": f"一致性检查完成: 共 {total} 台设备, {missing} 台存在数据不一致",
            "result": result,
        }

    # ═════════════════════════════════════════════════════════════════════
    #  4. 数据质量 GET /analysis/data-quality
    # ═════════════════════════════════════════════════════════════════════

    async def get_data_quality(
        self,
        page: int = 1,
        page_size: int = 20,
        meter_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        min_score: float | None = None,
        project_id: int | None = None,
    ) -> dict:
        """数据质量分析（来源 PG col_data_quality）。"""
        query = select(DataQuality).order_by(DataQuality.stat_date.desc())
        count_stmt = select(func.count()).select_from(DataQuality)

        if meter_id:
            query = query.where(DataQuality.meter_id == meter_id)
            count_stmt = count_stmt.where(DataQuality.meter_id == meter_id)
        if start_date:
            query = query.where(DataQuality.stat_date >= start_date)
            count_stmt = count_stmt.where(DataQuality.stat_date >= start_date)
        if end_date:
            query = query.where(DataQuality.stat_date <= end_date)
            count_stmt = count_stmt.where(DataQuality.stat_date <= end_date)
        if min_score is not None:
            query = query.where(DataQuality.quality_score >= min_score)
            count_stmt = count_stmt.where(DataQuality.quality_score >= min_score)

        total = (await self.db.execute(count_stmt)).scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        # 关联电表名
        meter_ids = {item.meter_id for item in items}
        meters = {}
        if meter_ids:
            meter_result = await self.db.execute(select(Meter).where(Meter.id.in_(meter_ids)))
            meters = {m.id: m for m in meter_result.scalars()}

        items_list = []
        for item in items:
            m = meters.get(item.meter_id)
            score = float(item.quality_score) if item.quality_score else 0
            items_list.append(
                {
                    "id": item.id,
                    "meter_name": m.meter_name if m else "",
                    "stat_date": item.stat_date.isoformat() if item.stat_date else None,
                    "total_points": item.total_points,
                    "success_points": item.success_points,
                    "failed_points": item.failed_points,
                    "quality_score": round(score, 1),
                    "abnormal_count": item.abnormal_count,
                    "first_collect_time": item.first_collect_time.strftime("%Y-%m-%d %H:%M:%S")
                    if item.first_collect_time
                    else None,
                    "last_collect_time": item.last_collect_time.strftime("%Y-%m-%d %H:%M:%S")
                    if item.last_collect_time
                    else None,
                }
            )

        # summary
        all_scores = [i["quality_score"] for i in items_list if i["quality_score"]]
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        total_devices = len({i["meter_name"] for i in items_list})
        abnormal_devices = len([i for i in items_list if i["quality_score"] < 80])
        total_pts = sum(i["total_points"] for i in items_list)
        success_pts = sum(i["success_points"] for i in items_list)
        success_rate = round(success_pts / total_pts * 100, 1) if total_pts > 0 else 0

        # trend（近7天平均分）
        trend = await self._build_quality_trend()

        return {
            "items": items_list,
            "total": total,
            "summary": {
                "avg_quality_score": round(avg_score, 1),
                "total_devices": total_devices,
                "abnormal_devices": abnormal_devices,
                "success_rate": success_rate,
            },
            "trend": trend,
        }

    async def _build_quality_trend(self) -> list[dict]:
        """构建近 7 天数据质量趋势。"""
        end = date.today()
        start = end - timedelta(days=6)

        stmt = (
            select(
                DataQuality.stat_date,
                func.avg(DataQuality.quality_score).label("avg_score"),
            )
            .where(DataQuality.stat_date >= start)
            .where(DataQuality.stat_date <= end)
            .group_by(DataQuality.stat_date)
            .order_by(DataQuality.stat_date)
        )
        result = await self.db.execute(stmt)
        rows = {r[0]: float(r[1]) if r[1] else 0 for r in result.all()}

        trend = []
        cur = start
        while cur <= end:
            score = rows.get(cur, 0)
            trend.append({"date": cur.isoformat(), "avg_score": round(score, 1)})
            cur += timedelta(days=1)
        return trend

    # ═════════════════════════════════════════════════════════════════════
    #  5. 分析报告 GET /analysis/reports
    # ═════════════════════════════════════════════════════════════════════

    async def get_reports(self, project_id: int | None = None) -> dict:
        """分析报告列表（来源 PG lab_test_report）。"""
        from app.models.test import TestReport

        stmt = select(TestReport).order_by(TestReport.id.desc())
        if project_id is not None:
            stmt = stmt.where(TestReport.project_id == project_id)

        result = await self.db.execute(stmt)
        reports = result.scalars().all()

        items = [
            {
                "id": r.id,
                "title": r.report_name or f"报告 #{r.id}",
                "project_id": r.project_id,
                "type": "type_approval",
                "status": r.status or "completed",
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            }
            for r in reports
        ]
        return {"items": items, "total": len(items)}

    # ═════════════════════════════════════════════════════════════════════
    #  导出辅助方法
    # ═════════════════════════════════════════════════════════════════════

    def export_daily_csv(self, data: dict) -> bytes:
        """将日线分析数据导出为 CSV。"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["小时", "正向有功电能(kWh)"])
        for i, e in enumerate(data.get("energy_trend", [])):
            writer.writerow([f"{i:02d}:00", e.get("positive_active", "0")])
        writer.writerow([])
        writer.writerow(["统计项", "值"])
        ed = data.get("energy_data", {})
        writer.writerow(["总电能(kWh)", ed.get("total_energy", "")])
        writer.writerow(["日增量(kWh)", ed.get("daily_increase", "")])
        writer.writerow(["增长率(%)", ed.get("increase_rate", "")])
        return output.getvalue().encode("utf-8-sig")

    def export_data_quality_csv(self, data: dict) -> bytes:
        """将数据质量分析导出为 CSV。"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["设备名", "日期", "总点数", "成功点数", "失败点数", "质量评分", "异常数"])
        for item in data.get("items", []):
            writer.writerow(
                [
                    item.get("meter_name", ""),
                    item.get("stat_date", ""),
                    item.get("total_points", 0),
                    item.get("success_points", 0),
                    item.get("failed_points", 0),
                    item.get("quality_score", 0),
                    item.get("abnormal_count", 0),
                ]
            )
        return output.getvalue().encode("utf-8-sig")
