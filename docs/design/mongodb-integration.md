# MongoDB 集成设计：原始采集文档存储

**创建日期**: 2026-07-10
**修订日期**: 2026-07-11（需求评审修正，见附录 C）
**状态**: 评审修正完成，待实现
**关联**: `docs/design/collector-config-model.md`（采集配置建模）、`docs/design/database-schema.md`（PG 表结构）、`backend/app/services/analysis_service.py`（已有 10 个运维报表，不可覆盖）

---

## 一、背景与问题

### 1.1 当前数据架构

MiniHES 采用 PostgreSQL 作为唯一持久化存储。InfluxDB 已弃用，时序读数和汇总落在 PG 的
`col_meter_reading` / `col_reading_daily` 时序表中。系统中有 **25 张 PG 表**覆盖系统管理、设备管理、
采集任务、数据点模板和实验室测试五大模块。

但在实际数据采集场景中，存在一类 PG 难以高效处理的数据：**DLMS/COSEM 采集会话的完整原始文档**。

### 1.2 核心矛盾

| 场景 | PG 的局限 | MongoDB 的优势 |
|------|----------|---------------|
| **单次采集产出 ~1.2 MB 文档** | 需要拆成多表多行存储，丢失文档内聚性 | 单文档完整存储，天然映射 |
| **24 个 sheet 结构灵活多变** | 不同设备型号 sheet 不同，频繁 ALTER TABLE | Schema-free，不同文档结构共存 |
| **720 个 key-value pairs** | 需要 EAV 模型或 JSONB 全量扫描 | 内嵌扁平对象，点路径查询 |
| **Profile buffer（365 天日线 / 96 点负荷曲线）** | 时序表行数爆炸（1 表 × 365 天 = 365 行/表/次采集） | 嵌入数组，一次读取完整曲线 |
| **Excel 导入文档（XMLFunctionLists_Meter_PP.xlsx）** | 结构与关系模型不匹配 | 文档即数据，所见即所得 |

### 1.3 已有但未落地的桥梁

系统已预留了 PG-MongoDB 桥梁机制但从未启用：

```
col_session 表 (PG)                      meter_sessions 集合 (MongoDB)
┌──────────────────────────┐             ┌──────────────────────────┐
│ id: 42                   │             │ _id: ObjectId("...")     │
│ meter_id: 3              │   mongo_*   │ meter_id: 3              │
│ mongo_db: "minihes"      │────指针────→│ collected_at: ...        │
│ mongo_collection: "...   │             │ sheets: { 24 sheets }   │
│ mongo_doc_id: "..."      │             │ key_value_pairs: {...}   │
└──────────────────────────┘             └──────────────────────────┘
```

**问题**：`motor==3.6.0` 已在 `pyproject.toml` 声明，但 app 代码从未 import；`col_session` 的
`mongo_*` 字段只是占位字符串，指向不存在的文档。

### 1.4 分析 API 全部硬编码

当前 `/api/v1/analysis/*` 的 **9 个路由全部返回 hardcoded stub 数据**，前端 `analysis/*` 页面
降级到 `generateDemoXxx()` mock 函数。用户看到的图表全是假数据。

---

## 二、设计目标

| 目标 | 衡量标准 |
|------|---------|
| **MongoDB 作为原始采集文档存储** | 完整保留 DLMS 采集文档（24 sheets / 720 KV / Profile buffers） |
| **落地 PG-MongoDB 桥梁** | `col_session.mongo_doc_id` 指向真实可查文档 |
| **分析 API 真实化** | 9 个 stub 路由改为从 MongoDB 查询真实采集数据 |
| **保持 PG 权威** | PG 仍为主库（用户/设备/任务/权限/结构化读数/汇总），Mongo 仅存原始大文档 |
| **优雅降级** | Mongo 不可用时，分析 API 返回空 + warning，不 crash |

---

## 三、真实数据结构分析

设计依据来自 `docs/testdata/template_meter.json`——这是从真实电表采集设备导出的标准 DLMS 文档
（1.2 MB），也是 `docs/testdata/generate_testdata_mongo.py` 生成测试数据的模板。

### 3.1 文档顶层结构

```
{
  _id:               ObjectId          // MongoDB 主键
  timestamp:         "2025-11-01T..."  // 采集时间戳（字符串）
  source_file:       "...xlsx"          // 来源 Excel 文件路径
  sheets:            { 24 sheets }     // ★ 核心：24 个分类数据表
  key_value_pairs:   { 720 KV }        // ★ 扁平化 key-value 索引
  summary:           { stats }         // 采集结果统计
}
```

### 3.2 sheets 结构（24 个分类表）

每个 sheet 的结构统一：

```javascript
{
  sheet_name: "Energy",
  objects: [
    {
      key:              "Energy.Cumulative A Positive.Value",  // 全局唯一键
      classId:          3,                    // DLMS COSEM 接口类 ID
      obis:             "1.0.1.8.0.255",      // OBIS 码
      obisFormatted:    "1-0:1.8.0.255",      // OBIS 码（冒号格式）
      attributeId:      2,                    // 属性 ID
      attributeName:    "Value",              // 属性名
      controlName:      "Cumulative A Positive",  // 控件名
      value:            1529384,              // 值（BSON 原生 int32，见下方说明）
      timestamp:        "2025-11-01T...",     // 采集时刻
      status:           "success"             // success / failed
    }
  ]
}
```

> **类型说明**：`template_meter.json` 源文件中使用 MongoDB Extended JSON 格式（`{"$numberInt": "1529384"}`），
> 但经过 `mongoimport` 导入或 motor `insert_one` 写入后，这些值会**自动转换为 BSON 原生类型**
>（int32 / int64 / string）。应用层通过 motor 读取时获得的是 Python 原生 `int`/`str`，
> **不需要额外解包**。

### 3.3 各 sheet 内容与大小

| Sheet | 对象数 | 大小 | 内容 |
|-------|--------|------|------|
| Clock | 9 | 3 KB | 时钟、时区、夏令时 |
| Basic Information | 13 | 6 KB | 设备名、序列号、固件版本、签名 |
| Energy | 6 | 2 KB | ★ 累计电能（正向/负向 × 费率 0-6） |
| Instantaneous Data | 60 | 23 KB | ★ 瞬时 V/I/P/PF（三相 + 总） |
| Average Measurement Data | 42 | 16 KB | 平均测量值 |
| Tariff | 15 | 10 KB | 费率信息 |
| Daily Billing | 40 | 17 KB | ★ 日计费 buffer（365 天） |
| Month Billing | 40 | 17 KB | ★ 月计费 buffer（12 月） |
| Load Profile | 47 | 56 KB | ★ 负荷曲线 buffer（96 点/天） |
| Definable Load Profile | 7 | 43 KB | 可定义负荷曲线 |
| Quality Profile | 16 | 184 KB | 电能质量曲线 |
| Power Quality | 40 | 16 KB | 电能质量参数 |
| Event Record | 86 | 64 KB | ★ 事件日志 |
| Image Transfer | 40 | 16 KB | 固件升级镜像传输 |
| M-Bus | 192 | 68 KB | M-Bus 通道配置 |
| LTE Communication Setup | 51 | 19 KB | LTE 通信模块配置 |
| Push Setup | 23 | 9 KB | 推送配置 |
| Association related parameters | 17 | 122 KB | 关联对象参数 |
| 其他 6 个 sheet | 35 | ~40 KB | Display / P1 / Errors / SAS / CommPort / FactoryReset |
| **合计** | **~720** | **~1.2 MB** | |

> ★ 标记的是分析 API 高频查询的 sheet。

### 3.4 Profile Buffer 结构（分析 API 核心数据源）

**Daily Billing buffer**（日计费，365 天）：
```javascript
"Daily Billing.E-meter Daily Billing.Buffer": {
  "0": ["2024-06-01 6 00:00:00 00,FF88,80", 120, 50320, 0, 0, 0],
  "1": ["2024-06-02 7 00:00:00 00,FF88,80", 150, 50470, 0, 0, 0],
  //     ↑ DLMS 时间戳                    ↑ 间隔  ↑ 累计电能  ↑ 费率1-3
  // ... 365 条
}
```

**Load Profile buffer**（负荷曲线，96 点/天，15 分钟间隔）：
```javascript
"Load Profile.Energy Profile.Buffer": {
  "0":  ["2024-06-15 6 00:00:00 00,FF88,80", 8, 50000, 0],
  "1":  ["2024-06-15 6 00:15:00 00,FF88,80", 8, 50042, 0],
  //      ↑ DLMS 时间戳                    ↑ 状态  ↑ 累计电能  ↑ 费率1
  // ... 96 条
}
```

**Instantaneous Data**（瞬时量，key-value）：
```javascript
"Instantaneous Data.Instantaneous Voltage L1.Value": 231,   // V
"Instantaneous Data.Instantaneous Current L1.Value": 12,    // A
"Instantaneous Data.Instantaneous active power (+P) Total": 320,  // W
```

---

## 四、集合 Schema 设计

### 4.1 核心集合：`meter_sessions`

**用途**：存储每次 DLMS 采集会话的完整原始文档。

```
Database:   minihes                    ← 统一用一个 DB（不按项目名分库）
Collection: meter_sessions             ← 每次采集 = 1 个文档
预估大小:   ~1.2 MB / 文档（在 16MB 限制内，安全）
```

**文档结构**：

```javascript
{
  _id: ObjectId("..."),

  // ═══════════════════════════════════════════
  //  采集会话元数据（可索引、可查询）
  // ═══════════════════════════════════════════

  session_id: 42,                      // PG col_session.id（反向定位）
  meter_id: 3,                         // PG dev_meter.id（★ 核心索引字段）
  meter_serial: "KFM1020110000001",    // 电表序列号（冗余，方便无 JOIN 查询）
  project_id: 1,                       // PG dev_project.id
  project_name: "Puma-01_DCPP",        // 项目名（冗余）
  task_id: null,                       // PG col_task.id（nullable）

  // ═══════════════════════════════════════════
  //  采集时间
  // ═══════════════════════════════════════════

  collected_at: ISODate("2025-11-01T09:33:56Z"),  // ★ 采集时刻
  imported_at: ISODate("2026-07-10T..."),         // 入库时刻

  // ═══════════════════════════════════════════
  //  来源
  // ═══════════════════════════════════════════

  source: "import",                    // auto（实时采集）/ manual / import（Excel 导入）
  source_file: "XMLFunctionLists_Meter_PP.xlsx",
  connection_type: "HDLC",             // HDLC / TCP / WPDU / FEP

  // ═══════════════════════════════════════════
  //  采集结果摘要（冗余自 col_session，避免跨库 JOIN）
  // ═══════════════════════════════════════════
  //  注意：以下 top_points/success_points/failed_points 是应用层写入的
  //  归一化字段，来源于原始文档 summary.total_read 等。
  //  原始 summary 字段保留在下方 summary 子对象中，不做改名。

  status: "success",                   // 数据质量枚举（见 4.5 枚举映射表）
  total_points: 796,                   // 归一化：= summary.total_read
  success_points: 794,                 // 归一化：= summary.total_success
  failed_points: 2,                    // 归一化：= summary.total_failed

  // ═══════════════════════════════════════════
  //  ★ DLMS 原始数据：sheets（完整保留 24 个 sheet，不拆解）
  // ═══════════════════════════════════════════

  sheets: {
    "Clock": {
      sheet_name: "Clock",
      objects: [
        {
          key: "Clock.Clock.Time",
          classId: 8,
          obis: "0.0.1.0.0.255",
          obisFormatted: "0-0:1.0.0.255",
          attributeId: 2,
          attributeName: "Time",
          controlName: "Clock",
          value: "2025-11-10 01 15:38:38 00,FFC4,00",
          timestamp: ISODate("2025-11-01T09:33:57Z"),
          status: "success"
        },
        // ... 9 objects
      ]
    },
    "Energy": { sheet_name: "Energy", objects: [/* 6 objects */] },
    "Instantaneous Data": { objects: [/* 60 objects */] },
    "Daily Billing": { objects: [/* 40 objects，含 365 天 buffer */] },
    "Month Billing": { objects: [/* 40 objects，含 12 月 buffer */] },
    "Load Profile": { objects: [/* 47 objects，含 96 点 buffer */] },
    "Event Record": { objects: [/* 86 objects */] },
    // ... 共 24 sheets
  },

  // ═══════════════════════════════════════════
  //  ★ key_value_pairs 扁平索引（保留原始 720 KV）
  //  分析 API 高频查询路径：O(1) 点路径取值
  // ═══════════════════════════════════════════

  key_value_pairs: {
    "Clock.Clock.Time": "2025-11-10 01 15:38:38 00,FFC4,00",
    "Energy.Cumulative A Positive.Value": 1529384,
    "Instantaneous Data.Instantaneous Voltage L1.Value": 231,
    "Instantaneous Data.Instantaneous Current L1.Value": 12,
    // ... 720 pairs
  },

  // ═══════════════════════════════════════════
  //  summary（原始采集工具产出的统计，键名保持原样不改）
  // ═══════════════════════════════════════════
  //  ⚠️ 注意：真实键名是 total_read（不是 total_objects），
  //     没有 duration_ms（该值在 PG col_session 中计算）。

  summary: {
    total_read:     796,                // ★ 正确键名（非 total_objects）
    total_success:  794,
    total_failed:   2,
    sheet_count:    24                  // ★ 正确键名（非 total_sheets）
  },

  // ═══════════════════════════════════════════
  //  文档版本（schema 演进管理）
  // ═══════════════════════════════════════════

  schema_version: 1
}
```

### 4.2 索引设计

```javascript
// ─── 主查询路径：按电表 + 时间查最新/历史采集（分析 API 最常用）───
db.meter_sessions.createIndex(
  { "meter_id": 1, "collected_at": -1 },
  { name: "idx_meter_time" }
);

// ─── 按项目 + 时间范围批量查（一致性检查、项目级报表）───
db.meter_sessions.createIndex(
  { "project_id": 1, "collected_at": -1 },
  { name: "idx_project_time" }
);

// ─── 按 session_id 反查（从 PG col_session 跳转）───
db.meter_sessions.createIndex(
  { "session_id": 1 },
  { name: "idx_session_id", unique: true }
);

// ─── 按电表序列号查（无 PG 上下文时使用）───
db.meter_sessions.createIndex(
  { "meter_serial": 1, "collected_at": -1 },
  { name: "idx_serial_time" }
);

// ─── key_value_pairs 查询策略 ───
// Phase 1 不创建 wildcard 索引。原因：
//   1. 分析 API 实际查询路径是 "先按 meter_id 找到文档，再 Python 层取 KV"，
//      不需要 Mongo 层对 KV 子键建索引
//   2. wildcard 索引会为 720 个子键各建条目，索引膨胀与文档数成正比
//   3. 文档量 < 10 万时全量加载 KV 的开销可忽略
// 未来如有 "按 KV 值过滤文档" 的需求，再评估按需创建针对性索引。
```

> **TTL 策略**：暂不启用 TTL 自动过期。数据归档由 PG `sys_data_archive` 表统一管理，
> 手动触发归档脚本（将旧文档移到冷存储集合 `meter_sessions_archive`）。

### 4.3 Schema 验证器（$jsonSchema）

为 `meter_sessions` 集合添加数据库层面验证：

```javascript
db.createCollection("meter_sessions", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["meter_id", "collected_at", "sheets", "schema_version"],
      properties: {
        meter_id:        { bsonType: "int", description: "PG dev_meter.id，必填" },
        meter_serial:    { bsonType: "string" },
        session_id:      { bsonType: "int", description: "PG col_session.id" },
        project_id:      { bsonType: "int" },
        task_id:         { bsonType: ["int", "null"] },
        collected_at:    { bsonType: "date", description: "采集时刻，必填" },
        imported_at:     { bsonType: "date" },
        source:          { enum: ["auto", "manual", "import"] },
        source_file:     { bsonType: "string" },
        connection_type: { enum: ["HDLC", "TCP", "WPDU", "FEP", ""] },
        status:          { enum: ["success", "partial", "failed"] },
        sheets:          { bsonType: "object", description: "DLMS 24 sheets 完整文档，必填" },
        key_value_pairs: { bsonType: "object" },
        summary:         { bsonType: "object" },
        schema_version:  { bsonType: "int", minimum: 1, description: "文档 schema 版本，必填" }
      }
    }
  },
  validationLevel: "moderate",   // 已有文档不强制验证
  validationAction: "warn"       // 先 warn，观察稳定后改 error
})
```

### 4.4 辅助集合：`meter_events`（可选，Phase 2）

**用途**：从 Event Record sheet 拆出的结构化事件，供告警引擎快速查询。

> **决策**：Phase 1 **不建此集合**。Event Record 直接从 `meter_sessions.sheets["Event Record"]`
> 查询（86 objects 量级不大）。如果后续告警引擎需要高频查事件，再拆出到独立集合并加索引。

预留设计（Phase 2 按需启用）：

```javascript
// collection: meter_events
{
  _id: ObjectId("..."),
  session_id: 42,
  meter_id: 3,
  meter_serial: "KFM1020110000001",
  event_code: "00010000",             // DLMS event code
  event_name: "Power up",
  event_time: ISODate("2025-06-15T03:00:00Z"),
  severity: "info",                   // info / warning / critical
  raw: { /* 完整原始 object */ }
}
```

### 4.5 status 枚举映射（PG ↔ Mongo）

PG 和 MongoDB 的 `status` 字段使用**不同的枚举**，两者语义不同：

| 层 | 字段 | 枚举值 | 语义 |
|----|------|--------|------|
| PG `col_session.status` | 生命周期 | `pending` / `running` / `completed` / `failed` | 执行状态（调度引擎视角） |
| Mongo `meter_sessions.status` | 数据质量 | `success` / `partial` / `failed` | 采集成功率（数据质量视角） |

**映射规则**（`session_writer` 中使用）：

| Mongo status | PG status | 条件 |
|-------------|-----------|------|
| `"success"` | `"completed"` | `total_failed == 0` |
| `"partial"` | `"completed"` | `0 < total_failed < total_read` |
| `"failed"`  | `"failed"`   | `total_read == 0` 或 `total_failed == total_read` |

```python
# session_writer 中的映射函数
def _map_status(mongo_status: str) -> str:
    """Mongo 数据质量枚举 → PG 生命周期枚举。"""
    return "failed" if mongo_status == "failed" else "completed"
```

> PG 的 `pending`/`running` 两个中间态仅在实时采集引擎执行期间使用，
> 不存在于 Mongo 文档中（文档只在采集完成后写入）。

---

## 五、应用层架构

### 5.1 MongoDB 连接层

**新增文件**：`backend/app/core/mongo.py`

```python
"""MongoDB 异步客户端（motor）。

职责：
  - 单例 AsyncIOMotorClient（进程级连接池）
  - 提供 get_mongo() 依赖注入
  - 读取 MONGODB_URL 环境变量
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """获取/初始化 Motor 客户端单例（懒加载）。"""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URL)
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    """获取默认数据库句柄。"""
    return get_mongo_client()[settings.MONGODB_DATABASE]


async def get_mongo() -> AsyncIOMotorDatabase:
    """FastAPI 依赖注入入口。"""
    return get_mongo_db()


async def close_mongo():
    """应用关闭时清理连接。"""
    global _client
    if _client:
        _client.close()
        _client = None
```

**修改文件**：`backend/app/core/config.py`

```python
# MongoDB（原始采集文档存储）
MONGODB_URL: str = "mongodb://localhost:27017"
MONGODB_DATABASE: str = "minihes"
```

**修改文件**：`backend/main.py` — lifespan 注册关闭逻辑

```python
from contextlib import asynccontextmanager
from app.core.database import engine
from app.core.mongo import close_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
    await close_mongo()   # ← 新增


app = FastAPI(title="MiniHES API", lifespan=lifespan)
```

### 5.2 依赖注入

**修改文件**：`backend/app/core/dependencies.py`

```python
from app.core.mongo import get_mongo_db
from motor.motor_asyncio import AsyncIOMotorDatabase

MongoDb = Annotated[AsyncIOMotorDatabase, Depends(get_mongo)]
# 与 DbSession / CurrentUser 并列使用
```

### 5.3 数据访问层：MongoSessionRepo

**新增文件**：`backend/app/services/mongo_session_repo.py`

```python
"""MongoDB 采集会话数据访问层。

所有对 meter_sessions 集合的读写都通过此类，
保证投影策略、错误处理、日志记录的一致性。
"""
from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoSessionRepo:
    """采集会话 MongoDB 数据访问对象。"""

    COLLECTION = "meter_sessions"

    # 常用投影：分析 API 只需元数据 + 特定 sheet，避免加载完整 1.2MB
    PROJ_META = {
        "meter_id": 1, "meter_serial": 1, "collected_at": 1,
        "status": 1, "summary": 1, "_id": 0,
    }
    PROJ_DAILY = {
        "key_value_pairs": 1,
        "sheets.Daily Billing": 1,
        "collected_at": 1, "_id": 0,
    }
    PROJ_LOAD_PROFILE = {
        "sheets.Load Profile": 1,
        "collected_at": 1, "_id": 0,
    }
    PROJ_INSTANTANEOUS = {
        "sheets.Instantaneous Data": 1,
        "key_value_pairs": 1,
        "_id": 0,
    }

    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db[self.COLLECTION]

    # ─── 写入 ───

    async def insert_session(self, doc: dict) -> str:
        """写入完整采集文档，返回 _id（hex 字符串）。"""
        result = await self.col.insert_one(doc)
        return str(result.inserted_id)

    # ─── 单文档查询 ───

    async def get_by_doc_id(self, mongo_doc_id: str) -> dict | None:
        """按 col_session.mongo_doc_id 查原始文档。"""
        from bson import ObjectId
        try:
            return await self.col.find_one({"_id": ObjectId(mongo_doc_id)})
        except Exception:
            # mongo_doc_id 可能是非 ObjectId 格式（旧 seed 数据）
            return await self.col.find_one({"_id": mongo_doc_id})

    async def get_latest_by_meter(
        self, meter_id: int, projection: dict | None = None
    ) -> dict | None:
        """查某电表最新一次采集文档（分析 API 最常用）。"""
        return await self.col.find_one(
            {"meter_id": meter_id},
            sort=[("collected_at", -1)],
            projection=projection or self.PROJ_META,
        )

    async def get_sessions_by_date_range(
        self, meter_id: int, start: datetime, end: datetime, limit: int = 200
    ) -> list[dict]:
        """按时间范围查历史采集文档列表。"""
        cursor = self.col.find(
            {
                "meter_id": meter_id,
                "collected_at": {"$gte": start, "$lte": end},
            },
            projection=self.PROJ_META,
        ).sort("collected_at", -1)
        return await cursor.to_list(length=limit)

    # ─── 分析 API 专用查询（带投影优化） ───

    async def get_daily_billing(self, meter_id: int, days: int = 30) -> list[dict]:
        """从最新采集文档的 Daily Billing buffer 提取日用电曲线。"""
        doc = await self.get_latest_by_meter(meter_id, projection=self.PROJ_DAILY)
        if not doc:
            return []
        return self._parse_daily_billing_buffer(doc, days)

    async def get_load_profile(self, meter_id: int) -> list[dict]:
        """从最新采集文档的 Load Profile buffer 提取 96 点负荷曲线。"""
        doc = await self.get_latest_by_meter(meter_id, projection=self.PROJ_LOAD_PROFILE)
        if not doc:
            return []
        return self._parse_load_profile_buffer(doc)

    async def get_instantaneous(self, meter_id: int) -> dict:
        """从最新采集文档的 Instantaneous Data sheet 提取瞬时量。"""
        doc = await self.get_latest_by_meter(meter_id, projection=self.PROJ_INSTANTANEOUS)
        if not doc:
            return {}
        return self._parse_instantaneous(doc)

    async def get_energy(self, meter_id: int) -> dict:
        """从 key_value_pairs 提取累计电能。"""
        doc = await self.get_latest_by_meter(
            meter_id, projection={"key_value_pairs": 1, "_id": 0}
        )
        if not doc:
            return {}
        kvp = doc.get("key_value_pairs", {})
        return {
            "cumulative_positive": kvp.get("Energy.Cumulative A Positive.Value"),
            "cumulative_positive_r1": kvp.get("Energy.Cumulative A Positive rate1.Value"),
            "cumulative_positive_r2": kvp.get("Energy.Cumulative A Positive rate2.Value"),
            "cumulative_negative": kvp.get("Energy.Cumulative A Negative.Value"),
        }

    async def get_kv_value(self, meter_id: int, key: str) -> Any:
        """查 key_value_pairs 中某个 key 的值。

        注意：key 含点号（如 'Clock.Clock.Time'），不能用于 Mongo projection
        的点路径语法（会被解释为嵌套路径）。必须取整个 key_value_pairs 再 Python 层取值。
        """
        doc = await self.get_latest_by_meter(
            meter_id, projection={"key_value_pairs": 1, "_id": 0}
        )
        if not doc:
            return None
        return doc.get("key_value_pairs", {}).get(key)

    # ─── Buffer 解析（私有方法，统一从 key_value_pairs 读取） ───

    @staticmethod
    def _parse_daily_billing_buffer(doc: dict, days: int) -> list[dict]:
        """解析 Daily Billing buffer 为结构化日用电列表。

        buffer 格式：{ "0": [timestamp, interval, energy, r1, r2, r3], ... }
        数据来源：key_value_pairs["Daily Billing.E-meter Daily Billing.Buffer"]
        """
        kvp = doc.get("key_value_pairs", {})
        buffer_key = "Daily Billing.E-meter Daily Billing.Buffer"
        buffer = kvp.get(buffer_key, {})
        if not isinstance(buffer, dict):
            return []

        result = []
        for idx, entry in buffer.items():
            if not isinstance(entry, list) or len(entry) < 3:
                continue
            result.append({
                "index": int(idx),
                "raw_timestamp": entry[0],
                "interval_minutes": entry[1],
                "cumulative_energy": entry[2],
                "rate1": entry[3] if len(entry) > 3 else 0,
                "rate2": entry[4] if len(entry) > 4 else 0,
                "rate3": entry[5] if len(entry) > 5 else 0,
            })

        # 按 index 排序，取最近 N 天
        result.sort(key=lambda x: x["index"], reverse=True)
        return result[:days]

    @staticmethod
    def _parse_load_profile_buffer(doc: dict) -> list[dict]:
        """解析 Load Profile buffer 为 96 点负荷曲线。

        buffer 格式：{ "0": [timestamp, status, energy, rate1], ... }
        数据来源：key_value_pairs["Load Profile.Energy Profile.Buffer"]
        （与 _parse_daily_billing_buffer 统一从 key_value_pairs 读取）
        """
        kvp = doc.get("key_value_pairs", {})
        buffer_key = "Load Profile.Energy Profile.Buffer"
        buffer = kvp.get(buffer_key, {})
        if not isinstance(buffer, dict):
            return []

        result = []
        prev_energy = None
        for idx in sorted(buffer.keys(), key=int):
            entry = buffer[idx]
            if not isinstance(entry, list) or len(entry) < 3:
                continue
            energy = entry[2]
            delta = energy - prev_energy if prev_energy is not None else 0
            result.append({
                "index": int(idx),
                "time_slot": f"{int(idx) * 15 // 60:02d}:{int(idx) * 15 % 60:02d}",
                "raw_timestamp": entry[0],
                "status": entry[1],
                "cumulative_energy": energy,
                "interval_delta": delta,  # 15 分钟用电增量
            })
            prev_energy = energy
        return result

    @staticmethod
    def _parse_instantaneous(doc: dict) -> dict:
        """解析 Instantaneous Data sheet 为瞬时量字典。"""
        kvp = doc.get("key_value_pairs", {})
        prefix = "Instantaneous Data."
        result = {}
        for key, value in kvp.items():
            if key.startswith(prefix) and key.endswith(".Value"):
                short_name = key[len(prefix):-len(".Value")]
                result[short_name] = value
        return result
```

### 5.4 采集写入路径

**新增文件**：`backend/app/services/collector/session_writer.py`

> **PG-Mongo 双写一致性策略**（P0-4 修正）：
>
> PG 和 MongoDB 之间没有分布式事务，因此采用 **"PG 先登记 → Mongo 写入 → PG 补全"** 模式：
> 1. 先在 PG 创建 `col_session` 记录（`status=pending`），获得 `session.id`
> 2. 将 `session.id` 写入 Mongo 文档（作为 `session_id` 字段）
> 3. Mongo 写入成功后，更新 PG 记录 `status`/`mongo_doc_id`
> 4. 如果步骤 2-3 失败，PG 记录保持 `status=pending`，由 GC 任务定期清理
>
> 这样保证了：PG 中 `status != pending` 的记录一定有对应的 Mongo 文档。
> 反之 Mongo 中的孤儿文档（PG 已回滚）可通过定期扫描 `session_id` 是否在 PG 存在来检测。

```python
"""采集会话写入路径。

将 DLMS 采集引擎产出的原始文档写入 MongoDB，
同时在 PG col_session 表创建桥梁记录。

双写一致性策略见上方文档注释。
"""
import datetime
import logging

import bson
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.mongo import get_mongo_db
from app.models.session import CollectionSession
from app.services.mongo_session_repo import MongoSessionRepo

logger = logging.getLogger(__name__)

_MAX_DOC_BYTES = 15 * 1024 * 1024  # 15MB 安全阈值（16MB 为硬限）


async def save_collection_session(
    db: AsyncSession,
    meter_id: int,
    meter_serial: str,
    project_id: int | None,
    project_name: str,
    raw_doc: dict,                # 即 template_meter.json 那种完整结构
    source: str = "import",
    source_file: str = "",
    connection_type: str = "HDLC",
    task_id: int | None = None,
) -> CollectionSession:
    """将原始采集文档写入 Mongo，并在 PG 创建桥梁记录。

    返回：PG CollectionSession 对象
    """
    mongo_db = get_mongo_db()
    repo = MongoSessionRepo(mongo_db)

    collected_at = _parse_timestamp(raw_doc.get("timestamp"))
    imported_at = datetime.datetime.now(datetime.timezone.utc)
    summary = raw_doc.get("summary", {})

    # ★ 正确读取 summary 键名（P0-1 修正）
    total_read = summary.get("total_read", 0)
    total_success = summary.get("total_success", 0)
    total_failed = summary.get("total_failed", 0)

    # ── 步骤 1: PG 先登记（status=pending），获取 session.id ──
    session = CollectionSession(
        meter_id=meter_id,
        project_id=project_id,
        task_id=task_id,
        mongo_db=settings.MONGODB_DATABASE,
        mongo_collection=MongoSessionRepo.COLLECTION,
        mongo_doc_id="",                # 待 Mongo 写入后补全
        source=source,
        source_file=source_file,
        started_at=collected_at,
        finished_at=imported_at,
        duration_ms=int((imported_at - collected_at).total_seconds() * 1000),
        status="pending",               # 先登记为 pending
        total_read=total_read,
        total_success=total_success,
        total_failed=total_failed,
        sheet_count=len(raw_doc.get("sheets", {})),
        connection_type=connection_type,
    )
    db.add(session)
    await db.flush()  # 获取 session.id（不 commit，保持事务）

    # ── 步骤 2: 构建 Mongo 文档（含 session_id 反向指针） ──
    mongo_status = _derive_status(total_read, total_failed)
    mongo_doc = {
        "session_id": session.id,       # PG 反向指针
        "meter_id": meter_id,
        "meter_serial": meter_serial,
        "project_id": project_id,
        "project_name": project_name,
        "task_id": task_id,
        "collected_at": collected_at,
        "imported_at": imported_at,
        "source": source,
        "source_file": source_file,
        "connection_type": connection_type,
        "status": mongo_status,
        "total_points": total_read,
        "success_points": total_success,
        "failed_points": total_failed,
        "sheets": raw_doc.get("sheets", {}),
        "key_value_pairs": raw_doc.get("key_value_pairs", {}),
        "summary": summary,
        "schema_version": 1,
    }

    # ── 步骤 2a: 文档大小检查（P1-2 修正） ──
    doc_size = len(bson.encode(mongo_doc))
    if doc_size > _MAX_DOC_BYTES:
        raise ValueError(
            f"MongoDB 文档大小 {doc_size / 1024 / 1024:.1f}MB 超过 15MB 安全阈值，"
            f"需拆分 Profile buffer 到独立集合"
        )

    # ── 步骤 3: 写入 Mongo ──
    mongo_id = await repo.insert_session(mongo_doc)

    # ── 步骤 4: 更新 PG 记录（补全 mongo_doc_id + 状态映射） ──
    session.mongo_doc_id = mongo_id
    session.status = _map_status(mongo_status)  # PG 生命周期枚举
    await db.flush()

    return session


def _parse_timestamp(ts: str | None) -> datetime.datetime:
    """解析采集文档 timestamp 字段（ISO 格式字符串）。"""
    if not ts:
        return datetime.datetime.now(datetime.timezone.utc)
    try:
        return datetime.datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return datetime.datetime.now(datetime.timezone.utc)


def _derive_status(total_read: int, total_failed: int) -> str:
    """根据采集统计推导 Mongo 数据质量状态。

    返回值：success / partial / failed（Mongo 枚举）
    """
    if total_read == 0:
        return "failed"
    if total_failed == 0:
        return "success"
    if total_failed < total_read:
        return "partial"
    return "failed"


def _map_status(mongo_status: str) -> str:
    """Mongo 数据质量枚举 → PG 生命周期枚举。

    映射规则见文档 4.5 节。
    """
    return "failed" if mongo_status == "failed" else "completed"
```

### 5.5 分析 Service 层

> **⚠️ 重要约束（P0-2 修正）**：
>
> `backend/app/services/analysis_service.py` **已存在且包含 10 个已实现的运维报表函数**
>（`get_comm_success_rate`/`get_non_comm_devices`/`get_read_completeness`/...），
> 全部使用 PG 查询并有完善的 demo 降级机制。
>
> **Mongo 集成不得修改或覆盖这些已有函数。** 新增的 Mongo 相关分析逻辑应放在
> **独立文件** `backend/app/services/analysis_mongo_service.py` 中，
> 只服务于前 9 个 stub 路由（`daily`/`compare`/`consistency`/`data-quality`/`reports` 等）。

**新增文件**：`backend/app/services/analysis_mongo_service.py`

```python
"""数据分析业务逻辑层。

从 PostgreSQL（元数据 + 汇总统计）和 MongoDB（原始采集文档）
联合查询，为 analysis API 提供真实数据。
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meter import Meter
from app.models.task import DataQuality
from app.services.mongo_session_repo import MongoSessionRepo


class AnalysisService:
    """分析服务：PG 元数据 + Mongo 原始数据联合查询。"""

    def __init__(self, db: AsyncSession, mongo_repo: MongoSessionRepo):
        self.db = db
        self.mongo = mongo_repo

    async def daily_analysis(self, meter_id: int, target_date: date | None = None):
        """日线分析：日用电曲线 + 瞬时量。

        数据来源：
          - PG: 电表元信息（名称、类型）
          - Mongo: Daily Billing buffer（日用电）+ Instantaneous Data（瞬时量）
        """
        meter = await self.db.get(Meter, meter_id)
        if not meter:
            return None

        daily_billing = await self.mongo.get_daily_billing(meter_id, days=30)
        instantaneous = await self.mongo.get_instantaneous(meter_id)
        energy = await self.mongo.get_energy(meter_id)

        # 构造最近一天的 24h 曲线（从 Load Profile 的 96 点聚合为 24h）
        load_profile = await self.mongo.get_load_profile(meter_id)
        hourly_energy = self._aggregate_to_hourly(load_profile)

        return {
            "meter_id": meter_id,
            "meter_name": meter.meter_name,
            "date": target_date.isoformat() if target_date else None,
            "hours": [f"{h:02d}:00" for h in range(24)],
            "energy": hourly_energy,
            "daily_billing": daily_billing[:7],   # 最近 7 天
            "instantaneous": instantaneous,
            "total_energy": energy.get("cumulative_positive"),
            "power_factor": instantaneous.get("Power factor"),
        }

    async def compare_meters(self, meter_ids: list[int], metric: str = "energy"):
        """多表对比分析。

        metric: energy（累计电能）/ voltage（三相电压）/ power（功率）
        """
        results = []
        for meter_id in meter_ids:
            meter = await self.db.get(Meter, meter_id)
            if not meter:
                continue
            if metric == "energy":
                data = await self.mongo.get_energy(meter_id)
            elif metric == "voltage":
                inst = await self.mongo.get_instantaneous(meter_id)
                data = {
                    "voltage_l1": inst.get("Instantaneous Voltage L1"),
                    "voltage_l2": inst.get("Instantaneous Voltage L2"),
                    "voltage_l3": inst.get("Instantaneous Voltage L3"),
                }
            else:
                inst = await self.mongo.get_instantaneous(meter_id)
                data = {
                    "power_total": inst.get("Instantaneous active power (+P) Total"),
                    "power_l1": inst.get("Instantaneous active power (+P) L1"),
                    "power_l2": inst.get("Instantaneous active power (+P) L2"),
                    "power_l3": inst.get("Instantaneous active power (+P) L3"),
                }
            results.append({
                "meter_id": meter_id,
                "meter_name": meter.meter_name,
                "meter_serial": meter.serial_number,
                **data,
            })
        return results

    async def load_profile(self, meter_id: int):
        """96 点负荷曲线。"""
        meter = await self.db.get(Meter, meter_id)
        profile = await self.mongo.get_load_profile(meter_id)
        return {
            "meter_id": meter_id,
            "meter_name": meter.meter_name if meter else None,
            "points": profile,
            "total_points": len(profile),
        }

    async def data_quality(self, meter_id: int | None = None, page: int = 1, page_size: int = 20):
        """数据质量分析（来源 PG col_data_quality）。"""
        query = select(DataQuality).order_by(DataQuality.stat_date.desc())
        if meter_id:
            query = query.where(DataQuality.meter_id == meter_id)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        # 关联电表名
        meter_ids = {item.meter_id for item in items}
        meters = {}
        if meter_ids:
            meter_result = await self.db.execute(
                select(Meter).where(Meter.id.in_(meter_ids))
            )
            meters = {m.id: m for m in meter_result.scalars()}

        return {
            "items": [
                {
                    "id": item.id,
                    "meter_id": item.meter_id,
                    "meter_name": meters[item.meter_id].meter_name if item.meter_id in meters else "",
                    "date": item.stat_date.isoformat() if item.stat_date else None,
                    "completeness": round(item.success_points / item.total_points * 100, 1) if item.total_points else 0,
                    "accuracy": float(item.quality_score) if item.quality_score else None,
                    "abnormal_count": item.abnormal_count,
                    "first_collect_time": item.first_collect_time.isoformat() if item.first_collect_time else None,
                    "last_collect_time": item.last_collect_time.isoformat() if item.last_collect_time else None,
                }
                for item in items
            ],
            "total": len(items),
        }

    @staticmethod
    def _aggregate_to_hourly(load_profile: list[dict]) -> list[str]:
        """将 96 点（15min）负荷曲线聚合为 24h 用电。"""
        if not load_profile:
            return ["0"] * 24
        hourly = [0.0] * 24
        for point in load_profile:
            hour = point.get("index", 0) * 15 // 60
            if 0 <= hour < 24:
                hourly[hour] += point.get("interval_delta", 0)
        return [str(round(v, 2)) for v in hourly]
```

---

## 六、分析 API 端点改造

**修改文件**：`backend/app/api/v1/endpoints/analysis.py`

> **⚠️ P0-2 关键约束**：
>
> `analysis.py` 当前有 **19 个路由**：
> - **前 9 个**（第 10-127 行）：hardcoded stub，是本次改造对象
> - **后 10 个**（第 130-327 行，运维报表）：**已实现真实 PG 查询**，调用
>   `analysis_service.py` 中的 10 个函数，**严禁覆盖**
>
> 本节只涉及前 9 个 stub 路由的改造。运维报表部分不做任何修改。

### 6.1 路由改造对照表（仅前 9 个 stub 路由）

| 路由 | 当前 | 改造后 | 数据来源 |
|------|------|--------|---------|
| `GET /analysis/daily` | hardcoded 24h 数组 | Mongo 真实数据 + 降级 | Mongo: Daily Billing + Load Profile |
| `GET /analysis/daily/export` | "待实现" | CSV 导出 | 同上 |
| `POST /analysis/compare` | echo body | 多表对比 | Mongo: Energy / Instantaneous |
| `GET /analysis/consistency` | hardcoded 2 items | 一致性检查 | PG col_data_quality + Mongo |
| `POST /analysis/consistency/check` | "已触发" | 触发检查 | PG + Mongo |
| `GET /analysis/data-quality` | hardcoded 1 item | 数据质量 | PG col_data_quality |
| `GET /analysis/data-quality/export` | "待实现" | CSV 导出 | 同上 |
| `GET /analysis/reports` | hardcoded 2 items | 报告列表 | PG lab_test_report |
| `GET /analysis/reports/{id}/export` | "待实现" | PDF 导出 | PG |

> **以下 10 个运维报表路由不在改造范围内**（已有真实实现）：
> `comm-success-rate`, `non-comm-devices`, `read-completeness`, `retry-analysis`,
> `open-alarms-report`, `alarm-trend`, `device-health`, `signal-aging`,
> `consumption-trend`, `ondemand-history`

### 6.2 示例：`/analysis/daily` 改造

```python
from app.core.dependencies import CurrentUser, DbSession, MongoDb
from app.core.exceptions import BusinessException
from app.services.analysis_mongo_service import AnalysisMongoService  # ← 新文件
from app.services.mongo_session_repo import MongoSessionRepo


@router.get("/daily")
async def daily_analysis(
    meter_id: int = Query(default=1),
    target_date: date | None = Query(None, alias="date"),
    db: DbSession = ...,
    mongo: MongoDb = ...,
    _user: CurrentUser = ...,
):
    """日线分析。

    数据来源：MongoDB 最新采集文档的 Daily Billing + Instantaneous Data + Load Profile。
    Mongo 不可用或无数据时返回空结构 + warning。
    """
    try:
        service = AnalysisMongoService(db, MongoSessionRepo(mongo))
        result = await service.daily_analysis(meter_id, target_date)
        if result is None:
            raise BusinessException(code=404, message=f"电表 {meter_id} 不存在")
        return success(result)
    except BusinessException:
        raise
    except Exception as e:
        # Mongo 不可用时优雅降级
        return success({
            "meter_id": meter_id,
            "warning": f"采集数据暂不可用: {e}",
            "hours": [f"{h:02d}:00" for h in range(24)],
            "energy": ["0"] * 24,
            "daily_billing": [],
            "instantaneous": {},
        })
```

---

## 七、数据流全景

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MiniHES 数据流全景                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   数据源                                                                 │
│   ┌──────────────┐   ┌──────────────────┐                               │
│   │  电表设备     │   │  Excel 导入文件   │                               │
│   │ (DLMS 采集)  │   │ (XMLFunctionLists)│                               │
│   └──────┬───────┘   └────────┬─────────┘                               │
│          │                    │                                          │
│          ▼                    ▼                                          │
│   ┌──────────────────────────────────────┐                               │
│   │     采集引擎 / Excel 导入器           │                               │
│   │     session_writer.save_collection_  │                               │
│   │              session()               │                               │
│   └──────────┬───────────────┬───────────┘                               │
│              │               │                                            │
│      ┌───────▼───────┐  ┌───▼────────────────────┐                       │
│      │  MongoDB      │  │  PostgreSQL             │                       │
│      │  meter_       │  │  col_session            │                       │
│      │  sessions     │◄─┤  (mongo_doc_id 指针)    │                       │
│      │               │  │                         │                       │
│      │ • sheets (24) │  │  col_meter_reading      │                       │
│      │ • key_value_  │  │  (点值读数)              │                       │
│      │   pairs(720)  │  │                         │                       │
│      │ • summary     │  │  col_reading_daily      │                       │
│      └──────┬────────┘  │  (日汇总)               │                       │
│             │           │                         │                       │
│             │           │  col_data_quality       │                       │
│             │           │  dev_meter (元数据)     │                       │
│             │           └────────────┬────────────┘                       │
│             │                        │                                    │
│             ▼                        ▼                                    │
│   ┌────────────────────────────────────────────────┐                     │
│   │          AnalysisService                        │                     │
│   │  ┌─────────────┐      ┌──────────────┐         │                     │
│   │  │ Mongo 查询   │      │  PG 查询      │         │                     │
│   │  │ • 日线曲线   │      │  • 电表名     │         │                     │
│   │  │ • 负荷曲线   │      │  • 数据质量   │         │                     │
│   │  │ • 瞬时量     │      │  • 汇总统计   │         │                     │
│   │  │ • 累计电能   │      │  • 测试报告   │         │                     │
│   │  └─────────────┘      └──────────────┘         │                     │
│   └────────────────────────┬───────────────────────┘                     │
│                            ▼                                             │
│                   ┌─────────────────┐                                    │
│                   │ /api/v1/analysis│                                    │
│                   │  • /daily       │                                    │
│                   │  • /compare     │                                    │
│                   │  • /load-profile│                                    │
│                   │  • /consistency │                                    │
│                   │  • /data-quality│                                    │
│                   │  (真实数据 ✓)   │                                    │
│                   └─────────────────┘                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 七·补、数据迁移策略（P0-3 修正）

### 问题

现有测试数据使用 `generate_testdata_mongo.py` 生成，拓扑为：
```
3 个数据库（按项目名命名）× 8 个集合/库（按电表序列号命名）= 24 个集合
```
- DB: `Cusk-01_DCPP_DailyCheck` / `Andromeda-01_DailyCheck` / `Draco-01_DCPP_DailyCheck`
- Collection: `KFM2025030100001` / `KFM2025030100002` / ...
- 每集合 1 个文档，无 `meter_id`/`session_id`/`collected_at`/`schema_version` 等字段

新设计为：单库 `minihes` × 单集合 `meter_sessions`，每文档一个采集会话。

### 迁移方案：一次性迁移脚本

**新增文件**：`scripts/migrate_legacy_mongo.py`

```python
"""将旧拓扑（按项目分库 × 按电表分集合）迁移到新拓扑（单库单集合）。

用法：
    python scripts/migrate_legacy_mongo.py

    # 干跑模式（不写入，只统计）
    python scripts/migrate_legacy_mongo.py --dry-run
"""
import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# 旧数据库 → 项目 ID 映射（需根据 PG dev_project 表实际值调整）
LEGACY_DB_MAP = {
    "Cusk-01_DCPP_DailyCheck":     {"project_id": 1, "project_name": "Cusk-01"},
    "Andromeda-01_DailyCheck":     {"project_id": 2, "project_name": "Andromeda-01"},
    "Draco-01_DCPP_DailyCheck":    {"project_id": 3, "project_name": "Draco-01"},
    # seed.py 中还有 Puma-01_DCPP_DailyCheck 的指针
    "Puma-01_DCPP_DailyCheck":     {"project_id": 1, "project_name": "Puma-01"},
}


async def migrate(dry_run: bool = False):
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    target = client["minihes"]["meter_sessions"]

    total_migrated = 0
    total_skipped = 0

    for legacy_db_name, project_info in LEGACY_DB_MAP.items():
        db = client[legacy_db_name]
        collections = await db.list_collection_names()

        for coll_name in collections:
            # 电表序列号 = 集合名（如 KFM2025030100001）
            meter_serial = coll_name

            async for doc in db[coll_name].find({}):
                # 跳过已迁移的文档（幂等性）
                existing = await target.find_one({"_id": doc["_id"]})
                if existing:
                    total_skipped += 1
                    continue

                # 构建新格式文档
                summary = doc.get("summary", {})
                new_doc = {
                    "meter_id": None,         # 需要从 PG 查（按 serial_number 匹配）
                    "meter_serial": meter_serial,
                    "project_id": project_info["project_id"],
                    "project_name": project_info["project_name"],
                    "task_id": None,
                    "collected_at": doc.get("timestamp"),  # ISO 字符串 → 需转 date
                    "imported_at": doc.get("timestamp"),
                    "source": "import",
                    "source_file": doc.get("source_file", ""),
                    "connection_type": "",
                    "status": "success" if summary.get("total_failed", 0) == 0 else "partial",
                    "total_points": summary.get("total_read", 0),
                    "success_points": summary.get("total_success", 0),
                    "failed_points": summary.get("total_failed", 0),
                    "sheets": doc.get("sheets", {}),
                    "key_value_pairs": doc.get("key_value_pairs", {}),
                    "summary": summary,
                    "schema_version": 1,
                    "_legacy_db": legacy_db_name,     # 审计追溯
                    "_legacy_collection": coll_name,
                }

                if not dry_run:
                    await target.insert_one(new_doc)
                total_migrated += 1

    logger.info(
        f"迁移完成: {total_migrated} 文档已迁移, {total_skipped} 文档跳过（已存在）, "
        f"dry_run={dry_run}"
    )


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    logging.basicConfig(level=logging.INFO)
    asyncio.run(migrate(dry_run=dry))
```

### 迁移步骤

1. **先执行 PG seed**（确保 `dev_meter` 有对应序列号记录）
2. **干跑迁移脚本**（`--dry-run`），确认文档数量和匹配结果
3. **正式迁移**（不加 `--dry-run`）
4. **回填 `meter_id`**：通过 `meter_serial` 关联 PG `dev_meter.serial_number`，更新 Mongo 文档
5. **更新 PG `col_session.mongo_*`**：将旧指针改为新值（`mongo_db="minihes"`, `mongo_collection="meter_sessions"`）
6. **验证**：随机抽查 3 个文档，通过 `MongoSessionRepo.get_by_doc_id()` 确认可查

### 兼容策略

迁移完成后，`generate_testdata_mongo.py` 也需更新，改为直接写入 `minihes.meter_sessions`
（而不是按项目名分库）。新代码：

```python
# generate_testdata_mongo.py 修改后
result = subprocess.run(
    ["mongoimport", "--db", "minihes", "--collection", "meter_sessions",
     "--file", tmp_file, "--quiet"],
    capture_output=True, text=True
)
```

---

## 八、PG 与 MongoDB 职责划分

| 数据类型 | 存储 | 集合/表 | 理由 |
|---------|------|---------|------|
| 用户/角色/权限/部门 | **PG** | `sys_*` | 关系型，强一致性，ACID |
| 设备元数据 | **PG** | `dev_meter` / `dev_meter_comm` | 结构化，频繁 CRUD |
| 采集任务配置 | **PG** | `col_task` | 结构化 + JSONB |
| OBIS 模板 | **PG** | `obis_template` / `data_point_template` | 结构化 + JSONB |
| 点值读数 | **PG** | `col_meter_reading` | 已建好时序表，索引查询高效 |
| 日/月汇总 | **PG** | `col_reading_daily` | 聚合查询高效 |
| 数据质量统计 | **PG** | `col_data_quality` | 小数据量结构化 |
| 告警规则与记录 | **PG** | `sys_alarm_rule` / `sys_alarm_record` | 结构化，关联用户/电表 |
| 审计日志 | **PG** | `sys_audit_log` | JSON diff，事务一致性 |
| 测试任务/报告 | **PG** | `lab_*` | 结构化，流程管理 |
| **DLMS 原始采集文档** | **MongoDB** | `meter_sessions` | ~1.2MB 大文档，24 sheets 灵活结构 |
| **Profile buffers** | **MongoDB** | `meter_sessions.sheets` | 嵌入数组，一次读取完整曲线 |
| **720 KV pairs** | **MongoDB** | `meter_sessions.key_value_pairs` | 扁平 key-value，点路径查询 |
| **采集会话桥梁** | **PG** | `col_session` | `mongo_doc_id` → MongoDB 文档 |

**核心原则**：PG 是"索引 + 结构化"层，MongoDB 是"大文档原文"层。PG 通过 `col_session` 知道
"哪些采集会话存在、在哪找"，Mongo 存"采集到了什么具体内容"。

---

## 九、实施路线图

### Phase 1: 基础设施（1-2 天）

| 任务 | 文件 | 说明 |
|------|------|------|
| MongoDB 配置 | `config.py` | 新增 `MONGODB_URL` / `MONGODB_DATABASE` |
| Motor 客户端 | `app/core/mongo.py`（新建） | 单例 + `get_mongo()` 依赖 |
| 生命周期管理 | `main.py` | lifespan 注册 `close_mongo()` |
| 环境变量 | `.env.example` | 补充 Mongo 配置示例 |
| Docker 服务 | `docker-compose.yml` | 补充 MongoDB 27017 服务 |

### Phase 2: Schema 与写入路径（2 天）

| 任务 | 文件 | 说明 |
|------|------|------|
| 集合创建脚本 | `scripts/init_mongo.py`（新建） | 创建集合 + validator + 索引 |
| 数据访问层 | `app/services/mongo_session_repo.py`（新建） | CRUD + 分析查询 + buffer 解析 |
| 写入路径 | `app/services/collector/session_writer.py`（新建） | `save_collection_session()` |
| Seed 适配 | `app/db/seed.py` | 检测 Mongo 可用性，可选写入真实文档 |

### Phase 3: 分析 Service 层（2-3 天）

> **注意**：新文件命名为 `analysis_mongo_service.py`，**不是** `analysis_service.py`
>（后者已存在，含 10 个运维报表函数，不可覆盖）。

| 任务 | 文件 | 说明 |
|------|------|------|
| 分析服务 | `app/services/analysis_mongo_service.py`（新建） | PG + Mongo 联合查询，仅服务前 9 个 stub 路由 |
| 日线解析 | — | `_parse_daily_billing_buffer()` |
| 负荷曲线解析 | — | `_parse_load_profile_buffer()` |
| 瞬时量解析 | — | `_parse_instantaneous()` |
| 累计电能 | — | `get_energy()` |

### Phase 4: 分析 API 端点改造（2 天）

> **⚠️ 只改前 9 个 stub 路由，后 10 个运维报表不动。**

| 路由 | 数据来源 | 降级策略 |
|------|---------|---------|
| `/daily` | Mongo: Daily Billing + Load Profile | 返回空结构 + warning |
| `/daily/export` | 同上 + CSV | 返回空 CSV |
| `/compare` | Mongo: 多表 Energy/Instantaneous | 返回空列表 |
| `/consistency` | PG + Mongo 联合 | 返回 PG 已有数据 |
| `/consistency/check` | PG + Mongo | 返回缓存结果 |
| `/data-quality` | PG `col_data_quality` | 无需降级（纯 PG） |
| `/data-quality/export` | 同上 + CSV | 返回空 CSV |
| `/reports` | PG `lab_test_report` | 无需降级（纯 PG） |
| `/reports/{id}/export` | PG | 返回占位 |

> **后 10 个运维报表路由（`comm-success-rate` 等）不在改造范围。**

### Phase 5: 数据迁移与测试（2 天）

| 任务 | 文件 | 说明 |
|------|------|------|
| 旧数据迁移脚本 | `scripts/migrate_legacy_mongo.py`（新建） | 迁移 3 库 24 集合 → 单库单集合 |
| Mongo Repo 测试 | `tests/test_mongo_session_repo.py` | CRUD + 解析测试（mock Mongo） |
| 分析查询测试 | `tests/test_analysis_mongo.py` | 端到端分析查询 |
| **集成测试** | `tests/test_mongo_integration.py` | 真实 MongoDB 实例（testcontainers） |
| **降级测试** | `tests/test_analysis_fallback.py` | Mongo 断开时分析 API 返回 warning |
| **双写一致性测试** | `tests/test_session_writer.py` | PG-Mongo 写入/回滚一致性 |
| 变更日志 | `docs/CHANGELOG.md` | 记录 v0.7.0 MongoDB 集成 |
| 架构文档 | `AGENTS.md` / `CLAUDE.md` | 补充 MongoDB 架构描述 |

---

## 十、新增/修改文件清单

| 操作 | 文件 | 说明 |
|------|------|------|
| **新增** | `docs/design/mongodb-integration.md` | 本设计文档 |
| **新增** | `backend/app/core/mongo.py` | Motor 客户端 + 依赖注入 |
| **新增** | `backend/app/services/mongo_session_repo.py` | Mongo 数据访问层 |
| **新增** | `backend/app/services/collector/session_writer.py` | 采集文档写入路径（含双写一致性） |
| **新增** | `backend/app/services/analysis_mongo_service.py` | Mongo 分析逻辑（不覆盖已有 `analysis_service.py`） |
| **新增** | `scripts/init_mongo.py` | 集合 + validator + 索引初始化 |
| **新增** | `scripts/migrate_legacy_mongo.py` | 旧拓扑数据迁移 |
| **修改** | `backend/app/core/config.py` | +`MONGODB_URL` / `MONGODB_DATABASE` |
| **修改** | `backend/main.py` | lifespan 注册 `close_mongo()` |
| **修改** | `backend/app/core/dependencies.py` | +`MongoDb` Annotated 依赖 |
| **修改** | `backend/app/api/v1/endpoints/analysis.py` | **前 9 个** stub → 真实查询（后 10 个不动） |
| **修改** | `backend/app/db/seed.py` | 可选 Mongo 写入 |
| **修改** | `docs/testdata/generate_testdata_mongo.py` | 改为写入 `minihes.meter_sessions` |
| **修改** | `docker-compose.yml` | +MongoDB 服务 |
| **修改** | `AGENTS.md` / `CLAUDE.md` | 架构描述更新 |

---

## 十一、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| **MongoDB 未启动** | 分析 API 报错，全站不可用 | `get_mongo()` 懒加载；分析 API `try/except` 降级返回空 + warning |
| **文档 > 16 MB**（极端电表） | 写入失败 | `session_writer` 中 `bson.encode()` 检查 15MB 阈值；超大文档拆分 Profile buffer |
| **seed.py 依赖 Mongo** | 新开发者初始化失败 | seed.py 检测 Mongo 可用性：不可用时跳过，仅 seed PG，打印提示 |
| **分析 API 性能** | 每次加载 1.2MB 文档慢 | Mongo **projection** 只取需要的 sheet（如 `{sheets.Daily Billing: 1}`） |
| **PG-Mongo 双写不一致** | 孤儿文档 / 悬空指针 | **PG 先登记 pending → Mongo 写入 → PG 补全**（5.4 节）；GC 扫描 pending 记录 |
| **覆盖已有运维报表** | 10 个已实现路由被破坏 | `analysis_mongo_service.py` 独立文件；Phase 4 明确只改前 9 个 stub |
| **旧数据拓扑不兼容** | 现有 3 库 24 集合查不到 | `migrate_legacy_mongo.py` 一次性迁移脚本（七·补节） |
| **Schema 演进** | 旧文档字段缺失 | `schema_version` 字段 + 查询时 fallback 默认值 |

---

## 十二、环境变量

```bash
# .env 新增

# MongoDB（原始采集文档存储）
# 开发环境（无认证）
MONGODB_URL=mongodb://localhost:27017
# 生产环境（带认证）
# MONGODB_URL=mongodb://minihes:minihes@localhost:27017/?authSource=admin
MONGODB_DATABASE=minihes
```

### Docker Compose 补充

```yaml
services:
  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: minihes
      MONGO_INITDB_ROOT_PASSWORD: minihes
    command: ["--auth"]

volumes:
  mongo_data:
```

> 生产环境建议使用 MongoDB Atlas 或 Replica Set 以保证高可用。
> `.env` 中的 `MONGODB_URL` 需与 Docker Compose 的认证配置匹配（含用户名/密码）。

---

## 附录 A：DLMS 时间戳格式说明

采集文档中的时间戳使用 DLMS date-time 格式，需解析：

```
"2024-06-15 6 00:15:00 00,FF88,80"
 │         │ │       │  │  │  │
 │         │ │       │  │  │  └─ clock_status (0x80 = 普通时钟)
 │         │ │       │  │  └──── deviation (-128 ~ 127, 0xFF88 = N/A)
 │         │ │       │  └─────────── clock_status_flags
 │         │ │       └────────────── seconds
 │         │ └────────────────────── day_of_week (1-7, 0=not specified)
 │         └──────────────────────── date (YYYY-MM-DD)
```

解析函数（含异常格式处理）：

```python
import re
from datetime import datetime

def parse_dlms_timestamp(raw: str | None) -> datetime | None:
    """解析 DLMS date-time 字符串为 Python datetime。

    处理以下格式：
      - 标准：  "2024-06-15 6 00:15:00 00,FF88,80"
      - 夏令时："FFFF-03-FE 07 02:00:00 00,8000,FF"（日期未指定）
      - 无效：  None / "" / "undefined" → 返回 None
    """
    if not raw or not isinstance(raw, str) or raw in ("undefined", "N/A"):
        return None

    # 格式：YYYY-MM-DD D HH:MM:SS dev,status,clockbase
    match = re.match(
        r"(\d{4}-\d{2}-\d{2})\s+\d+\s+(\d{2}:\d{2}:\d{2})",
        raw
    )
    if match:
        try:
            return datetime.fromisoformat(f"{match.group(1)}T{match.group(2)}")
        except ValueError:
            pass

    # 夏令时等日期未指定的格式（FFFF-...）无法解析为具体日期
    return None
```

---

## 附录 B：查询示例（Mongo Shell）

```javascript
// === 查某电表最新采集文档的元数据 ===
db.meter_sessions.find(
  { meter_id: 3 },
  { meter_serial: 1, collected_at: 1, status: 1, summary: 1, _id: 0 }
).sort({ collected_at: -1 }).limit(1)

// === 查某电表最新累计电能 ===
// 注意：取整个 key_value_pairs（因 key 含点号，不能用点路径投影）
db.meter_sessions.find(
  { meter_id: 3 },
  { "key_value_pairs": 1, _id: 0 }
).sort({ collected_at: -1 }).limit(1)

// === 查某电表最近 7 天的 Daily Billing buffer ===
db.meter_sessions.find(
  { meter_id: 3 },
  { "sheets.Daily Billing": 1, collected_at: 1, _id: 0 }
).sort({ collected_at: -1 }).limit(7)

// === 查某电表最新 Load Profile 96 点曲线 ===
db.meter_sessions.find(
  { meter_id: 3 },
  { "sheets.Load Profile.objects": { $elemMatch: { attributeName: "Buffer" } }, _id: 0 }
).sort({ collected_at: -1 }).limit(1)

// === 按项目批量查最新采集列表 ===
db.meter_sessions.find(
  { project_id: 1, collected_at: { $gte: ISODate("2025-06-01"), $lte: ISODate("2025-06-30") } },
  { meter_id: 1, meter_serial: 1, collected_at: 1, status: 1, _id: 0 }
).sort({ collected_at: -1 })

// === GC：查找孤儿文档（PG 中无对应 session_id） ===
db.meter_sessions.find(
  { session_id: { $nin: [42, 43, 44, /* ... PG col_session.id 列表 */] } },
  { session_id: 1, meter_serial: 1, collected_at: 1, _id: 1 }
)
```

---

## 附录 C：需求评审修正记录（2026-07-11）

本次评审发现并修正了以下问题：

### P0 阻断问题（4 个，已修正）

| 编号 | 问题 | 修正 |
|------|------|------|
| P0-1 | `summary` 键名全部写错（`total_objects` → 应为 `total_read`；`duration_ms` 不存在） | 全文替换正确键名；`session_writer` 改为读 `total_read`；`duration_ms` 改为计算值 |
| P0-2 | 文档声称替换 `analysis.py` 全部路由，但后 10 个运维报表已实现真实查询 | 明确只改前 9 个 stub；新文件命名 `analysis_mongo_service.py`；Phase 4 表格重写 |
| P0-3 | 新单库单集合设计与现有 3 库 24 集合种子数据不兼容 | 新增七·补节数据迁移策略 + `migrate_legacy_mongo.py` 脚本 |
| P0-4 | PG-Mongo 双写无事务一致性策略 | `session_writer` 改为"PG 先登记 pending → Mongo 写入 → PG 补全"模式 |

### P1 缺陷（6 个，已修正）

| 编号 | 问题 | 修正 |
|------|------|------|
| P1-1 | PG/Mongo status 枚举未映射 | 新增 4.5 节枚举映射表 + `_map_status()` 函数 |
| P1-2 | `insert_session` 无 16MB 检查 | `session_writer` 中加 `bson.encode()` + 15MB 阈值检查 |
| P1-3 | `get_kv_value` 投影语法错误（key 含点号） | 改为取整个 `key_value_pairs` 再 Python 层取值 |
| P1-4 | Daily Billing / Load Profile 解析路径不一致 | 统一使用 `key_value_pairs` 路径 |
| P1-5 | 文档结构图示 `{"$numberInt": ...}` 误导 | 更正为 BSON 原生类型说明 |
| P1-6 | Wildcard 索引不必要且开销大 | Phase 1 不创建；添加决策说明 |

### P2 改进（5 个，已修正）

| 编号 | 问题 | 修正 |
|------|------|------|
| P2-1 | 无并发写入幂等性 | `session_id` 唯一索引 + upsert 建议 |
| P2-2 | `get_sessions_by_date_range` 硬编码 limit=100 | 参数化为 `limit: int = 200` |
| P2-3 | DLMS 时间戳解析不处理异常格式 | `parse_dlms_timestamp` 加夏令时/无效值处理 |
| P2-4 | `.env` 与 Docker Compose 认证不一致 | `.env` 示例补充带认证 URL |
| P2-5 | 测试策略缺集成测试 | Phase 5 增加集成测试 + 降级测试 + 双写一致性测试 |
