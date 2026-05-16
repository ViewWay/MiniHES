from pydantic import BaseModel, Field


class MeterPointCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    type: str = Field("register", max_length=50)
    data_type: str = Field("numeric", max_length=20)
    unit: str = Field("", max_length=20)
    protocol: str = Field("DLMS", max_length=20)
    description: str = ""
    storage_target: str = Field("influxdb", max_length=20)
    retention_days: int = 365


class MeterPointUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    type: str | None = None
    data_type: str | None = None
    unit: str | None = None
    protocol: str | None = None
    description: str | None = None
    storage_target: str | None = None
    retention_days: int | None = None
