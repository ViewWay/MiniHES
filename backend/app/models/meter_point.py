import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class MeterPoint(Base, TimestampMixin):
    __tablename__ = "dev_meter_point"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id"), index=True)
    obis_code: Mapped[str] = mapped_column(String(30), index=True)
    point_name: Mapped[str] = mapped_column(String(100))
    point_type: Mapped[str] = mapped_column(String(50))  # register, profile, attribute
    data_type: Mapped[str] = mapped_column(String(20), default="numeric")  # numeric, int, string
    unit: Mapped[str] = mapped_column(String(20), default="")
    scaler: Mapped[int] = mapped_column(Integer, default=0)
    is_collectible: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str] = mapped_column(Text, default="")

    meter: Mapped["Meter"] = relationship()


class MeterReading(Base):
    __tablename__ = "col_meter_reading"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id"), index=True)
    point_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter_point.id"), index=True)
    task_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("col_task.id"), nullable=True
    )
    reading_value: Mapped[float] = mapped_column(Numeric(18, 6))
    reading_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )
    quality: Mapped[str] = mapped_column(String(20), default="good")  # good, suspect, bad
    source: Mapped[str] = mapped_column(String(20), default="auto")  # auto, manual
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    meter: Mapped["Meter"] = relationship()
    point: Mapped["MeterPoint"] = relationship()


class ReadingDailySummary(Base, TimestampMixin):
    __tablename__ = "col_reading_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter.id"), index=True)
    point_id: Mapped[int] = mapped_column(Integer, ForeignKey("dev_meter_point.id"), index=True)
    stat_date: Mapped[datetime.date] = mapped_column(index=True)
    min_value: Mapped[float] = mapped_column(Numeric(18, 6))
    max_value: Mapped[float] = mapped_column(Numeric(18, 6))
    avg_value: Mapped[float] = mapped_column(Numeric(18, 6))
    first_value: Mapped[float] = mapped_column(Numeric(18, 6))
    last_value: Mapped[float] = mapped_column(Numeric(18, 6))
    reading_count: Mapped[int] = mapped_column(Integer, default=0)
    delta: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
