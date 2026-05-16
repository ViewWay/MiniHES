from datetime import datetime
from pydantic import BaseModel


class MeterBase(BaseModel):
    serial_number: str
    meter_name: str
    meter_type_id: int = 1
    project_id: int = 0
    protocol: str = "DLMS"
    line_type: str = "1p2w"
    manufacturer: str = ""
    model: str = ""
    firmware_version: str = ""
    hardware_version: str = ""
    frame_number: str = ""
    location: str = ""
    status: str = "offline"
    factory_date: str = ""
    purchase_date: str = ""
    warranty_date: str = ""
    notes: str = ""


class MeterCreate(MeterBase):
    pass


class MeterUpdate(MeterBase):
    pass


class MeterOut(MeterBase):
    id: int

    class Config:
        from_attributes = True


class MeterStatusChange(BaseModel):
    status: str
    reason: str = ""


class MeterStatusHistoryOut(BaseModel):
    status: str
    reason: str
    created_at: str


class MeterAttachmentOut(BaseModel):
    id: int
    filename: str
    size: int
    uploaded_at: str


class MeterBorrowOut(BaseModel):
    id: int
    meter_id: int
    meter_name: str
    borrower_name: str
    borrow_reason: str
    expected_return_date: str
    status: str
    created_at: str


class MeterRepairOut(BaseModel):
    id: int
    meter_id: int
    meter_name: str
    description: str
    cost: int
    status: str
    created_at: str


class MeterTypeOut(BaseModel):
    id: int
    name: str
    code: str
    description: str

    class Config:
        from_attributes = True


class WireTypeOut(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class MeterPointOut(BaseModel):
    id: int
    name: str
    code: str
    unit: str
    protocol: str
    description: str

    class Config:
        from_attributes = True
