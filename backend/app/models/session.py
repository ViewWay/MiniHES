import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class CollectionSession(Base, TimestampMixin):
    __tablename__ = "col_session"
    __table_args__ = (
        Index("ix_session_meter_time", "meter_id", "started_at"),
        Index("ix_session_project_time", "project_id", "started_at"),
        {"comment": "采集会话表（PG-MongoDB 桥梁）"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id", ondelete="RESTRICT"), index=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dev_project.id", ondelete="SET NULL"), nullable=True
    )
    task_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("col_task.id", ondelete="SET NULL"), nullable=True)

    # MongoDB 定位
    mongo_db: Mapped[str] = mapped_column(String(200), default="")
    mongo_collection: Mapped[str] = mapped_column(String(200), default="")
    mongo_doc_id: Mapped[str] = mapped_column(String(100), default="")

    # 来源
    source: Mapped[str] = mapped_column(String(20), default="auto")  # auto, manual, import
    source_file: Mapped[str] = mapped_column(String(500), default="")

    # 时间
    started_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    # 采集结果统计
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # pending, running, completed, failed
    total_read: Mapped[int] = mapped_column(Integer, default=0)
    total_success: Mapped[int] = mapped_column(Integer, default=0)
    total_failed: Mapped[int] = mapped_column(Integer, default=0)
    sheet_count: Mapped[int] = mapped_column(Integer, default=0)

    # 连接信息
    connection_type: Mapped[str] = mapped_column(String(20), default="")  # HDLC, TCP, WPDU, FEP
    communication: Mapped[str] = mapped_column(String(20), default="")
    meter_ip: Mapped[str] = mapped_column(String(50), default="")
    ping_status: Mapped[bool] = mapped_column(Boolean, default=False)

    # 错误摘要
    error_summary: Mapped[str] = mapped_column(Text, default="")

    meter: Mapped["Meter"] = relationship()
