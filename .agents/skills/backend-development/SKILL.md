---
name: backend-development
description: |
  MiniHES 后端开发规范。当用户进行 FastAPI 后端开发、API 设计、数据库操作、
  DLMS 协议实现、数据采集任务开发时自动激活。
  涵盖分层架构、编码原则、安全要求、数据库规范。
---

# MiniHES 后端开发规范

## 何时使用

- 编写 FastAPI endpoint、service、model、schema
- 数据库迁移、种子数据
- DLMS 协议栈开发
- 数据采集任务调度
- 后端代码审查或重构

## 技术栈

- **框架**: FastAPI + uvicorn
- **语言**: Python 3.12 (uv 管理)
- **ORM**: SQLAlchemy 2.0 async (asyncpg)
- **数据库**: PostgreSQL + Redis + InfluxDB
- **迁移**: Alembic
- **任务调度**: APScheduler
- **验证**: Pydantic v2

## 分层架构

严格遵循单向依赖，禁止跨层调用：

```
api/v1/endpoints/   → 路由层（HTTP 处理）
       ↓
schemas/             → 数据验证层（Pydantic）
       ↓
services/            → 业务逻辑层
       ↓
models/              → 数据访问层（SQLAlchemy ORM）
       ↓
core/                → 基础设施（config, database, security）
```

### 各层职责

| 层 | 职责 | 禁止 |
|---|------|------|
| endpoints | 参数接收、调用 service、返回响应 | 直接操作 ORM、写业务逻辑 |
| schemas | 请求/响应模型、数据验证 | 访问数据库 |
| services | 业务逻辑、事务管理、跨模型协调 | 直接处理 HTTP 请求 |
| models | ORM 定义、表结构 | 包含业务逻辑 |
| core | 配置、数据库连接、安全工具 | 依赖业务层 |

## 编码原则

### 先设计后编码

1. 先确认需求和接口设计
2. 定义 schema（请求/响应模型）
3. 实现 service 层业务逻辑
4. 实现 endpoint 路由
5. 编写测试

**禁止**：未确认方案就直接改数据库或写代码。

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 表名 | `{模块前缀}_{名称}` | `dev_meter`, `col_task` |
| 模型类 | PascalCase | `MeterComm`, `TaskLog` |
| 字段名 | snake_case | `meter_id`, `created_at` |
| API 路径 | kebab-case 复数 | `/api/v1/meter-points` |
| Service 方法 | 动词_名词 | `get_meter`, `create_task` |
| Schema 类 | `{动作}{资源}{Request/Response}` | `CreateMeterRequest` |

### 表前缀约定

| 前缀 | 模块 | 示例 |
|------|------|------|
| `sys_` | 系统管理 | `sys_user`, `sys_role`, `sys_audit_log` |
| `dev_` | 设备管理 | `dev_meter`, `dev_meter_comm` |
| `col_` | 数据采集 | `col_task`, `col_meter_reading` |
| `lab_` | 实验室测试 | `lab_test_task`, `lab_defect` |

## 响应格式

### 成功响应

直接返回数据，使用标准 HTTP 状态码：

```python
# 200 OK - 查询
@router.get("/meters")
async def list_meters(...):
    return {"items": [...], "total": 100}

# 201 Created - 创建
@router.post("/meters", status_code=201)
async def create_meter(...):
    return meter
```

### 错误响应

HTTP 状态码 + 业务码：

```python
{
    "detail": "错误描述",
    "error_code": 10001
}
```

### 业务错误码

| 范围 | 模块 | 示例 |
|------|------|------|
| 10001-10999 | 设备管理 | 10001=设备不存在 |
| 20001-20999 | 数据采集 | 20001=任务执行失败 |
| 30001-30999 | 系统管理 | 30001=认证失败 |

## 数据库规范

### ORM 模型

```python
from app.core.database import Base, TimestampMixin

class Meter(Base, TimestampMixin):
    __tablename__ = "dev_meter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    serial_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    # ... 其他字段

    # relationship 使用字符串引用避免循环导入
    comm: Mapped["MeterComm | None"] = relationship(back_populates="meter", uselist=False)
```

### 关键规则

- 所有模型继承 `Base`，需要时间戳的加 `TimestampMixin`
- `Mapped` 类型注解，必须指定 `nullable`
- JSON 字段用 `Mapped[dict]` + `mapped_column(JSON, ...)`
- ForeignKey 必须显式声明，有 `ondelete` 约束
- 新模型必须在 `app/models/__init__.py` 注册

### 迁移流程

```bash
# 1. 生成迁移（先确认模型变更正确）
uv run alembic revision --autogenerate -m "描述"

# 2. 检查迁移文件（特别是 nullable、default、现有数据）

# 3. 应用迁移
uv run alembic upgrade head
```

**迁移注意**：
- 有现有数据的表添加 NOT NULL 列时，需先填充默认值或先加 nullable 列再改
- 删除列前确认无代码引用
- 不可回滚的迁移需确认

## 安全要求

### 必须

- 所有用户输入通过 Pydantic schema 验证
- 使用参数化查询（SQLAlchemy ORM 自动处理）
- JWT token 认证保护需要登录的接口
- 密码使用 bcrypt/pbkdf2 哈希存储
- API 路径中不暴露内部 ID 结构

### 禁止

- 拼接 SQL 字符串
- 硬编码密钥或密码
- 返回完整异常堆栈给前端
- 未验证的外部输入直接传入数据库查询

## 输出格式

构建后端功能时，按以下格式输出：

1. **文件结构** — 展示代码应放在哪里
2. **完整代码** — 功能完整、有类型注解的代码
3. **依赖** — 需要安装的包（`uv add xxx`）
4. **数据库迁移** — 如有模型变更，提供 alembic 命令
5. **环境变量** — 如有需要，提供 `.env` 配置
6. **运行说明** — 如何启动和验证

### 完整功能示例

**Schema 层**:
```python
# schemas/meter.py
from pydantic import BaseModel, Field

class CreateMeterRequest(BaseModel):
    serial_number: str = Field(..., max_length=50)
    meter_name: str = Field(..., max_length=100)
    meter_type_id: int | None = None

class MeterDetail(BaseModel):
    id: int
    serial_number: str
    meter_name: str
    current_status: str

    model_config = {"from_attributes": True}
```

**Service 层**:
```python
# services/meter_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Meter
from app.schemas.meter import CreateMeterRequest

async def create_meter(db: AsyncSession, data: CreateMeterRequest) -> Meter:
    meter = Meter(**data.model_dump())
    db.add(meter)
    await db.flush()
    return meter
```

**Endpoint 层**:
```python
# api/v1/endpoints/meters.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user
from app.schemas.meter import CreateMeterRequest, MeterDetail
from app.services.meter_service import create_meter

router = APIRouter(prefix="/meters", tags=["meters"])

@router.post("", response_model=MeterDetail, status_code=201)
async def create(
    data: CreateMeterRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await create_meter(db, data)
```

**依赖安装**:
```bash
uv add <package>         # 如果需要新包
uv run alembic revision --autogenerate -m "add xxx"
uv run alembic upgrade head
```

## 文件结构参考

```
app/
├── api/v1/endpoints/    # 每个业务一个文件
│   ├── auth.py
│   ├── meters.py
│   ├── tasks.py
│   └── ...
├── schemas/             # 对应 endpoint 的请求/响应模型
│   ├── auth.py
│   ├── meter.py
│   └── ...
├── services/            # 业务逻辑，按模块组织
│   ├── meter_service.py
│   ├── task_service.py
│   └── ...
├── models/              # ORM 模型
├── core/                # 基础设施
│   ├── config.py        # Settings
│   ├── database.py      # engine, session, Base
│   ├── security.py      # JWT, password
│   ├── dependencies.py  # get_db, get_current_user
│   └── exceptions.py    # 自定义异常
└── main.py
```
