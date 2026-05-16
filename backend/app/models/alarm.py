import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class AlarmRule(Base, TimestampMixin):
    __tablename__ = "sys_alarm_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_name: Mapped[str] = mapped_column(String(100))
    rule_type: Mapped[str] = mapped_column(String(50))  # threshold, anomaly, communication
    point_code: Mapped[str] = mapped_column(String(50), default="")
    condition_config: Mapped[dict | None] = mapped_column(JSON, default=None)
    severity: Mapped[str] = mapped_column(String(20))  # critical, warning, info
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    alarms: Mapped[list["Alarm"]] = relationship(back_populates="rule")


class Alarm(Base):
    __tablename__ = "sys_alarm_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id"), index=True)
    rule_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_alarm_rule.id"), nullable=True)
    alarm_type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20))
    alarm_message: Mapped[str] = mapped_column(Text)
    alarm_value: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    threshold_value: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    is_handled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    handled_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=True)
    handled_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rule: Mapped["AlarmRule | None"] = relationship(back_populates="alarms")
