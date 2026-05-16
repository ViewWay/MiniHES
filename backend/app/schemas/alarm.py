from pydantic import BaseModel, Field


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


class AlarmRuleCreate(BaseModel):
    rule_name: str = Field(..., max_length=100)
    rule_type: str = Field(..., max_length=50)  # threshold, anomaly, communication
    point_code: str = Field("", max_length=50)
    condition_config: dict | None = None
    severity: str = Field(..., max_length=20)  # critical, warning, info
    is_enabled: bool = True


class AlarmRuleUpdate(BaseModel):
    rule_name: str | None = Field(None, max_length=100)
    rule_type: str | None = None
    point_code: str | None = None
    condition_config: dict | None = None
    severity: str | None = None
    is_enabled: bool | None = None
