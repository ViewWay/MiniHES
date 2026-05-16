import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Task(Base, TimestampMixin):
    __tablename__ = "col_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_name: Mapped[str] = mapped_column(String(100))
    task_type: Mapped[str] = mapped_column(String(20))  # cron, interval, once
    schedule_config: Mapped[dict] = mapped_column(JSON, default=dict)
    execution_content: Mapped[dict] = mapped_column(JSON, default=dict)
    filter_config: Mapped[dict] = mapped_column(JSON, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    retry_times: Mapped[int] = mapped_column(Integer, default=3)
    timeout: Mapped[int] = mapped_column(Integer, default=300)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_execute_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_execute_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True
    )

    logs: Mapped[list["TaskLog"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class TaskLog(Base):
    __tablename__ = "col_task_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("col_task.id"), index=True)
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20))  # pending, running, completed, failed
    total_devices: Mapped[int] = mapped_column(Integer, default=0)
    success_devices: Mapped[int] = mapped_column(Integer, default=0)
    failed_devices: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    task: Mapped["Task"] = relationship(back_populates="logs")
    devices: Mapped[list["TaskDevice"]] = relationship(back_populates="log", cascade="all, delete-orphan")


class TaskDevice(Base):
    __tablename__ = "col_task_device"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    log_id: Mapped[int] = mapped_column(Integer, ForeignKey("col_task_log.id"), index=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("col_task.id"), index=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id"), index=True)
    status: Mapped[str] = mapped_column(String(20))  # pending, success, failed, timeout
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str] = mapped_column(String(50), default="")
    error_message: Mapped[str] = mapped_column(Text, default="")
    start_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    data_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    log: Mapped["TaskLog"] = relationship(back_populates="devices")


class DataQuality(Base):
    __tablename__ = "col_data_quality"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id"), index=True)
    task_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("col_task.id"), nullable=True)
    stat_date: Mapped[datetime.date] = mapped_column(Date)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    success_points: Mapped[int] = mapped_column(Integer, default=0)
    failed_points: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    abnormal_count: Mapped[int] = mapped_column(Integer, default=0)
    first_collect_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_collect_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
