"""采集任务配置 Schema — 对应 Excel Configuration sheet。

设计决策 2-C：单 schema 全包含，字段带 tags metadata 标注适用 task_category。
前端根据 tags 动态显隐字段，后端不做条件必填校验。

tags 值为 task_category 字符串列表，如 ["p2p", "metering", "dcu"]。
字段无 tags 时默认全部任务类型适用。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BaseTaskConfig(BaseModel):
    """所有设备类型共享的公共配置"""

    # ── 通信参数（公共）──
    communication: str = Field("HDLC", description="HDLC/WPDU/FEP/Modbus/MQTT")
    batch: int = Field(6, ge=1, le=100, description="并发抄读表数")
    client_id: int = Field(1, ge=0, le=16, description="DLMS 客户端 SAP")
    timeout: int = Field(30, ge=1, le=600, description="单次超时(秒)")
    retry_times: int = Field(3, ge=0, le=10, description="重试次数")

    is_unlock: bool = Field(True, description="是否解锁")
    data_recapture: bool = Field(False, description="是否补采")

    # ── 网络监控 ──
    is_pcap: bool | None = Field(None, description="Wireshark 监控")
    iface: str | None = Field(None, description="指定网卡")
    log_path: str | None = Field(None, description="日志路径")


class ElectricMeterConfig(BaseTaskConfig):
    """电表配置 — 对应 Excel Configuration sheet 电表参数。

    覆盖 p2p / metering / dcu 三种 task_category。
    字段 json_schema_extra.tags 标注适用的任务类型，前端据此动态显隐。
    """

    # ── 连接方式 ──
    connect_type: Literal["Network", "Serial"] | None = Field(
        None, description="连接方式，默认 HDLC→Serial, WPDU/FEP→Network"
    )

    # ── 抄读策略 ──
    read_strategy: Literal["full", "by_entry", "by_range"] = Field(
        "full",
        json_schema_extra={"tags": ["p2p", "metering", "dcu"]},
    )
    by_entry: int | None = Field(
        None,
        description="按条数抄读, 如 -200/-1",
        json_schema_extra={"tags": ["p2p", "dcu"]},
    )
    by_range: Literal["yesterday", "all", "lastweek"] | None = Field(
        None,
        json_schema_extra={"tags": ["metering", "dcu"]},
    )
    by_range_start: datetime | None = Field(None, description="自定义起始时间")
    by_range_end: datetime | None = Field(None, description="自定义结束时间")
    by_range_period_hours: int | None = Field(None, description="当前时间向前推算周期(h)")

    # ── 安全密钥 ──
    encryption_key: str | None = Field(
        None,
        description="EKey",
        json_schema_extra={"tags": ["p2p", "metering", "dcu"]},
    )
    auth_key: str | None = Field(None, description="AKey")
    lls_key: str | None = Field(None, description="低级安全密钥")
    hls_key: str | None = Field(None, description="高级安全密钥")

    # ── 模块/版本（metering 专用）──
    is_dongle: bool | None = Field(
        None,
        description="蓝牙连接",
        json_schema_extra={"tags": ["metering"]},
    )
    is_check_archive: bool | None = Field(
        None,
        description="FEP 检查档案",
        json_schema_extra={"tags": ["p2p"]},
    )
    app1_id: str | None = Field(
        None,
        description="App1 版本号生产命令",
        json_schema_extra={"tags": ["metering"]},
    )
    app2_id: str | None = Field(
        None,
        description="App2 版本号生产命令",
        json_schema_extra={"tags": ["metering"]},
    )
    module_cmcs_id: str | None = Field(
        None,
        description="模块版本号生产命令",
        json_schema_extra={"tags": ["metering"]},
    )
    identifier: str | None = Field(
        None,
        description="Andromeda 标识 (KFM-03/KFM-01)",
        json_schema_extra={"tags": ["metering"]},
    )

    # ── DCU 专用 ──
    reading_object_obis: str | None = Field(
        None,
        description="抄读状态判断 OBIS (默认 7,1-0:99.1.0.255,2)",
        json_schema_extra={"tags": ["dcu"]},
    )


class WaterMeterConfig(BaseTaskConfig):
    """水表配置（Modbus）— 未来扩展"""

    communication: str = Field("Modbus")
    register_start: int = Field(0, ge=0)
    register_count: int = Field(20, ge=1, le=125)
    function_code: int = Field(3, description="Modbus 功能码: 3=读保持, 4=读输入")
    slave_id: int = Field(1, ge=1, le=247)
    byte_order: Literal["ABCD", "DCBA", "BADC", "CDAB"] = Field("ABCD")


class GasMeterConfig(BaseTaskConfig):
    """气表配置（Modbus / 私有协议）— 未来扩展"""

    communication: str = Field("Modbus")
    register_start: int = Field(0, ge=0)
    register_count: int = Field(10, ge=1, le=125)
    function_code: int = Field(4, description="Modbus 功能码")
    slave_id: int = Field(1, ge=1, le=247)
    byte_order: Literal["ABCD", "DCBA", "BADC", "CDAB"] = Field("ABCD")


class ConcentratorConfig(BaseTaskConfig):
    """集中器配置 — 未来扩展"""

    communication: str = Field("MQTT")
    topic: str | None = Field(None, description="MQTT 订阅主题")
    qos: int = Field(1, ge=0, le=2)
    sub_device_ids: list[int] | None = Field(None, description="下挂电表 ID 列表")


class CommModuleConfig(BaseTaskConfig):
    """通信模块配置 — 未来扩展"""

    communication: str = Field("AT")
    command_set: str | None = Field(None, description="命令集合名称")
