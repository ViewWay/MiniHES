"""数据点模板模型 — 统一表 + JSONB 扩展（方案 A）。

对应设计文档 docs/design/collector-config-model.md。

三张表协作：
    obis_template          — 模板集合（如 metering_full 345 项）
    data_point_template    — 模板明细（统一 address 列 + protocol_params JSONB）
    task_obis_override     — 任务级覆盖（勾选/取消/微调参数）
"""

from __future__ import annotations

import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class ObisTemplate(Base, TimestampMixin):
    """数据点模板 — 一组可复用的抄读数据点定义。

    每个 (device_type, task_category) 组合可有一个或多个模板，
    例如电表 metering 有 metering_full(345项)。
    """

    __tablename__ = "obis_template"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_obis_template_name_version"),
        {"comment": "数据点模板表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    device_type: Mapped[str] = mapped_column(String(30))
    task_category: Mapped[str] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)

    items: Mapped[list[DataPointTemplate]] = relationship(back_populates="template", cascade="all, delete-orphan")


class DataPointTemplate(Base):
    """数据点模板明细 — 统一存储所有设备类型的数据点定义。

    address 列是通用标识：
        电表 → OBIS 码 (如 '1.0.1.8.0.255')
        水表 → Modbus 寄存器地址 (如 '40001')
        模块 → AT 命令 (如 'AT+CSQ')

    protocol_params JSONB 存协议差异参数：
        电表 → {"class_id": 3, "attribute_id": 2}
        水表 → {"function_code": 3, "register_count": 2, "byte_order": "ABCD"}
        模块 → {"command": "AT+CSQ", "parse_rule": "regex", ...}
    """

    __tablename__ = "data_point_template"
    __table_args__ = (
        UniqueConstraint("template_id", "address", "sort_order", name="uq_dpt_template_addr_order"),
        Index("ix_dpt_template", "template_id"),
        Index("ix_dpt_device_type", "device_type"),
        {"comment": "数据点模板明细表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("obis_template.id", ondelete="CASCADE"))
    device_type: Mapped[str] = mapped_column(String(30))

    # ── 通用字段 ──
    module: Mapped[str | None] = mapped_column(String(50), nullable=True)
    point_name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(String(60))
    data_type: Mapped[str] = mapped_column(String(20), default="numeric")
    unit: Mapped[str] = mapped_column(String(20), default="")
    scaler: Mapped[int] = mapped_column(Integer, default=0)
    is_read: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── 协议特有参数（JSONB）──
    protocol_params: Mapped[dict] = mapped_column(JSONB, default=dict)

    template: Mapped[ObisTemplate] = relationship(back_populates="items")


class TaskObisOverride(Base):
    """任务数据点覆盖 — 模板 + 覆盖机制（设计决策 1-A）。

    override 表为空时，任务读模板默认值；
    用户取消某项 → is_selected=False；
    用户微调参数 → custom_params 存覆盖值。
    """

    __tablename__ = "task_obis_override"
    __table_args__ = (
        UniqueConstraint("task_id", "template_item_id", name="uq_task_override_item"),
        Index("ix_task_override_task", "task_id"),
        {"comment": "任务数据点覆盖表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("col_task.id", ondelete="CASCADE"))
    template_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("data_point_template.id", ondelete="CASCADE"))
    is_selected: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
