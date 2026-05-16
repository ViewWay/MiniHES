import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class TestTask(Base, TimestampMixin):
    __tablename__ = "lab_test_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_name: Mapped[str] = mapped_column(String(100))
    test_type: Mapped[str] = mapped_column(String(50))  # protocol, accuracy, function, stability
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("dev_project.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planned")  # planned, running, completed, failed
    description: Mapped[str] = mapped_column(Text, default="")
    start_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_end_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=True)

    defects: Mapped[list["Defect"]] = relationship(back_populates="test_task")
    report: Mapped["TestReport | None"] = relationship(back_populates="test_task", uselist=False)


class Defect(Base):
    __tablename__ = "lab_defect"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey("lab_test_task.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(20))  # critical, major, minor
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, resolved, closed
    meter_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("dev_meter.id"), nullable=True)
    detected_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=True)
    resolved_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    test_task: Mapped["TestTask"] = relationship(back_populates="defects")


class TestReport(Base, TimestampMixin):
    __tablename__ = "lab_test_report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey("lab_test_task.id"), unique=True)
    report_number: Mapped[str] = mapped_column(String(50), unique=True)
    test_type: Mapped[str] = mapped_column(String(50))
    test_environment: Mapped[str] = mapped_column(String(200), default="")
    test_duration_days: Mapped[int] = mapped_column(Integer, default=0)
    firmware_version: Mapped[str] = mapped_column(String(50), default="")
    hardware_version: Mapped[str] = mapped_column(String(50), default="")
    conclusion: Mapped[str] = mapped_column(String(20))  # pass, fail
    notes: Mapped[str] = mapped_column(Text, default="")
    generated_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=True)

    test_task: Mapped["TestTask"] = relationship(back_populates="report")
