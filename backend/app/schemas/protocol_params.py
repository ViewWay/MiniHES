"""协议特有参数校验 — 为 data_point_template.protocol_params JSONB 提供代码层强类型校验。

对应设计文档 6.3 节。JSONB 在数据库层无类型约束，
通过 Pydantic 在读写时补充校验。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DlmsParams(BaseModel):
    """电表 DLMS/COSEM 协议参数"""

    class_id: int = Field(ge=0, le=65535, description="COSEM 接口类 ID")
    attribute_id: int = Field(ge=0, le=255, description="属性 ID")


class ModbusParams(BaseModel):
    """Modbus 协议参数（水表/气表）"""

    function_code: int = Field(ge=1, le=4, description="功能码: 3=读保持寄存器, 4=读输入寄存器")
    register_count: int = Field(ge=1, le=125, description="寄存器数量")
    byte_order: Literal["ABCD", "DCBA", "BADC", "CDAB"] = Field("ABCD", description="字节序（大小端）")


class CommandParams(BaseModel):
    """AT 命令 / 私有指令参数（通信模块）"""

    command: str = Field(description="命令字符串，如 AT+CSQ")
    parse_rule: Literal["regex", "json_path", "fixed_offset"] = Field("regex", description="解析规则")
    pattern: str | None = Field(None, description="正则表达式或 JSONPath")
    group: int = Field(1, ge=0, description="正则捕获组序号")


# 设备类型 → 协议参数 Schema 映射
PROTOCOL_PARAMS_MAP: dict[str, type[BaseModel]] = {
    "electric_meter": DlmsParams,
    "water_meter": ModbusParams,
    "gas_meter": ModbusParams,
    "comm_module": CommandParams,
}


def validate_protocol_params(device_type: str, params: dict) -> BaseModel | dict:
    """根据设备类型查找对应 Schema 并校验 protocol_params。

    未知设备类型直接返回原始 dict（放行，不校验）。
    """
    schema_cls = PROTOCOL_PARAMS_MAP.get(device_type)
    if schema_cls is None:
        return params
    return schema_cls(**(params or {}))
