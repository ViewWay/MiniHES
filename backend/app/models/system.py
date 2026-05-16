import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class AuditLog(Base):
    __tablename__ = "sys_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_user.id"), index=True)
    username: Mapped[str] = mapped_column(String(50))
    operation_type: Mapped[str] = mapped_column(String(50), index=True)  # CREATE, UPDATE, DELETE, LOGIN
    resource_type: Mapped[str] = mapped_column(String(50), default="")  # meter, task, report
    resource_id: Mapped[int] = mapped_column(Integer, default=0)
    old_values: Mapped[dict | None] = mapped_column(JSON, default=None)
    new_values: Mapped[dict | None] = mapped_column(JSON, default=None)
    ip_address: Mapped[str] = mapped_column(String(50), default="")
    user_agent: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DataArchive(Base, TimestampMixin):
    __tablename__ = "sys_data_archive"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    archive_type: Mapped[str] = mapped_column(String(20))  # postgresql, influxdb
    table_name: Mapped[str] = mapped_column(String(100))
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    archive_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, completed, failed
