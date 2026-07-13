"""采集系统设备类型与任务类型定义。

DeviceType 决定数据点标识方式（OBIS码/寄存器地址/命令字）。
TaskCategory 决定执行行为（抄读策略/数据点集）。
两者的组合在 ConfigRegistry 中注册。
"""

from enum import Enum


class DeviceType(str, Enum):
    """设备类型 — 决定数据点标识方式和通信协议"""

    ELECTRIC_METER = "electric_meter"  # DLMS/COSEM, OBIS 码
    WATER_METER = "water_meter"  # Modbus, 寄存器地址
    GAS_METER = "gas_meter"  # Modbus / 私有协议
    CONCENTRATOR = "concentrator"  # DCU, 下挂电表档案
    COMM_MODULE = "comm_module"  # AT 命令 / 私有指令


class TaskCategory(str, Enum):
    """任务类型 — 决定执行行为和数据点集"""

    P2P = "p2p"  # 点对点（模块通信测试）
    METERING = "metering"  # 基表全量抄读
    DCU = "dcu"  # 集中器抄读
    MODBUS_POLL = "modbus_poll"  # Modbus 轮询（水气表）
    MQTT_SUBSCRIBE = "mqtt_subscribe"  # MQTT 订阅（集中器上报）
    COMMAND_TEST = "command_test"  # AT 命令测试（模块）


# device × category 有效组合矩阵
# 新增设备/任务类型时在此添加组合
VALID_COMBINATIONS: set[tuple[DeviceType, TaskCategory]] = {
    (DeviceType.ELECTRIC_METER, TaskCategory.P2P),
    (DeviceType.ELECTRIC_METER, TaskCategory.METERING),
    (DeviceType.ELECTRIC_METER, TaskCategory.DCU),
    (DeviceType.WATER_METER, TaskCategory.MODBUS_POLL),
    (DeviceType.GAS_METER, TaskCategory.MODBUS_POLL),
    (DeviceType.CONCENTRATOR, TaskCategory.DCU),
    (DeviceType.CONCENTRATOR, TaskCategory.MQTT_SUBSCRIBE),
    (DeviceType.COMM_MODULE, TaskCategory.P2P),
    (DeviceType.COMM_MODULE, TaskCategory.COMMAND_TEST),
}
