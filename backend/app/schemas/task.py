from pydantic import BaseModel


class ScheduleConfig(BaseModel):
    cron: str | None = None
    interval_minutes: int | None = None


class ExecutionContent(BaseModel):
    meter_ids: list[int] | None = None
    obis_codes: list[str] | None = None
    analysis_type: str | None = None
    report_type: str | None = None


class TaskCreate(BaseModel):
    task_name: str
    task_type: str
    schedule_config: ScheduleConfig = {}
    execution_content: ExecutionContent = {}
    filter_config: dict = {}
    priority: int = 3
    retry_times: int = 3
    timeout: int = 60
    is_enabled: bool = True


class TaskUpdate(BaseModel):
    task_name: str | None = None
    task_type: str | None = None
    schedule_config: dict | None = None
    execution_content: dict | None = None
    filter_config: dict | None = None
    priority: int | None = None
    retry_times: int | None = None
    timeout: int | None = None
    is_enabled: bool | None = None


class TaskToggle(BaseModel):
    is_enabled: bool
