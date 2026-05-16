from datetime import datetime
from pydantic import BaseModel


class ScheduleConfig(BaseModel):
    cron: str | None = None
    interval_minutes: int | None = None


class ExecutionContent(BaseModel):
    meter_ids: list[int] | None = None
    obis_codes: list[str] | None = None
    analysis_type: str | None = None
    report_type: str | None = None


class TaskBase(BaseModel):
    task_name: str
    task_category: str
    task_type: str
    schedule_config: ScheduleConfig = {}
    execution_content: ExecutionContent = {}
    filter_config: dict = {}
    priority: int = 3
    retry_times: int = 3
    timeout: int = 60
    is_enabled: bool = True


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    pass


class TaskOut(TaskBase):
    id: int
    status: str = "paused"
    created_at: str = ""
    last_run: str | None = None
    next_run: str | None = None
    today_executions: int = 0

    class Config:
        from_attributes = True


class TaskToggle(BaseModel):
    is_enabled: bool


class TaskLogOut(BaseModel):
    id: int
    task_id: int
    status: str
    started_at: str
    finished_at: str | None = None
    duration_ms: int
    success_count: int
    fail_count: int

    class Config:
        from_attributes = True
