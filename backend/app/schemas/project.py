from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: str = ""
    test_lead_id: int | None = None
    dev_lead_id: int | None = None
    status: str = Field("active", max_length=20)


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    test_lead_id: int | None = None
    dev_lead_id: int | None = None
    status: str | None = None
