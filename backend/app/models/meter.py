from __future__ import annotations

import datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class MeterType(Base, TimestampMixin):
    __tablename__ = "dev_meter_type"
    __table_args__ = {"comment": "电表类型表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")

    meters: Mapped[list["Meter"]] = relationship(back_populates="meter_type")


class WireType(Base, TimestampMixin):
    __tablename__ = "dev_wire_type"
    __table_args__ = {"comment": "接线方式表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")


class Meter(Base, TimestampMixin):
    __tablename__ = "dev_meter"
    __table_args__ = {"comment": "电表设备表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    serial_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    meter_name: Mapped[str] = mapped_column(String(100))
    meter_type_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dev_meter_type.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dev_project.id", ondelete="SET NULL"), nullable=True, index=True
    )
    protocol: Mapped[str] = mapped_column(String(20), default="DLMS")
    line_type: Mapped[str] = mapped_column(String(20), default="single_phase")
    manufacturer: Mapped[str] = mapped_column(String(100), default="")
    model: Mapped[str] = mapped_column(String(100), default="")
    firmware_version: Mapped[str] = mapped_column(String(50), default="")
    hardware_version: Mapped[str] = mapped_column(String(50), default="")
    frame_number: Mapped[str] = mapped_column(String(50), default="")
    location: Mapped[str] = mapped_column(String(200), default="")
    current_status: Mapped[str] = mapped_column(String(20), default="in_stock", index=True)
    factory_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    purchase_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    warranty_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True
    )

    project: Mapped["Project | None"] = relationship(back_populates="meters")
    meter_type: Mapped["MeterType | None"] = relationship(back_populates="meters")
    comm: Mapped["MeterComm | None"] = relationship(back_populates="meter", uselist=False, cascade="all, delete-orphan")
    snapshot: Mapped["MeterSnapshot | None"] = relationship(
        back_populates="meter", uselist=False, cascade="all, delete-orphan"
    )
    status_history: Mapped[list["MeterStatusHistory"]] = relationship(
        back_populates="meter", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["MeterAttachment"]] = relationship(back_populates="meter", cascade="all, delete-orphan")


class MeterComm(Base, TimestampMixin):
    __tablename__ = "dev_meter_comm"
    __table_args__ = {"comment": "电表通信配置表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id", ondelete="CASCADE"), unique=True)
    protocol: Mapped[str] = mapped_column(String(20), default="DLMS")
    connection_type: Mapped[str] = mapped_column(String(20), default="tcp")
    host: Mapped[str] = mapped_column(String(255), default="")
    port: Mapped[int] = mapped_column(Integer, default=4059)
    device_address: Mapped[str] = mapped_column(String(50), default="")
    baud_rate: Mapped[int] = mapped_column(Integer, default=9600)
    parity: Mapped[str] = mapped_column(String(10), default="none")
    data_bits: Mapped[int] = mapped_column(Integer, default=8)
    stop_bits: Mapped[int] = mapped_column(Integer, default=1)
    auth_config: Mapped[dict | None] = mapped_column(JSON, default=None)
    timeout: Mapped[int] = mapped_column(Integer, default=30)
    retry_times: Mapped[int] = mapped_column(Integer, default=3)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Excel Meter sheet 扩展字段 ──
    device_type: Mapped[str] = mapped_column(String(30), default="electric_meter")
    pos: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 表台位置（基表任务必填）
    meter_mac: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 蓝牙地址
    src_wport: Mapped[int | None] = mapped_column(Integer, nullable=True)  # WPDU 源端口
    dst_wport: Mapped[int | None] = mapped_column(Integer, nullable=True)  # WPDU 目的端口
    lls_key: Mapped[str | None] = mapped_column(String(200), nullable=True)  # 低级安全密钥
    hls_key: Mapped[str | None] = mapped_column(String(200), nullable=True)  # 高级安全密钥
    comm_layer: Mapped[str] = mapped_column(String(10), default="HDLC")  # HDLC/WPDU/FEP

    meter: Mapped["Meter"] = relationship(back_populates="comm")


class MeterSnapshot(Base, TimestampMixin):
    __tablename__ = "dev_meter_snapshot"
    __table_args__ = {"comment": "电表实时快照表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id", ondelete="CASCADE"), unique=True)
    online_status: Mapped[bool] = mapped_column(Boolean, default=False)
    last_comm_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signal_strength: Mapped[int | None] = mapped_column(Integer, nullable=True)
    firmware_version: Mapped[str] = mapped_column(String(50), default="")
    error_code: Mapped[str] = mapped_column(String(20), default="")
    stack_usage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eeprom_write_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_data_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    meter: Mapped["Meter"] = relationship(back_populates="snapshot")


class MeterStatusHistory(Base):
    __tablename__ = "dev_meter_status"
    __table_args__ = {"comment": "电表状态变更记录表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id", ondelete="CASCADE"), index=True)
    old_status: Mapped[str] = mapped_column(String(20), default="")
    new_status: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(String(200), default="")
    changed_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    meter: Mapped["Meter"] = relationship(back_populates="status_history")


class MeterBorrow(Base, TimestampMixin):
    __tablename__ = "dev_meter_borrow"
    __table_args__ = {"comment": "电表借还记录表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id", ondelete="RESTRICT"), index=True)
    borrower_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True
    )
    borrow_reason: Mapped[str] = mapped_column(String(200))
    expected_return_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    actual_return_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    dept_approver_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True
    )
    lab_approver_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True
    )
    approval_status: Mapped[str] = mapped_column(String(20), default="pending_department")

    meter: Mapped["Meter"] = relationship()
    borrower: Mapped["User | None"] = relationship(foreign_keys=[borrower_id])


class MeterRepair(Base, TimestampMixin):
    __tablename__ = "dev_meter_repair"
    __table_args__ = {"comment": "电表维修记录表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id", ondelete="RESTRICT"), index=True)
    description: Mapped[str] = mapped_column(Text)
    cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    repaired_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True
    )

    meter: Mapped["Meter"] = relationship()


class MeterAttachment(Base):
    __tablename__ = "dev_meter_attachment"
    __table_args__ = {"comment": "电表附件表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(200))
    file_path: Mapped[str] = mapped_column(String(500))
    size: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    meter: Mapped["Meter"] = relationship(back_populates="attachments")
