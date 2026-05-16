import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Meter ----------

class MeterCreate(BaseModel):
    serial_number: str = Field(..., min_length=1, max_length=50, description="序列号")
    meter_name: str = Field(..., min_length=1, max_length=100, description="样机名称")
    meter_type_id: Optional[int] = Field(default=None, description="电表类型ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    protocol: str = Field(default="DLMS", max_length=20, description="协议")
    line_type: str = Field(default="single_phase", max_length=20, description="接线方式")
    manufacturer: str = Field(default="", max_length=100, description="制造商")
    model: str = Field(default="", max_length=100, description="型号")
    firmware_version: str = Field(default="", max_length=50, description="固件版本")
    hardware_version: str = Field(default="", max_length=50, description="硬件版本")
    frame_number: str = Field(default="", max_length=50, description="机架号")
    location: str = Field(default="", max_length=200, description="位置")
    factory_date: Optional[str] = Field(default=None, description="出厂日期")
    purchase_date: Optional[str] = Field(default=None, description="购买日期")
    warranty_date: Optional[str] = Field(default=None, description="保修日期")
    notes: str = Field(default="", description="备注")


class MeterUpdate(BaseModel):
    meter_name: Optional[str] = Field(default=None, max_length=100)
    meter_type_id: Optional[int] = Field(default=None)
    project_id: Optional[int] = Field(default=None)
    protocol: Optional[str] = Field(default=None, max_length=20)
    line_type: Optional[str] = Field(default=None, max_length=20)
    manufacturer: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)
    firmware_version: Optional[str] = Field(default=None, max_length=50)
    hardware_version: Optional[str] = Field(default=None, max_length=50)
    frame_number: Optional[str] = Field(default=None, max_length=50)
    location: Optional[str] = Field(default=None, max_length=200)
    factory_date: Optional[str] = Field(default=None)
    purchase_date: Optional[str] = Field(default=None)
    warranty_date: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)


class MeterListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    project_id: Optional[int] = None
    status: Optional[str] = None
    keyword: Optional[str] = None


class MeterDetail(BaseModel):
    id: int
    serial_number: str
    meter_name: str
    meter_type_id: Optional[int] = None
    project_id: Optional[int] = None
    protocol: str
    line_type: str
    manufacturer: str
    model: str
    firmware_version: str
    hardware_version: str
    frame_number: str
    location: str
    status: str
    factory_date: Optional[str] = None
    purchase_date: Optional[str] = None
    warranty_date: Optional[str] = None
    notes: str
    comm: Optional[dict] = None
    snapshot: Optional[dict] = None

    class Config:
        from_attributes = True


# ---------- Status ----------

class MeterStatusChange(BaseModel):
    status: str = Field(..., min_length=1, max_length=20, description="目标状态")
    reason: str = Field(default="", max_length=200, description="变更原因")


class MeterStatusHistoryOut(BaseModel):
    id: int
    old_status: str
    new_status: str
    reason: str
    created_at: str


# ---------- Communication ----------

class MeterCommUpdate(BaseModel):
    protocol: Optional[str] = Field(default=None, max_length=20)
    connection_type: Optional[str] = Field(default=None, max_length=20)
    host: Optional[str] = Field(default=None, max_length=255)
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    device_address: Optional[str] = Field(default=None, max_length=50)
    baud_rate: Optional[int] = Field(default=None)
    parity: Optional[str] = Field(default=None, max_length=10)
    data_bits: Optional[int] = Field(default=None)
    stop_bits: Optional[int] = Field(default=None)
    timeout: Optional[int] = Field(default=None, ge=1, le=300)
    retry_times: Optional[int] = Field(default=None, ge=0, le=10)
    is_enabled: Optional[bool] = Field(default=None)


# ---------- Borrow ----------

class BorrowCreate(BaseModel):
    meter_id: int = Field(..., description="样机ID")
    borrow_reason: str = Field(..., min_length=1, max_length=200, description="借用原因")
    expected_return_date: Optional[str] = Field(default=None, description="预计归还日期")
    dept_approver_id: Optional[int] = Field(default=None, description="部门审批人ID")


class BorrowApproval(BaseModel):
    approved: bool = Field(default=True, description="是否通过")
    reason: str = Field(default="", max_length=200, description="审批意见")


# ---------- Repair ----------

class RepairCreate(BaseModel):
    meter_id: int = Field(..., description="样机ID")
    description: str = Field(..., min_length=1, description="维修描述")
    cost: int = Field(default=0, ge=0, description="维修费用(分)")


class RepairUpdate(BaseModel):
    description: Optional[str] = Field(default=None, description="维修描述")
    cost: Optional[int] = Field(default=None, ge=0, description="维修费用(分)")
    status: Optional[str] = Field(default=None, max_length=20, description="状态")


# ---------- Attachment ----------

class AttachmentUpload(BaseModel):
    filename: str = Field(..., min_length=1, max_length=200, description="文件名")
    file_path: str = Field(..., min_length=1, max_length=500, description="文件路径")
    size: int = Field(default=0, ge=0, description="文件大小(字节)")


# ---------- Output schemas ----------

class MeterCommOut(BaseModel):
    id: int
    meter_id: int
    protocol: str
    connection_type: str
    host: str
    port: int
    device_address: str
    baud_rate: int
    parity: str
    data_bits: int
    stop_bits: int
    timeout: int
    retry_times: int
    is_enabled: bool

    class Config:
        from_attributes = True


class MeterSnapshotOut(BaseModel):
    id: int
    meter_id: int
    online_status: bool
    last_comm_time: Optional[str] = None
    signal_strength: Optional[int] = None
    firmware_version: str
    error_code: str

    class Config:
        from_attributes = True


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


class MeterBorrowOut(BaseModel):
    id: int
    meter_id: int
    meter_name: str
    borrower_id: Optional[int] = None
    borrow_reason: str
    expected_return_date: Optional[str] = None
    actual_return_date: Optional[str] = None
    approval_status: str
    created_at: str

    class Config:
        from_attributes = True


class MeterRepairOut(BaseModel):
    id: int
    meter_id: int
    description: str
    cost: int
    status: str
    repaired_by: Optional[int] = None
    created_at: str

    class Config:
        from_attributes = True


class MeterAttachmentOut(BaseModel):
    id: int
    meter_id: int
    filename: str
    file_path: str
    size: int
    uploaded_by: Optional[int] = None
    created_at: str

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
