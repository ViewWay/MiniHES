# 采集任务配置建模设计

**创建日期**: 2026-07-09
**状态**: 设计评审中
**关联**: 基于 `MeterSchedulerFusion/meterParams/模板` Excel 配置文件

---

## 一、背景与问题

### 1.1 现有 Excel 配置结构

当前实验室抄表测试使用 Excel 文件驱动，包含 9 个 sheet：

| Sheet | 作用 | 示例行数 |
|-------|------|----------|
| **Meter** | 电表清单 + 连接参数（IP/串口/蓝牙/密钥） | 3 表 |
| **Configuration** | 全局执行参数，含 `tag` 列标注参数适用的任务类型 | 30 参数 |
| **P2PObis** | P2P 任务 OBIS 码集（信号指标） | 14 项 |
| **MeteringObis** | 基表任务 OBIS 码集（全量抄读） | 345 项 |
| **DCUObis** | DCU 任务 OBIS 码集 | 2 项 |
| **ObisList** | 完整对象模型参考（IEC 62056） | 95 项 |
| **case** | 测试用例定义（健壮性/性能） | 27 用例 |
| **data** | 用例重复次数 + 数据对比规则 | 92 检查点 |
| **param** | 继电器控制参数 | 2 参数 |

### 1.2 核心矛盾

| Excel 概念 | MiniHES 现状 | 差距 |
|---|---|---|
| testTask (P2P/Metering/DCU) | `Task.task_type` = cron/interval/once | ❌ **语义冲突**：调度类型 ≠ 业务类型 |
| communication (HDLC/WPDU/FEP) | `MeterComm.protocol` = "DLMS" | ❌ 缺通信封装层 |
| batch / clientId | 无 | ❌ 未建模 |
| byEntry / byRange 抄读策略 | 无 | ❌ 核心业务逻辑未建模 |
| 4 个 OBIS sheet | `MeterPoint` 逐表手配 | ❌ **缺 OBIS 模板概念** |
| Configuration 全局参数 | `execution_content` (松散 JSON) | ⚠️ 无 schema 验证 |
| tag 条件配置 (p2p/metering/dcu) | 无 | ❌ 参数无适用范围标注 |

### 1.3 扩展需求

业务不仅限于电表，需支持：
- 电表（DLMS/COSEM）
- 水表 / 气表（Modbus）
- 集中器（DCU，下挂电表）
- 通信模块（AT 命令/私有指令）

---

## 二、设计决策（已确认）

| 决策点 | 选择 | 说明 |
|--------|------|------|
| **模板覆盖机制** | A — 模板完整集合 + 任务可勾选/取消 | 模板存全量，Task 通过 override 表覆盖个别项 |
| **条件配置处理** | C — 单 schema 全包含 + 前端动态显隐 | 字段带 `tags` metadata，前端按 task_category 显隐 |
| **数据点存储** | A — 统一表 + JSONB 扩展列 | 一张 `data_point_template` 表管所有设备类型 |

---

## 三、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户侧                                     │
│  前端表单 / Excel 上传 / API 创建                                  │
├─────────────────────────────────────────────────────────────────┤
│                        配置层                                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │ DeviceType   │  │ TaskCategory     │  │ ConfigRegistry    │  │
│  │ (枚举,代码层) │  │ (枚举,代码层)     │  │ (注册表,代码层)    │  │
│  │ electric     │  │ p2p              │  │                   │  │
│  │ water        │  │ metering         │  │ device × category │  │
│  │ gas          │  │ dcu              │  │ → schema + defaults│  │
│  │ concentrator │  │ modbus_poll      │  │ → obis_template   │  │
│  │ module       │  │ mqtt_subscribe   │  │                   │  │
│  └──────────────┘  └──────────────────┘  └───────────────────┘  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                        数据层                                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │ Task         │  │ ObisTemplate     │  │ TaskObisOverride  │  │
│  │ +device_type │  │ +device_type     │  │ task_id           │  │
│  │ +task_categ. │  │ +task_category   │  │ template_item_id  │  │
│  │ +obis_tmpl_id│  │                  │  │ is_selected       │  │
│  │ +config(JSON)│  │ DataPointTemplate│  │ custom_params     │  │
│  └──────────────┘  │ (统一表+JSONB)   │  └───────────────────┘  │
│                    │ +address(通用)   │                         │
│  ┌──────────────┐  │ +protocol_params │  ┌───────────────────┐  │
│  │ MeterComm    │  │   (协议差异)     │  │ MeterPoint        │  │
│  │ +pos         │  └──────────────────┘  │ (逐表配置,保留)   │  │
│  │ +meter_mac   │                        └───────────────────┘  │
│  │ +keys        │                                               │
│  │ +comm_layer  │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、详细设计

### 4.1 代码层：设备类型与任务类型

```python
# app/services/collector/types.py

from enum import Enum


class DeviceType(str, Enum):
    """设备类型 — 决定数据点标识方式和通信协议"""
    ELECTRIC_METER = "electric_meter"    # DLMS/COSEM, OBIS 码
    WATER_METER = "water_meter"          # Modbus, 寄存器地址
    GAS_METER = "gas_meter"              # Modbus / 私有协议
    CONCENTRATOR = "concentrator"        # DCU, 下挂电表档案
    COMM_MODULE = "comm_module"          # AT 命令 / 私有指令


class TaskCategory(str, Enum):
    """任务类型 — 决定执行行为和数据点集"""
    P2P = "p2p"                          # 点对点（模块通信测试）
    METERING = "metering"                # 基表全量抄读
    DCU = "dcu"                          # 集中器抄读
    MODBUS_POLL = "modbus_poll"          # Modbus 轮询（水气表）
    MQTT_SUBSCRIBE = "mqtt_subscribe"    # MQTT 订阅（集中器上报）
    COMMAND_TEST = "command_test"        # AT 命令测试（模块）


# device × category 有效组合矩阵
VALID_COMBINATIONS = {
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
```

### 4.2 代码层：配置 Registry

每种 `device × category` 组合注册一个 Pydantic schema + 默认值 + OBIS 模板引用。

```python
# app/services/collector/registry.py

from dataclasses import dataclass
from typing import Type
from pydantic import BaseModel


@dataclass
class ConfigRegistration:
    """一个 device × category 组合的注册信息"""
    device_type: DeviceType
    task_category: TaskCategory
    config_schema: Type[BaseModel]       # 该组合的 Pydantic 配置类
    defaults: dict                       # 默认参数
    obis_template_name: str | None       # 关联的系统模板名
    description: str                     # 人类可读描述


class ConfigRegistry:
    """配置注册表 — 启动时注册所有组合"""

    def __init__(self):
        self._registrations: dict[tuple[DeviceType, TaskCategory], ConfigRegistration] = {}

    def register(self, reg: ConfigRegistration):
        key = (reg.device_type, reg.task_category)
        self._registrations[key] = reg

    def get(self, device_type: DeviceType, task_category: TaskCategory) -> ConfigRegistration | None:
        return self._registrations.get((device_type, task_category))

    def validate_config(self, device_type, task_category, raw: dict) -> BaseModel:
        """根据组合查找 schema 并校验 + 填充默认值"""
        reg = self.get(device_type, task_category)
        if not reg:
            raise ValueError(f"不支持的组合: {device_type} × {task_category}")
        merged = {**reg.defaults, **raw}
        return reg.config_schema(**merged)

    def list_combinations(self) -> list[dict]:
        """列出所有已注册组合（供前端动态渲染表单）"""
        return [
            {
                "device_type": r.device_type.value,
                "task_category": r.task_category.value,
                "description": r.description,
            }
            for r in self._registrations.values()
        ]


registry = ConfigRegistry()
```

### 4.3 代码层：配置 Schema（单 schema + tags metadata）

采用**方案 C**：一个 schema 全包含，字段带 `tags` 标注适用场景。

```python
# app/schemas/collector_config.py

from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field


class BaseTaskConfig(BaseModel):
    """所有设备类型共享的公共配置"""

    # ── 通信参数（公共）──
    communication: str = Field("HDLC", description="HDLC/WPDU/FEP/Modbus/MQTT")

    batch: int = Field(6, ge=1, le=100, description="并发抄读表数")
    client_id: int = Field(1, ge=0, le=16, description="DLMS 客户端 SAP")
    timeout: int = Field(30, ge=1, le=600, description="单次超时(秒)")
    retry_times: int = Field(3, ge=0, le=10, description="重试次数")

    is_unlock: bool = Field(True, description="是否解锁")
    data_recapture: bool = Field(False, description="是否补采")

    # ── 网络监控 ──
    is_pcap: bool | None = Field(None, description="Wireshark 监控")
    iface: str | None = Field(None, description="指定网卡")
    log_path: str | None = Field(None, description="日志路径")


class ElectricMeterConfig(BaseTaskConfig):
    """电表配置 — 对应 Excel Configuration sheet 的电表参数
    覆盖 p2p / metering / dcu 三种 task_category
    """

    # ── 连接方式 ──
    connect_type: Literal["Network", "Serial"] | None = Field(
        None, description="连接方式，默认 HDLC→Serial, WPDU/FEP→Network"
    )

    # ── 抄读策略 ──
    read_strategy: Literal["full", "by_entry", "by_range"] = Field(
        "full", json_schema_extra={"tags": ["p2p", "metering", "dcu"]}
    )
    by_entry: int | None = Field(
        None, description="按条数抄读, 如 -200/-1",
        json_schema_extra={"tags": ["p2p", "dcu"]}
    )
    by_range: Literal["yesterday", "all", "lastweek"] | None = Field(
        None, json_schema_extra={"tags": ["metering", "dcu"]}
    )
    by_range_start: datetime | None = Field(None, description="自定义起始时间")
    by_range_end: datetime | None = Field(None, description="自定义结束时间")
    by_range_period_hours: int | None = Field(
        None, description="当前时间向前推算周期(h)"
    )

    # ── 安全密钥 ──
    encryption_key: str | None = Field(
        None, description="EKey", json_schema_extra={"tags": ["p2p", "metering", "dcu"]}
    )
    auth_key: str | None = Field(None, description="AKey")
    lls_key: str | None = Field(None, description="低级安全密钥")
    hls_key: str | None = Field(None, description="高级安全密钥")

    # ── 模块/版本（metering 专用）──
    is_dongle: bool | None = Field(
        None, description="蓝牙连接",
        json_schema_extra={"tags": ["metering"]}
    )
    is_check_archive: bool | None = Field(
        None, description="FEP 检查档案",
        json_schema_extra={"tags": ["p2p"]}
    )
    app1_id: str | None = Field(
        None, description="App1 版本号生产命令",
        json_schema_extra={"tags": ["metering"]}
    )
    app2_id: str | None = Field(
        None, description="App2 版本号生产命令",
        json_schema_extra={"tags": ["metering"]}
    )
    module_cmcs_id: str | None = Field(
        None, description="模块版本号生产命令",
        json_schema_extra={"tags": ["metering"]}
    )
    identifier: str | None = Field(
        None, description="Andromeda 标识 (KFM-03/KFM-01)",
        json_schema_extra={"tags": ["metering"]}
    )

    # ── DCU 专用 ──
    reading_object_obis: str | None = Field(
        None, description="抄读状态判断 OBIS (默认 7,1-0:99.1.0.255,2)",
        json_schema_extra={"tags": ["dcu"]}
    )


class WaterMeterConfig(BaseTaskConfig):
    """水表配置（Modbus）— 未来扩展"""

    communication: str = Field("Modbus")
    register_start: int = Field(0, ge=0)
    register_count: int = Field(20, ge=1, le=125)
    function_code: int = Field(3, description="Modbus 功能码: 3=读保持, 4=读输入")
    slave_id: int = Field(1, ge=1, le=247)
    byte_order: Literal["ABCD", "DCBA", "BADC", "CDAB"] = Field("ABCD")


class ConcentratorConfig(BaseTaskConfig):
    """集中器配置 — 未来扩展"""

    communication: str = Field("MQTT")
    topic: str | None = Field(None, description="MQTT 订阅主题")
    qos: int = Field(1, ge=0, le=2)
    sub_device_ids: list[int] | None = Field(
        None, description="下挂电表 ID 列表"
    )


class CommModuleConfig(BaseTaskConfig):
    """通信模块配置 — 未来扩展"""

    communication: str = Field("AT")
    command_set: str | None = Field(
        None, description="命令集合名称"
    )
```

### 4.4 代码层：注册初始化

```python
# app/services/collector/bootstrap.py

def register_all():
    """启动时注册所有 device × category 组合"""

    # ── 电表 × P2P（模块通信测试）──
    registry.register(ConfigRegistration(
        device_type=DeviceType.ELECTRIC_METER,
        task_category=TaskCategory.P2P,
        config_schema=ElectricMeterConfig,
        defaults={
            "communication": "HDLC",
            "batch": 6,
            "read_strategy": "by_entry",
            "is_unlock": True,
        },
        obis_template_name="p2p_signal",
        description="电表 P2P — 模块信号通信测试（14项信号指标）",
    ))

    # ── 电表 × Metering（基表全量抄读）──
    registry.register(ConfigRegistration(
        device_type=DeviceType.ELECTRIC_METER,
        task_category=TaskCategory.METERING,
        config_schema=ElectricMeterConfig,
        defaults={
            "communication": "HDLC",
            "batch": 6,
            "read_strategy": "by_range",
            "data_recapture": True,
        },
        obis_template_name="metering_full",
        description="电表基表 — 全量抄读（345项 OBIS）",
    ))

    # ── 电表 × DCU（集中器抄读）──
    registry.register(ConfigRegistration(
        device_type=DeviceType.ELECTRIC_METER,
        task_category=TaskCategory.DCU,
        config_schema=ElectricMeterConfig,
        defaults={
            "communication": "FEP",
            "read_strategy": "full",
        },
        obis_template_name="dcu_archive",
        description="电表 DCU — 集中器档案抄读",
    ))

    # ── 水表 × Modbus ──
    registry.register(ConfigRegistration(
        device_type=DeviceType.WATER_METER,
        task_category=TaskCategory.MODBUS_POLL,
        config_schema=WaterMeterConfig,
        defaults={"communication": "Modbus", "batch": 1},
        obis_template_name="water_modbus",
        description="水表 — Modbus 轮询抄读",
    ))

    # ── 集中器 × MQTT ──
    registry.register(ConfigRegistration(
        device_type=DeviceType.CONCENTRATOR,
        task_category=TaskCategory.MQTT_SUBSCRIBE,
        config_schema=ConcentratorConfig,
        defaults={"communication": "MQTT"},
        obis_template_name=None,
        description="集中器 — MQTT 订阅上报数据",
    ))

    # ── 通信模块 × AT 命令测试 ──
    registry.register(ConfigRegistration(
        device_type=DeviceType.COMM_MODULE,
        task_category=TaskCategory.COMMAND_TEST,
        config_schema=CommModuleConfig,
        defaults={"communication": "AT"},
        obis_template_name="module_at_commands",
        description="通信模块 — AT 命令测试",
    ))
```

---

## 五、数据库设计

### 5.1 ER 关系图

```
┌──────────────────┐         ┌──────────────────┐
│ ObisTemplate     │1───────*│ DataPointTemplate│
│ (模板)            │         │ (统一数据点表)    │
│ device_type      │         │ address(通用)     │
│ task_category    │         │ protocol_params  │
│ is_system        │         │ (JSONB,协议差异)  │
└────────┬─────────┘         └──────────────────┘
         │1
         │
         *
┌────────┴─────────┐         ┌──────────────────┐
│ Task             │1───────*│ TaskObisOverride │
│ device_type      │         │ (覆盖表)          │
│ task_category    │         │ is_selected       │
│ obis_template_id │         │ custom_params     │
│ config (JSON)    │         └──────────────────┘
│ execution_content│
│ (→Registry校验)  │         ┌──────────────────┐
└────────┬─────────┘         │ MeterPoint       │
         │                   │ (逐表配置,保留)  │
         │                   └──────────────────┘
         *
┌────────┴─────────┐         ┌──────────────────┐
│ TaskDevice       │         │ MeterComm        │
│ (执行明细)        │         │ +pos/mac/keys    │
└──────────────────┘         │ +comm_layer      │
                             └──────────────────┘
```

### 5.2 新建表：ObisTemplate + DataPointTemplate

```sql
-- ============================================================
-- 数据点模板表
-- ============================================================
CREATE TABLE obis_template (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(100)  NOT NULL,
    device_type   VARCHAR(30)   NOT NULL,           -- electric_meter / water_meter...
    task_category VARCHAR(30)   NOT NULL,           -- p2p / metering / dcu...
    description   TEXT,
    is_system     BOOLEAN       DEFAULT FALSE,      -- 系统内置不可删
    version       INT           DEFAULT 1,
    created_at    TIMESTAMPTZ   DEFAULT now(),
    updated_at    TIMESTAMPTZ   DEFAULT now(),
    UNIQUE(name, version)
);

COMMENT ON TABLE obis_template IS '数据点模板表';

-- ============================================================
-- 数据点模板明细（统一表 + JSONB 扩展）
-- ============================================================
CREATE TABLE data_point_template (
    id              SERIAL PRIMARY KEY,
    template_id     INT          NOT NULL REFERENCES obis_template(id) ON DELETE CASCADE,
    device_type     VARCHAR(30)  NOT NULL,           -- 冗余,加速查询

    -- 通用字段（所有设备类型都有）
    module          VARCHAR(50),                     -- Clock/Energy/Instantaneous/Volume/Signal...
    point_name      VARCHAR(200) NOT NULL,
    address         VARCHAR(60)  NOT NULL,           -- 通用标识：OBIS码 / Modbus寄存器 / 命令字
    data_type       VARCHAR(20)  DEFAULT 'numeric',
    unit            VARCHAR(20)  DEFAULT '',
    scaler          INT          DEFAULT 0,
    is_read         BOOLEAN      DEFAULT TRUE,
    sort_order      INT          DEFAULT 0,
    remark          TEXT,

    -- 协议特有参数（差异部分，JSONB）
    -- 电表(DLMS): {"class_id": 3, "attribute_id": 2}
    -- 水表(Modbus): {"function_code": 3, "register_count": 2, "byte_order": "ABCD"}
    -- 模块(AT): {"command": "AT+CSQ", "parse_rule": "regex", "pattern": "\\+CSQ: (\\d+)"}
    protocol_params JSONB        DEFAULT '{}',

    UNIQUE(template_id, address)
);

CREATE INDEX ix_dpt_template ON data_point_template(template_id);
CREATE INDEX ix_dpt_device_type ON data_point_template(device_type);

COMMENT ON TABLE data_point_template IS '数据点模板明细表';
COMMENT ON COLUMN data_point_template.address IS '通用标识：电表=OBIS码, 水表=寄存器地址, 模块=命令字';
COMMENT ON COLUMN data_point_template.protocol_params IS '协议特有参数，JSONB';
```

### 5.3 新建表：TaskObisOverride（模板覆盖）

```sql
-- ============================================================
-- 任务数据点覆盖表（模板 + 覆盖机制）
-- ============================================================
CREATE TABLE task_obis_override (
    id                  SERIAL PRIMARY KEY,
    task_id             INT          NOT NULL REFERENCES col_task(id) ON DELETE CASCADE,
    template_item_id    INT          NOT NULL REFERENCES data_point_template(id) ON DELETE CASCADE,
    is_selected         BOOLEAN      DEFAULT TRUE,     -- 勾选/取消
    custom_params       JSONB,                         -- 覆盖个别参数
    created_at          TIMESTAMPTZ  DEFAULT now(),

    UNIQUE(task_id, template_item_id)
);

COMMENT ON TABLE task_obis_override IS '任务数据点覆盖表';
```

**覆盖逻辑**：
- 创建任务引用模板时，override 表为空 → 全部读模板默认值
- 用户取消某项 → `INSERT (task_id, item_id, is_selected=false)`
- 用户微调参数 → `INSERT (task_id, item_id, custom_params={...})`
- 查询任务实际数据点集 = 模板 LEFT JOIN override，override 优先

### 5.4 现有表修改：Task

```sql
-- col_task 新增字段（向后兼容，全部有默认值）
ALTER TABLE col_task
    ADD COLUMN device_type     VARCHAR(30) DEFAULT 'electric_meter',
    ADD COLUMN task_category   VARCHAR(30) DEFAULT 'metering',
    ADD COLUMN obis_template_id INT REFERENCES obis_template(id) ON DELETE SET NULL;

COMMENT ON COLUMN col_task.task_type IS '调度类型: cron/interval/once';
COMMENT ON COLUMN col_task.task_category IS '业务类型: p2p/metering/dcu/modbus_poll/...';
COMMENT ON COLUMN col_task.device_type IS '设备类型: electric_meter/water_meter/...';
COMMENT ON COLUMN col_task.obis_template_id IS '数据点模板ID';
COMMENT ON COLUMN col_task.execution_content IS '执行配置JSON, 通过 ConfigRegistry 校验';
```

**注意**：现有 `task_type` 语义**不变**（仍然是 cron/interval/once），新增 `task_category` 承载业务语义。

### 5.5 现有表修改：MeterComm

```sql
-- dev_meter_comm 新增字段（对齐 Excel Meter sheet 连接参数）
ALTER TABLE dev_meter_comm
    ADD COLUMN device_type  VARCHAR(30)  DEFAULT 'electric_meter',
    ADD COLUMN pos          INT,                          -- 表台位置
    ADD COLUMN meter_mac    VARCHAR(50),                  -- 蓝牙地址
    ADD COLUMN src_wport    INT,                          -- WPDU 源端口
    ADD COLUMN dst_wport    INT,                          -- WPDU 目的端口
    ADD COLUMN lls_key      VARCHAR(200),                 -- 低级安全密钥
    ADD COLUMN hls_key      VARCHAR(200),                 -- 高级安全密钥
    ADD COLUMN comm_layer   VARCHAR(10)  DEFAULT 'HDLC';  -- HDLC/WPDU/FEP

COMMENT ON COLUMN dev_meter_comm.comm_layer IS '通信封装层: HDLC/WPDU/FEP';
```

---

## 六、数据点存储方案详解（方案 A）

### 6.1 设计原则

```
data_point_template
├── address (VARCHAR 60)    ← 统一标识列，所有设备类型都有
│   电表: '1.0.1.8.0.255'   (OBIS 码)
│   水表: '40001'            (Modbus 寄存器地址)
│   模块: 'AT+CSQ'           (AT 命令)
│
├── 通用列 (module/point_name/unit/scaler/data_type/...)
│   所有设备类型都有这些字段，语义一致
│
└── protocol_params (JSONB) ← 协议差异兜底
    按设备类型有不同的 schema（代码层校验）
```

### 6.2 实际存储示例

```sql
-- ── 电表（DLMS/COSEM）──
INSERT INTO data_point_template
    (template_id, device_type, module, point_name, address,
     data_type, unit, scaler, protocol_params)
VALUES
    (1, 'electric_meter', 'Energy', 'Active energy import rate 1',
     '1.0.1.8.1.255', 'numeric', 'kWh', 0,
     '{"class_id": 3, "attribute_id": 2}'),

    (1, 'electric_meter', 'Instantaneous', 'Voltage L1',
     '1.0.32.7.0.255', 'numeric', 'V', 1,
     '{"class_id": 3, "attribute_id": 2}');

-- ── 水表（Modbus）──
INSERT INTO data_point_template
    (template_id, device_type, module, point_name, address,
     data_type, unit, scaler, protocol_params)
VALUES
    (2, 'water_meter', 'Volume', '累计用水量',
     '40001', 'numeric', 'm³', 3,
     '{"function_code": 3, "register_count": 2, "byte_order": "ABCD"}');

-- ── 通信模块（AT 命令）──
INSERT INTO data_point_template
    (template_id, device_type, module, point_name, address,
     data_type, protocol_params)
VALUES
    (3, 'comm_module', 'Signal', 'CSQ 信号强度',
     'AT+CSQ', 'string',
     '{"command": "AT+CSQ", "parse_rule": "regex", "pattern": "\\+CSQ: (\\d+)", "group": 1}');
```

### 6.3 代码层协议参数校验

JSONB 没有强类型，但通过 Pydantic 在代码层补充校验：

```python
# app/schemas/protocol_params.py

class DlmsParams(BaseModel):
    """电表 DLMS 协议参数"""
    class_id: int = Field(ge=0, le=65535)
    attribute_id: int = Field(ge=0, le=255)

class ModbusParams(BaseModel):
    """Modbus 协议参数"""
    function_code: int = Field(ge=1, le=4)
    register_count: int = Field(ge=1, le=125)
    byte_order: Literal["ABCD", "DCBA", "BADC", "CDAB"] = "ABCD"

class CommandParams(BaseModel):
    """AT 命令 / 私有指令参数"""
    command: str
    parse_rule: Literal["regex", "json_path", "fixed_offset"] = "regex"
    pattern: str | None = None
    group: int = 1

# 校验映射
PROTOCOL_PARAMS_MAP = {
    "electric_meter": DlmsParams,
    "water_meter": ModbusParams,
    "gas_meter": ModbusParams,
    "comm_module": CommandParams,
}

def validate_protocol_params(device_type: str, params: dict) -> BaseModel:
    schema = PROTOCOL_PARAMS_MAP.get(device_type)
    if schema:
        return schema(**params)
    return params  # 未知类型放行
```

### 6.4 查询：任务实际数据点集

```sql
-- 查某个任务的完整数据点集（模板 + override 合并）
SELECT
    t.id           AS template_item_id,
    t.address,
    t.point_name,
    t.module,
    t.unit,
    t.data_type,
    COALESCE(o.is_selected, t.is_read) AS final_is_selected,
    CASE
        WHEN o.custom_params IS NOT NULL
        THEN o.custom_params || t.protocol_params  -- override 优先合并
        ELSE t.protocol_params
    END AS final_params
FROM data_point_template t
JOIN col_task task ON task.obis_template_id = t.template_id
LEFT JOIN task_obis_override o ON o.task_id = task.id AND o.template_item_id = t.id
WHERE task.id = :task_id
  AND COALESCE(o.is_selected, t.is_read) = TRUE
ORDER BY t.sort_order;
```

---

## 七、Excel 导入映射

Excel 9 个 sheet → MiniHES 数据模型的映射关系：

| Excel Sheet | → MiniHES 目标 | 说明 |
|---|---|---|
| **Meter** | `Meter` + `MeterComm` | serialNo→serial_number, serverIpAddress→MeterComm.host, llsKey/hlsKey→新字段 |
| **Configuration** | `Task.execution_content` (JSON) | 按 tag 拆分后写入 ElectricMeterConfig，Registry 校验 |
| **P2PObis** | `ObisTemplate(name=p2p_signal)` + items | 14 项信号指标 |
| **MeteringObis** | `ObisTemplate(name=metering_full)` + items | 345 项全量 |
| **DCUObis** | `ObisTemplate(name=dcu_archive)` + items | 2 项 |
| **ObisList** | 参考数据，不导入 | IEC 62056 标准对象模型 |
| **case** | `TestTask` | 测试用例编号 + 检查点 |
| **data** | 重复次数→TestTask config, 对比规则→待建 | 健壮性检查参数 |
| **param** | 待建 relay 控制表 | 继电器参数（后期） |

### Configuration sheet tag 映射

```
tag = "p2p/metering/dcu"     → 该参数在三种任务下都适用
tag = "metering"             → 仅 metering 任务生效
tag = "metering/dcu"         → metering 和 dcu 生效
```

导入时全部写入 `ElectricMeterConfig` schema，前端根据字段 `json_schema_extra.tags` 动态显隐。

---

## 八、前端动态表单驱动

前端创建任务时的流程：

```
1. 选择设备类型 (device_type)
   → 调 GET /api/v1/collector/registry/combinations
   → 返回该设备类型支持的 task_category 列表

2. 选择任务类型 (task_category)
   → 调 GET /api/v1/collector/registry/schema?device=electric_meter&category=metering
   → 返回 JSON Schema（含字段 tags 标注）
   → 前端根据 tags 渲染表单字段（当前 category 不在 tags 中的字段隐藏）

3. 选择 OBIS 模板
   → 调 GET /api/v1/collector/templates?device=electric_meter&category=metering
   → 返回模板列表 + 每个模板的数据点数量

4. 填写配置 → 提交
   → POST /api/v1/tasks  (config 为 JSON，后端 Registry 校验)
```

---

## 九、实施计划

### Phase 1: 数据模型 + Migration（1-2天）
- [ ] 创建 `obis_template` + `data_point_template` + `task_obis_override` 表
- [ ] `col_task` 加 `device_type` / `task_category` / `obis_template_id`
- [ ] `dev_meter_comm` 加连接参数字段
- [ ] Alembic migration（down_revision = `14399098fe8c`）

### Phase 2: 代码层 Registry + Schema（2-3天）
- [ ] `app/services/collector/types.py` — 枚举定义
- [ ] `app/services/collector/registry.py` — 注册表
- [ ] `app/schemas/collector_config.py` — 配置 schema
- [ ] `app/schemas/protocol_params.py` — 协议参数校验
- [ ] bootstrap 初始化注册

### Phase 3: 系统模板数据导入（1天）
- [ ] Excel 4 个 OBIS sheet → 系统 ObisTemplate（is_system=true）
- [ ] seed 脚本写入 p2p_signal(14) / metering_full(345) / dcu_archive(2)

### Phase 4: API + 前端（2-3天）
- [ ] Registry 查询 API（combinations / schema）
- [ ] 模板 CRUD API
- [ ] Task API 集成 Registry 校验
- [ ] 前端动态表单

### Phase 5: Excel 导入功能（2天）
- [ ] Excel 解析器（openpyxl）
- [ ] Configuration tag 拆分逻辑
- [ ] 导入预览 + 校验 + 确认
