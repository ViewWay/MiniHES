from datetime import datetime
from pydantic import BaseModel


class AlarmOut(BaseModel):
    id: int
    meter_id: int
    meter_name: str
    alarm_type: str
    severity: str
    alarm_message: str
    alarm_value: str | None = None
    threshold_value: str | None = None
    is_handled: bool
    handle_notes: str | None = None
    created_at: str

    class Config:
        from_attributes = True


class AlarmHandleRequest(BaseModel):
    handle_notes: str = ""


class AlarmStatsOut(BaseModel):
    total: int
    unhandled_count: int
    critical_count: int
    warning_count: int
    info_count: int
    active: int
