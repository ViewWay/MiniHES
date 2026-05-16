from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "dev_project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    test_lead_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True
    )
    dev_lead_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True
    )
    start_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    meters: Mapped[list["Meter"]] = relationship(back_populates="project")
