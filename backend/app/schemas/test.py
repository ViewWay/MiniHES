from datetime import datetime
from pydantic import BaseModel, Field


class TestTaskCreate(BaseModel):
    test_name: str = Field(..., max_length=100)
    test_type: str = Field(..., max_length=50)
    project_id: int | None = None
    status: str = Field("planned", max_length=20)
    description: str = ""
    start_time: datetime | None = None
    expected_end_time: datetime | None = None


class TestTaskUpdate(BaseModel):
    test_name: str | None = Field(None, max_length=100)
    test_type: str | None = None
    project_id: int | None = None
    status: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    expected_end_time: datetime | None = None


class TestReportCreate(BaseModel):
    report_number: str = Field(..., max_length=50)
    test_type: str = Field(..., max_length=50)
    test_environment: str = Field("", max_length=200)
    test_duration_days: int = 0
    firmware_version: str = Field("", max_length=50)
    hardware_version: str = Field("", max_length=50)
    conclusion: str  # pass, fail
    notes: str = ""


class TestReportUpdate(BaseModel):
    test_environment: str | None = None
    test_duration_days: int | None = None
    firmware_version: str | None = None
    hardware_version: str | None = None
    conclusion: str | None = None
    notes: str | None = None


class DefectCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = ""
    severity: str  # critical, major, minor
    meter_id: int | None = None
    detected_at: datetime | None = None


class DefectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    status: str | None = None  # open, resolved, closed
    meter_id: int | None = None
