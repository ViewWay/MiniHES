from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    meter_ids: list[int] = Field(..., min_length=2)
    start_date: str
    end_date: str
    point_code: str = "1.0.0.0.0.255"


class ConsistencyCheckRequest(BaseModel):
    meter_ids: list[int]
    start_date: str
    end_date: str
