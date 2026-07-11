"""OBIS 模板种子数据 — 从 Excel 配置模板导入 3 套系统模板。

模板来源: MeterSchedulerFusion/meterParams/模板 Excel 文件
  - P2PObis sheet   → p2p_signal (14 项信号指标)
  - MeteringObis sheet → metering_full (全量抄读)
  - DCUObis sheet   → dcu_archive (2 项)

可独立运行: python -m app.db.seed_obis_templates
也可在主 seed 中调用: from app.db.seed_obis_templates import seed_obis_templates
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.obis_template import DataPointTemplate, ObisTemplate

logger = logging.getLogger(__name__)

# ============================================================
# P2P 信号指标模板 (14 项，来自 Excel P2PObis sheet)
# ============================================================
P2P_OBIS_ITEMS: list[tuple[str, str, str, int, int]] = [
    ("Signal", "Load profile-buffer", "1-0:99.1.0.255", 7, 2),
    ("Signal", "Signal indicate(CSQ)", "0-1:94.31.6.255", 1, 2),
    ("Signal", "RSRP", "0-1:94.31.7.255", 1, 2),
    ("Signal", "RSRQ", "0-1:94.31.8.255", 1, 2),
    ("Signal", "RSSI", "0-1:94.31.9.255", 1, 2),
    ("Signal", "SNR", "0-1:94.31.10.255", 1, 2),
    ("Signal", "PCI", "0-1:94.31.11.255", 1, 2),
    ("Signal", "EARFCN", "0-1:94.31.13.255", 1, 2),
    ("GSMDiagnostic", "Operator", "0-0:25.6.0.255", 47, 2),
    ("GSMDiagnostic", "Status", "0-0:25.6.0.255", 47, 3),
    ("GSMDiagnostic", "CS attachment", "0-0:25.6.0.255", 47, 4),
    ("GSMDiagnostic", "PS status", "0-0:25.6.0.255", 47, 5),
    ("GSMDiagnostic", "Cell info", "0-0:25.6.0.255", 47, 6),
    ("GSMDiagnostic", "Capture time", "0-0:25.6.0.255", 47, 8),
]

# ============================================================
# DCU 档案模板 (2 项，来自 Excel DCUObis sheet)
# ============================================================
DCU_OBIS_ITEMS: list[tuple[str, str, str, int, int]] = [
    ("Archive", "Archive Management", "0-0:21.0.1.255", 1, 2),
    ("Archive", "Device name", "0-0:42.0.0.255", 1, 2),
]


def _build_metering_items() -> list[tuple[str, str, str, int, int]]:
    """构建基表全量抄读模板明细（来自 Excel MeteringObis sheet）。

    返回 (module, point_name, obis_code, class_id, attribute_id) 列表。
    """
    items: list[tuple[str, str, str, int, int]] = []

    # ── DeviceID ──
    items += [
        ("DeviceID", "Device ID&value", "0.0.96.1.0.255", 1, 2),
        ("DeviceID", "LogicalName&value", "0.0.42.0.0.255", 1, 2),
    ]

    # ── Clock (8 attributes) ──
    for attr, label in [
        (2, "time"),
        (3, "time_zone"),
        (4, "status"),
        (5, "daylights_savings_begin"),
        (6, "daylights_savings_end"),
        (7, "daylights_savings_deviation"),
        (8, "daylights_savings_enabled"),
    ]:
        items.append(("Clock", f"Clock&{label}", "0.0.1.0.0.255", 8, attr))

    # ── Tariff ──
    items += [
        ("Tariff", "Activity calendar&season_profile_active", "0.0.13.0.0.255", 20, 3),
        ("Tariff", "Activity calendar&week_profile_table_active", "0.0.13.0.0.255", 20, 4),
        ("Tariff", "Activity calendar&day_profile_table_active", "0.0.13.0.0.255", 20, 5),
        ("Tariff", "Activity calendar&season_profile_passive", "0.0.13.0.0.255", 20, 7),
        ("Tariff", "Activity calendar&week_profile_table_passive", "0.0.13.0.0.255", 20, 8),
        ("Tariff", "Activity calendar&day_profile_table_passive", "0.0.13.0.0.255", 20, 9),
        ("Tariff", "Special Days Table&entries", "0.0.11.0.0.255", 11, 2),
        ("Tariff", "Currently active tariff&value", "0.0.96.14.0.255", 1, 2),
    ]

    # ── DisconnectControl ──
    for prefix, addr in [("0.0", "0.0.96.3.10.255"), ("0.1", "0.1.96.3.10.255"), ("0.2", "0.2.96.3.10.255")]:
        label = "Disconnect control" if prefix == "0.0" else ("Relay control" if prefix == "0.1" else "Relay contro2")
        items.append(("DisconnectControl", f"{label}&output_state", addr, 70, 2))
        items.append(("DisconnectControl", f"{label}&control_state", addr, 70, 3))

    # ── Billing Profiles (Monthly/Daily, 7 attrs each) ──
    for module, addr, sched_addr in [
        ("MonthlyBilling", "0.0.98.1.0.255", "0.0.15.0.0.255"),
        ("DailyBilling", "0.0.98.2.0.255", "0.0.15.1.0.255"),
    ]:
        for attr, label in [
            (2, "buffer"),
            (3, "capture_objects"),
            (4, "capture_period"),
            (5, "sort_method"),
            (6, "sort_object"),
            (7, "entries_in_use"),
            (8, "profile_entries"),
        ]:
            items.append((module, f"{module} Profile&{label}", addr, 7, attr))
        items.append((module, f"{module} Profile&schedule", sched_addr, 22, 4))

    # ── Load Profiles (1/2, 7 attrs each) ──
    for module, addr in [("LoadProfile1", "1.0.99.1.0.255"), ("LoadProfile2", "1.0.99.2.0.255")]:
        for attr, label in [
            (2, "buffer"),
            (3, "capture_objects"),
            (4, "capture_period"),
            (5, "sort_method"),
            (6, "sort_object"),
            (7, "entries_in_use"),
            (8, "profile_entries"),
        ]:
            items.append((module, f"{module}&{label}", addr, 7, attr))

    # ── PowerQualityProfile ──
    pq_addr = "1.0.99.14.0.255"
    for attr, label in [
        (2, "buffer"),
        (3, "capture_objects"),
        (4, "capture_period"),
        (5, "sort_method"),
        (6, "sort_object"),
        (7, "entries_in_use"),
        (8, "profile_entries"),
    ]:
        items.append(("PowerQualityProfile", f"Power Quality Profile&{label}", pq_addr, 7, attr))

    # ── Energy: Active/Reactive/Apparent import+export, rate 0-6 ──
    # format: (energy_type, direction, obis_var, rate_range)
    energy_specs = [
        # (var_code, label_prefix, rates)
        (1, "Active energy import", range(0, 7)),  # 1.0.1.8.x.255
        (2, "Active energy export", range(0, 7)),  # 1.0.2.8.x.255
        (3, "Reactive energy import", range(0, 7)),  # 1.0.3.8.x.255
        (4, "Reactive energy export", range(0, 7)),  # 1.0.4.8.x.255
        (5, "Reactive energy QI", range(0, 7)),  # 1.0.5.8.x.255
        (6, "Reactive energy QII", range(0, 7)),  # 1.0.6.8.x.255
        (7, "Reactive energy QIII", range(0, 7)),  # 1.0.7.8.x.255
        (8, "Reactive energy QIV", range(0, 7)),  # 1.0.8.8.x.255
        (15, "Absolute energy |+A|+|-A|", range(0, 7)),  # 1.0.15.8.x.255
        (16, "Net Energy |+A|-|-A|", range(0, 7)),  # 1.0.16.8.x.255
    ]
    for var_code, label, rates in energy_specs:
        for rate in rates:
            suffix = f".{rate}" if rate > 0 else ""
            rate_label = f" rate {rate}" if rate > 0 else ""
            addr = f"1.0.{var_code}.8{suffix}.255"
            items.append(("Energy", f"{label}{rate_label}&value", addr, 3, 2))
            items.append(("Energy", f"{label}{rate_label}&scaler_unit", addr, 3, 3))

    # ── Instantaneous: Current/Voltage/Power/PowerFactor/PhaseAngle ──
    inst_specs = [
        (31, "Instantaneous current L1", "A"),
        (51, "Instantaneous current L2", "A"),
        (71, "Instantaneous current L3", "A"),
        (32, "Instantaneous voltage L1", "V"),
        (52, "Instantaneous voltage L2", "V"),
        (72, "Instantaneous voltage L3", "V"),
    ]
    for var, label, _unit in inst_specs:
        addr = f"1.0.{var}.7.0.255"
        items.append(("Instantaneous", f"{label}&value", addr, 3, 2))
        items.append(("Instantaneous", f"{label}&scaler_unit", addr, 3, 3))

    # Power: active/reactive/apparent × import/export × total/L1/L2/L3
    power_specs = [
        # (var, direction, phases) — phases[0] is total
        (1, "active import", [None, 21, 41, 61]),
        (2, "active export", [None, 22, 42, 62]),
        (3, "reactive import", [None, 23, 43, 63]),
        (4, "reactive export", [None, 24, 44, 64]),
        (9, "apparent import", [None, 29, 49, 69]),
        (10, "apparent export", [None, 30, 50, 70]),
    ]
    for base_var, direction, phases in power_specs:
        for idx, phase_var in enumerate(phases):
            var = phase_var if phase_var else base_var
            label = f"Instantaneous {direction} power" + (f" L{idx}" if idx > 0 else "")
            addr = f"1.0.{var}.7.0.255"
            items.append(("Instantaneous", f"{label}&value", addr, 3, 2))
            items.append(("Instantaneous", f"{label}&scaler_unit", addr, 3, 3))

    # Power Factor (total + L1-L3)
    for var, label in [(13, ""), (33, " L1"), (53, " L2"), (73, " L3")]:
        addr = f"1.0.{var}.7.0.255"
        items.append(("Instantaneous", f"Instantaneous Power Factor{label}&value", addr, 3, 2))
        items.append(("Instantaneous", f"Instantaneous Power Factor{label}&scaler_unit", addr, 3, 3))

    # Phase Angles
    phase_angle_specs = [
        (81, 40, "U(L1) to I(L1)"),
        (81, 51, "U(L2) to I(L2)"),
        (81, 62, "U(L3) to I(L3)"),
        (81, 10, "U(L1) to U(L1)"),
        (81, 20, "U(L2) to U(L2)"),
        (81, 21, "U(L3) to U(L3)"),
    ]
    for var, idx, label in phase_angle_specs:
        addr = f"1.0.{var}.7.{idx}.255"
        items.append(("Instantaneous", f"Phase Angle {label}&value", addr, 3, 2))
        items.append(("Instantaneous", f"Phase Angle {label}&scaler_unit", addr, 3, 3))

    # Battery Voltage
    items.append(("Instantaneous", "Voltage of Battery&value", "0.0.96.6.3.255", 3, 2))
    items.append(("Instantaneous", "Voltage of Battery&scaler_unit", "0.0.96.6.3.255", 3, 3))

    # ── AverageValues ──
    avg_specs = [
        (32, 24, "Current Average Voltage L1"),
        (52, 24, "Current Average Voltage L2"),
        (72, 24, "Current Average Voltage L3"),
        (31, 24, "Current Average Current L1"),
        (51, 24, "Current Average Current L2"),
        (71, 24, "Current Average Current L3"),
        (13, 24, "Current Average Power Factor"),
        (33, 24, "Current Average Power Factor L1"),
        (53, 24, "Current Average Power Factor L2"),
        (73, 24, "Current Average Power Factor L3"),
        (14, 24, "Current Average Frequency"),
        (32, 25, "Last Average Voltage L1"),
        (52, 25, "Last Average Voltage L2"),
        (72, 25, "Last Average Voltage L3"),
        (31, 25, "Last Average Current L1"),
        (51, 25, "Last Average Current L2"),
        (71, 25, "Last Average Current L3"),
        (13, 25, "Last Average Power Factor"),
        (33, 25, "Last Average Power Factor L1"),
        (53, 25, "Last Average Power Factor L2"),
        (73, 25, "Last Average Power Factor L3"),
        (14, 25, "Last Average Frequency"),
    ]
    for var, meas, label in avg_specs:
        addr = f"1.0.{var}.{meas}.0.255"
        items.append(("AverageValues", f"{label}&value", addr, 3, 2))
        items.append(("AverageValues", f"{label}&scaler_unit", addr, 3, 3))

    # ── Status ──
    items += [
        ("Status", "Error register", "0.0.97.97.0.255", 1, 2),
        ("Status", "Alarm register 1", "0.0.97.98.0.255", 1, 2),
        ("Status", "Alarm register 2", "0.0.97.98.1.255", 1, 2),
    ]

    # ── Event Logs ──
    event_specs = [
        ("0.0.99.98.0.255", "Standard Event Log"),
        ("0.0.99.98.1.255", "Fraud detection Event Log"),
        ("0.0.99.98.5.255", "Communication Event Log"),
        ("0.0.99.98.4.255", "Quality Event Log"),
        ("0.0.99.98.11.255", "Limit Change Event Log"),
        ("0.0.99.98.2.255", "Disconnect control Event Log"),
        ("1.0.99.97.0.255", "Long Power Failure Event Log"),
        ("1.0.99.97.1.255", "Short Power Failure Event Log"),
    ]
    for addr, label in event_specs:
        items.append(("Event", f"{label}&Capture Objects", addr, 7, 3))
        items.append(("Event", f"{label}&Buffer", addr, 7, 2))

    return _deduplicate(items)


def _deduplicate(items: list[tuple]) -> list[tuple]:
    """去重：同一 (module, point_name, obis_code, class_id, attribute_id) 只保留第一条。

    注意：同一 obis_code 可以有不同 attribute_id（如 Clock 的 attr 2-8），
    这些不是重复项，都需要保留。sort_order 在插入时按列表索引赋值，保证唯一。
    """
    seen: set[tuple] = set()
    result = []
    for item in items:
        key = item  # (module, point_name, obis_code, class_id, attribute_id)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


METERING_OBIS_ITEMS = _build_metering_items()


async def seed_obis_templates(session: AsyncSession) -> dict[str, int]:
    """创建 3 套系统 OBIS 模板。

    幂等：如模板已存在则跳过。
    返回 {template_name: item_count}。
    """
    result: dict[str, int] = {}

    templates_to_create = [
        ("p2p_signal", "electric_meter", "p2p", "P2P 信号指标模板（14项，来自 Excel P2PObis sheet）", P2P_OBIS_ITEMS),
        (
            "metering_full",
            "electric_meter",
            "metering",
            "基表全量抄读模板（来自 Excel MeteringObis sheet）",
            METERING_OBIS_ITEMS,
        ),
        ("dcu_archive", "electric_meter", "dcu", "DCU 档案抄读模板（2项，来自 Excel DCUObis sheet）", DCU_OBIS_ITEMS),
    ]

    for name, dev_type, category, desc, items in templates_to_create:
        existing = await session.execute(select(ObisTemplate).where(ObisTemplate.name == name))
        if existing.scalar_one_or_none() is not None:
            logger.info("模板 %s 已存在，跳过", name)
            continue

        tpl = ObisTemplate(
            name=name,
            device_type=dev_type,
            task_category=category,
            description=desc,
            is_system=True,
            version=1,
        )
        session.add(tpl)
        await session.flush()

        for idx, (module, point_name, obis, cls_id, attr_id) in enumerate(items):
            session.add(
                DataPointTemplate(
                    template_id=tpl.id,
                    device_type=dev_type,
                    module=module,
                    point_name=point_name,
                    address=obis,
                    data_type="numeric",
                    is_read=True,
                    sort_order=idx,
                    protocol_params={"class_id": cls_id, "attribute_id": attr_id},
                )
            )

        result[name] = len(items)
        logger.info("创建模板 %s: %d 项", name, len(items))

    await session.flush()
    return result


if __name__ == "__main__":
    import asyncio

    from app.core.database import AsyncSessionLocal

    async def main():
        async with AsyncSessionLocal() as session:
            counts = await seed_obis_templates(session)
            await session.commit()
            print(f"OBIS 模板创建完成: {counts}")

    asyncio.run(main())
