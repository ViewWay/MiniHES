from datetime import datetime
from pydantic import BaseModel


class ProjectBase(BaseModel):
    name: str
    description: str = ""
    test_leader: str = ""
    dev_leader: str = ""
    status: str = "testing"
    device_count: int = 0
    online_count: int = 0
    progress: int = 0


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    pass


class ProjectOut(ProjectBase):
    id: int
    created_at: str = ""

    class Config:
        from_attributes = True
