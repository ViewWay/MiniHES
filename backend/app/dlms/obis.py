"""
OBIS 码定义和常量

参考标准: IEC 62056-61: Object Identification System (OBIS)
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict


class InterfaceClass(IntEnum):
    """
    COSEM 接口类别 (IEC 62056-62)

    常用类别:
    - 1: Clock
    - 2: PNG calendar
    - 3: Activity calendar
    - 4: Register
    - 5: Demand register
    - 6: Register with activation
    - 7: Profile
    - 8: Load profile
    - 15: SAP assignment
    """

    # 数据接口类
    DATA = 1
    REGISTER = 4
    DEMAND_REGISTER = 5
    REGISTER_ACTIVATION = 6
    PROFILE = 7
    EXTENDED_REGISTER = 8

    # 控制接口类
    SCHEDULE = 10
    SCRIPT_TABLE = 11
    STATUS_MAPPING = 12
    SINGLE_ACTION_SCHEDULE = 14
    SAP_ASSIGNMENT = 15

    # 通知接口类
    EVENT = 21
    ACCOUNT = 22
    MBUS_CLIENT = 72


@dataclass
class OBISDefinition:
    """OBIS 码定义"""

    code: str
    name: str
    description: str
    unit: str
    interface_class: InterfaceClass
    attribute_count: int = 1


# 常用 OBIS 码定义表
COMMON_OBIS_CODES: Dict[str, OBISDefinition] = {
    # 电能数据
    "1.0.0.0.0.255": OBISDefinition(
        code="1.0.0.0.0.255",
        name="total_active_energy",
        description="总正向有功电能 (Total)",
        unit="kWh",
        interface_class=InterfaceClass.REGISTER,
    ),
    "1.0.1.8.0.255": OBISDefinition(
        code="1.0.1.8.0.255",
        name="current_demand",
        description="当前需量",
        unit="W",
        interface_class=InterfaceClass.DEMAND_REGISTER,
    ),
    "1.0.2.8.0.255": OBISDefinition(
        code="1.0.2.8.0.255",
        name="max_demand",
        description="最大需量",
        unit="W",
        interface_class=InterfaceClass.DEMAND_REGISTER,
    ),
    # 电压数据
    "1.0.12.7.0.255": OBISDefinition(
        code="1.0.12.7.0.255",
        name="voltage_l1",
        description="A相电压",
        unit="V",
        interface_class=InterfaceClass.EXTENDED_REGISTER,
    ),
    "1.0.32.7.0.255": OBISDefinition(
        code="1.0.32.7.0.255",
        name="voltage_l2",
        description="B相电压",
        unit="V",
        interface_class=InterfaceClass.EXTENDED_REGISTER,
    ),
    "1.0.52.7.0.255": OBISDefinition(
        code="1.0.52.7.0.255",
        name="voltage_l3",
        description="C相电压",
        unit="V",
        interface_class=InterfaceClass.EXTENDED_REGISTER,
    ),
    # 电流数据
    "1.0.21.7.0.255": OBISDefinition(
        code="1.0.21.7.0.255",
        name="current_l1",
        description="A相电流",
        unit="A",
        interface_class=InterfaceClass.EXTENDED_REGISTER,
    ),
    "1.0.41.7.0.255": OBISDefinition(
        code="1.0.41.7.0.255",
        name="current_l2",
        description="B相电流",
        unit="A",
        interface_class=InterfaceClass.EXTENDED_REGISTER,
    ),
    "1.0.61.7.0.255": OBISDefinition(
        code="1.0.61.7.0.255",
        name="current_l3",
        description="C相电流",
        unit="A",
        interface_class=InterfaceClass.EXTENDED_REGISTER,
    ),
    # 功率因数
    "1.0.14.7.0.255": OBISDefinition(
        code="1.0.14.7.0.255",
        name="power_factor_l1",
        description="A相功率因数",
        unit="",
        interface_class=InterfaceClass.EXTENDED_REGISTER,
    ),
    # 状态和配置
    "0.0.1.0.0.255": OBISDefinition(
        code="0.0.1.0.0.255", name="meter_status", description="电表状态", unit="", interface_class=InterfaceClass.DATA
    ),
    "0.0.96.1.0.255": OBISDefinition(
        code="0.0.96.1.0.255",
        name="meter_serial",
        description="电表序列号",
        unit="",
        interface_class=InterfaceClass.DATA,
    ),
    "0.0.96.1.1.255": OBISDefinition(
        code="0.0.96.1.1.255",
        name="meter_firmware",
        description="固件版本",
        unit="",
        interface_class=InterfaceClass.DATA,
    ),
}


def get_obis_definition(code: str) -> OBISDefinition:
    """获取 OBIS 码定义"""
    return COMMON_OBIS_CODES.get(code)


def list_obis_codes_by_name(name_pattern: str) -> list[OBISDefinition]:
    """按名称模糊搜索 OBIS 码"""
    return [defn for defn in COMMON_OBIS_CODES.values() if name_pattern.lower() in defn.name.lower()]
