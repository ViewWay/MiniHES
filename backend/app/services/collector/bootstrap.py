"""注册初始化 — 启动时注册所有 device × category 组合到 ConfigRegistry。

新增设备/任务类型时在此添加 register 调用。
"""

from __future__ import annotations

from app.schemas.collector_config import (
    CommModuleConfig,
    ConcentratorConfig,
    ElectricMeterConfig,
    GasMeterConfig,
    WaterMeterConfig,
)

from .registry import ConfigRegistration, registry
from .types import DeviceType, TaskCategory

_registered = False


def register_all() -> None:
    """注册所有 device × category 组合（幂等，重复调用安全）"""
    global _registered
    if _registered:
        return

    # ── 电表 × P2P（模块通信测试）──
    registry.register(
        ConfigRegistration(
            device_type=DeviceType.ELECTRIC_METER,
            task_category=TaskCategory.P2P,
            config_schema=ElectricMeterConfig,
            defaults={
                "communication": "HDLC",
                "batch": 6,
                "read_strategy": "by_entry",
                "is_unlock": True,
            },
            obis_template_name="p2p_signal",
            description="电表 P2P — 模块信号通信测试（14项信号指标）",
        )
    )

    # ── 电表 × Metering（基表全量抄读）──
    registry.register(
        ConfigRegistration(
            device_type=DeviceType.ELECTRIC_METER,
            task_category=TaskCategory.METERING,
            config_schema=ElectricMeterConfig,
            defaults={
                "communication": "HDLC",
                "batch": 6,
                "read_strategy": "by_range",
                "data_recapture": True,
            },
            obis_template_name="metering_full",
            description="电表基表 — 全量抄读（345项 OBIS）",
        )
    )

    # ── 电表 × DCU（集中器抄读）──
    registry.register(
        ConfigRegistration(
            device_type=DeviceType.ELECTRIC_METER,
            task_category=TaskCategory.DCU,
            config_schema=ElectricMeterConfig,
            defaults={
                "communication": "FEP",
                "read_strategy": "full",
            },
            obis_template_name="dcu_archive",
            description="电表 DCU — 集中器档案抄读",
        )
    )

    # ── 水表 × Modbus ──
    registry.register(
        ConfigRegistration(
            device_type=DeviceType.WATER_METER,
            task_category=TaskCategory.MODBUS_POLL,
            config_schema=WaterMeterConfig,
            defaults={"communication": "Modbus", "batch": 1},
            obis_template_name="water_modbus",
            description="水表 — Modbus 轮询抄读",
        )
    )

    # ── 气表 × Modbus ──
    registry.register(
        ConfigRegistration(
            device_type=DeviceType.GAS_METER,
            task_category=TaskCategory.MODBUS_POLL,
            config_schema=GasMeterConfig,
            defaults={"communication": "Modbus", "batch": 1},
            obis_template_name="gas_modbus",
            description="气表 — Modbus 轮询抄读",
        )
    )

    # ── 集中器 × MQTT ──
    registry.register(
        ConfigRegistration(
            device_type=DeviceType.CONCENTRATOR,
            task_category=TaskCategory.MQTT_SUBSCRIBE,
            config_schema=ConcentratorConfig,
            defaults={"communication": "MQTT"},
            obis_template_name=None,
            description="集中器 — MQTT 订阅上报数据",
        )
    )

    # ── 通信模块 × AT 命令测试 ──
    registry.register(
        ConfigRegistration(
            device_type=DeviceType.COMM_MODULE,
            task_category=TaskCategory.COMMAND_TEST,
            config_schema=CommModuleConfig,
            defaults={"communication": "AT"},
            obis_template_name="module_at_commands",
            description="通信模块 — AT 命令测试",
        )
    )

    _registered = True
