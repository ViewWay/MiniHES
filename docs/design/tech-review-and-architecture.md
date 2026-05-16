# MiniHES 技术审查与架构设计

**审查日期**: 2026-05-16
**审查范围**: 全栈技术选型、项目结构、后端架构、开发流程

---

## 一、技术审查结论

### 1.1 当前状态

| 层 | 状态 | 评价 |
|----|------|------|
| 前端 | ✅ 基本完成 | 99个源文件，页面完整覆盖PRD |
| Mock API | ✅ 完成 | 72个API文件，前后端已联调 |
| 后端 | ⚠️ 骨架阶段 | 仅health端点，缺models/services/schemas |
| 数据库 | ❌ 未搭建 | 无migration、无表结构 |
| DLMS协议 | ⚠️ 原型阶段 | APDU/ACSE/OBIS有雏形，但编解码是简化实现 |

### 1.2 发现的问题

**P0 - 架构层面：**
1. 后端缺少分层架构设计（无 models / schemas / services 层）
2. 无数据库连接管理（无 SQLAlchemy Session、无 Alembic migration）
3. 无统一响应格式（前端 mock 返回 `{code: 0}`，后端未定义）
4. 无统一异常处理（无全局 exception handler）

**P1 - 设计层面：**
5. `Settings` 配置过于简陋，缺 JWT/Redis/InfluxDB/数据库等配置
6. 无依赖注入体系（无 FastAPI Depends 组织）
7. DLMS 协议栈的 AARQ 编码是硬编码字节，不可维护
8. 通信适配器缺连接池管理，每次采集都新建连接开销大

**P2 - 工程规范：**
9. 后端缺 `.env.example` 文件
10. 无 pre-commit / lint 配置
11. `requirements.txt` 和 `pyproject.toml` 并存（应只保留 pyproject.toml）

---

## 二、后端架构设计

### 2.1 分层架构

```
┌───────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                        │
├───────────────────────────────────────────────────────────────────┤
│  api/v1/endpoints/   ← 路由层：参数校验、响应格式化               │
│  ├── auth.py         ├── meters.py       ├── tasks.py             │
│  ├── projects.py     ├── analysis.py     ├── alarms.py            │
│  ├── tests.py        ├── screens.py      └── system/              │
├───────────────────────────────────────────────────────────────────┤
│  schemas/            ← 数据契约：Pydantic 请求/响应模型           │
│  ├── auth.py         ├── meter.py        ├── task.py              │
│  ├── project.py      ├── analysis.py     ├── alarm.py             │
│  ├── test.py         └── common.py       (分页、统一响应)         │
├───────────────────────────────────────────────────────────────────┤
│  services/           ← 业务逻辑层：核心业务规则                    │
│  ├── auth/           ├── meter/          ├── task/                │
│  │   └── jwt.py      │   └── status.py  │   └── scheduler.py     │
│  ├── collector/      ├── analysis/       ├── alarm/               │
│  │   └── executor.py │   └── daily.py   │   └── engine.py        │
│  └── test/                                                          │
├───────────────────────────────────────────────────────────────────┤
│  models/             ← 数据访问层：SQLAlchemy ORM 模型             │
│  ├── user.py         ├── meter.py        ├── task.py              │
│  ├── project.py      ├── alarm.py        ├── test.py              │
│  └── base.py         (Base, TimestampMixin, 通用方法)             │
├───────────────────────────────────────────────────────────────────┤
│  core/               ← 基础设施层                                  │
│  ├── config.py       (Settings 完整配置)                            │
│  ├── security.py     (JWT, 密码哈希)                               │
│  ├── database.py     (SQLAlchemy 异步引擎, Session 管理)           │
│  ├── redis.py        (Redis 连接池)                                 │
│  ├── influxdb.py     (InfluxDB 客户端封装)                         │
│  ├── dependencies.py (通用 Depends: get_db, get_current_user)     │
│  └── exceptions.py   (自定义异常 + 全局处理器)                     │
├───────────────────────────────────────────────────────────────────┤
│  dlms/               ← 协议栈（保持现有，后续迭代完善）           │
│  adapters/           ← 通信适配器（保持现有，增加连接池）         │
└───────────────────────────────────────────────────────────────────┘
```

### 2.2 关键设计决策

#### 统一响应格式

**双层响应机制**：HTTP 状态码 + 业务码

- HTTP 状态码：传输层语义（200 OK, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Error）
- 业务码：应用层语义，放在响应体 `code` 字段，成功时与 HTTP 状态码一致

```python
# core/response.py
from typing import Any, Generic, TypeVar
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")

class ResponseBase(BaseModel):
    code: int = 200
    message: str = "success"

class ResponseData(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T | None = None

class PagedData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

class PagedResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: PagedData[T]

# 便捷方法
def ok(data: Any = None, message: str = "success") -> JSONResponse:
    return JSONResponse(status_code=200, content={
        "code": 200, "message": message, "data": data
    })

def created(data: Any = None, message: str = "created") -> JSONResponse:
    return JSONResponse(status_code=201, content={
        "code": 201, "message": message, "data": data
    })

def fail(code: int = 400, message: str = "bad request", status: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status, content={
        "code": code, "message": message
    })
```

**业务错误码定义**：

| 范围 | 说明 | HTTP 状态码 |
|------|------|-------------|
| 200 | 成功 | 200 |
| 201 | 创建成功 | 201 |
| 400 | 请求参数错误 | 400 |
| 401 | 未认证 | 401 |
| 403 | 无权限 | 403 |
| 404 | 资源不存在 | 404 |
| 10001 | 设备不存在 | 404 |
| 10002 | 设备状态不允许此操作 | 400 |
| 10003 | 设备已被借用 | 409 |
| 10004 | 采集任务正在执行 | 409 |
| 10005 | 采集任务不存在 | 404 |
| 10006 | 审批流程未完成 | 400 |
| 10007 | 项目不存在 | 404 |
| 10008 | 序列号已存在 | 409 |
| 20001 | 通信超时 | 504 |
| 20002 | 协议解析失败 | 500 |
| 20003 | 设备离线 | 503 |
| 30001 | 用户名或密码错误 | 401 |
| 30002 | Token 已过期 | 401 |
| 30003 | 权限不足 | 403 |

**响应示例**：

成功（200）：
```json
HTTP/1.1 200 OK
{
  "code": 200,
  "message": "success",
  "data": { "id": 123, "serial_number": "DLMS2024001" }
}
```

创建成功（201）：
```json
HTTP/1.1 201 Created
{
  "code": 201,
  "message": "created",
  "data": { "id": 123 }
}
```

业务错误（设备状态不允许）：
```json
HTTP/1.1 400 Bad Request
{
  "code": 10002,
  "message": "设备状态不允许此操作",
  "data": null
}
```

认证失败（401）：
```json
HTTP/1.1 401 Unauthorized
{
  "code": 401,
  "message": "Token 已过期"
}
```

校验失败（400）：
```json
HTTP/1.1 400 Bad Request
{
  "code": 400,
  "message": "参数校验失败",
  "errors": [
    { "field": "serial_number", "message": "此字段为必填项" }
  ]
}
```

> 前端 mock 中 `code: 0` 为临时调整，联调时对齐为标准 HTTP + 业务码。

#### 数据库连接管理

```python
# core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

#### 依赖注入体系

```python
# core/dependencies.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from app.core.database import get_db
from app.core.security import decode_token

security = HTTPBearer()

async def get_current_user(token=Depends(security), db=Depends(get_db)):
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(401, "Invalid token")
    user = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(401, "User not found")
    return user

def require_permissions(*permissions: str):
    async def checker(user=Depends(get_current_user)):
        # 检查用户角色是否有所需权限
        ...
        return user
    return checker
```

#### 全局异常处理

```python
# core/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

class BusinessException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(status_code=200, content={
        "code": exc.code,
        "message": exc.message,
    })

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=200, content={
        "code": 400,
        "message": "参数校验失败",
        "errors": [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()],
    })
```

#### 配置完善

```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 应用
    PROJECT_NAME: str = "MiniHES"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/metering_db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # InfluxDB
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = ""
    INFLUXDB_ORG: str = "metering"
    INFLUXDB_BUCKET: str = "metering"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 采集
    COLLECTOR_MAX_WORKERS: int = 10
    COLLECTOR_DEFAULT_TIMEOUT: int = 30
    COLLECTOR_RETRY_TIMES: int = 3

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2.3 目标目录结构

```
backend/
├── main.py                     # FastAPI 应用入口
├── alembic.ini                 # Alembic 配置
├── migrations/                 # 数据库迁移目录
│   └── versions/
├── .env.example                # 环境变量模板
├── pyproject.toml              # uv 项目配置
│
└── app/
    ├── __init__.py
    │
    ├── api/v1/
    │   ├── api.py              # 路由注册汇总
    │   └── endpoints/
    │       ├── auth.py         # 登录/登出/刷新
    │       ├── health.py       # 健康检查
    │       ├── projects.py     # 项目管理
    │       ├── meters.py       # 样机管理 + 借用 + 维修
    │       ├── tasks.py        # 采集任务
    │       ├── analysis.py     # 数据分析
    │       ├── alarms.py       # 告警管理
    │       ├── tests.py        # 测试任务 + 报告 + 缺陷
    │       ├── screens.py      # 大屏数据
    │       ├── system.py       # 用户/角色/部门/菜单
    │       └── upload.py       # 文件上传
    │
    ├── schemas/                # Pydantic 请求/响应模型
    │   ├── __init__.py
    │   ├── common.py           # 统一响应、分页
    │   ├── auth.py
    │   ├── meter.py
    │   ├── task.py
    │   ├── analysis.py
    │   ├── alarm.py
    │   ├── test.py
    │   ├── system.py
    │   └── screen.py
    │
    ├── services/               # 业务逻辑
    │   ├── __init__.py
    │   ├── auth.py             # JWT + 密码验证
    │   ├── meter.py            # 样机CRUD + 状态流转
    │   ├── borrow.py           # 借用审批
    │   ├── task.py             # 任务CRUD
    │   ├── scheduler.py        # APScheduler 调度
    │   ├── collector.py        # 采集执行引擎
    │   ├── analysis.py         # 分析计算
    │   ├── alarm.py            # 告警引擎
    │   ├── report.py           # 报告生成
    │   └── system.py           # 系统管理
    │
    ├── models/                 # SQLAlchemy ORM
    │   ├── __init__.py
    │   ├── base.py             # DeclarativeBase, TimestampMixin
    │   ├── user.py             # User, Role, Permission, Department
    │   ├── meter.py            # Meter, MeterComm, MeterSnapshot, Borrow, Repair
    │   ├── project.py          # Project, MeterType, WireType, MeterPoint
    │   ├── task.py             # Task, TaskLog, TaskDevice
    │   ├── alarm.py            # AlarmRule, AlarmRecord
    │   ├── test.py             # TestTask, TestReport, Defect
    │   └── system.py           # AuditLog, DataArchive
    │
    ├── core/
    │   ├── __init__.py
    │   ├── config.py           # Settings
    │   ├── database.py         # 异步引擎 + Session
    │   ├── redis.py            # Redis 连接
    │   ├── influxdb.py         # InfluxDB 客户端
    │   ├── security.py         # JWT 编解码 + 密码哈希
    │   ├── dependencies.py     # get_db, get_current_user
    │   ├── exceptions.py       # 自定义异常 + 全局处理器
    │   └── response.py         # 统一响应封装
    │
    ├── dlms/                   # DLMS 协议栈（保持现有结构）
    │   ├── protocol/
    │   │   ├── apdu.py
    │   │   └── acse.py
    │   ├── cosem/
    │   └── obis.py
    │
    └── adapters/               # 通信适配器（保持现有 + 连接池）
        ├── base.py
        ├── infrared.py
        └── cellular.py
```

---

## 三、开发流程

### 3.1 Schema-Driven 开发

FastAPI 自带 `/docs` (Swagger UI) + `/redoc`，代码即文档，不需要 Apifox。

```bash
# 需要离线分享时导出 OpenAPI JSON
curl http://localhost:8000/api/v1/openapi.json > docs/openapi.json
```

### 3.2 每个 Phase 的开发步骤

```
1. models/       → 定义 SQLAlchemy ORM 模型
2. alembic       → 生成并执行数据库迁移
3. schemas/      → 定义 Pydantic 请求/响应模型（接口契约）
4. services/     → 实现业务逻辑
5. endpoints/    → 注册路由，注入依赖
6. /docs         → Swagger UI 验证接口
7. tests/        → pytest 编写测试
```

### 3.3 Phase 推进计划

#### Phase 1: 基础框架 + 认证系统（2周）

```
Day 1-2:  基础设施
  ├── core/config.py       → 完善所有配置项
  ├── core/database.py     → SQLAlchemy 异步引擎
  ├── core/redis.py        → Redis 连接池
  ├── core/response.py     → 统一响应格式
  ├── core/exceptions.py   → 全局异常处理
  ├── .env.example         → 环境变量模板
  └── alembic init         → 初始化迁移

Day 3-4:  用户认证
  ├── models/user.py       → User, Role, Permission, Department
  ├── alembic migration    → 建表
  ├── schemas/auth.py      → 登录/注册/Token 模型
  ├── core/security.py     → JWT + passlib
  ├── core/dependencies.py → get_db, get_current_user
  ├── services/auth.py     → 认证逻辑
  └── endpoints/auth.py    → login/logout/refresh

Day 5-7:  系统管理
  ├── schemas/system.py    → 用户/角色/部门 模型
  ├── services/system.py   → CRUD 逻辑
  ├── endpoints/system.py  → 用户/角色/部门/菜单/审计 API
  └── tests/               → 认证和系统管理测试

Day 8-10: 项目管理 + 基础数据
  ├── models/project.py    → Project, MeterType, WireType, MeterPoint
  ├── schemas/project.py
  ├── services/project.py
  └── endpoints/projects.py

交付物：可运行的认证系统 + 用户管理 + 项目管理
```

#### Phase 2: 样机管理（3周）

```
Week 1: 样机 CRUD + 状态流转
  ├── models/meter.py       → Meter, MeterComm, MeterSnapshot, MeterStatus
  ├── schemas/meter.py
  ├── services/meter.py     → CRUD + 状态机
  └── endpoints/meters.py

Week 2: 借用审批 + 维修
  ├── models/meter.py       → Borrow, Repair
  ├── services/borrow.py    → 审批流程
  └── endpoints/meters.py   → 借用/维修 API

Week 3: 附件上传 + 对接前端
  ├── endpoints/upload.py   → 文件上传
  ├── 前后端联调
  └── tests/

交付物：完整的样机管理系统
```

#### Phase 3: 采集任务系统（4周）

```
Week 1: 任务 CRUD
  ├── models/task.py
  ├── schemas/task.py
  ├── services/task.py
  └── endpoints/tasks.py

Week 2: APScheduler 调度引擎
  ├── services/scheduler.py → 任务调度（JobStore=PostgreSQL）
  ├── services/collector.py → 采集执行引擎
  └── core/influxdb.py      → InfluxDB 写入封装

Week 3: DLMS 协议对接
  ├── 接入私有 DLMS 库
  ├── adapters/ 连接池管理
  └── 采集流程打通

Week 4: 监控 + 日志 + 联调
  ├── endpoints/tasks.py    → 日志/监控 API
  ├── WebSocket 实时推送
  └── tests/

交付物：可运行的采集任务系统
```

#### Phase 4: 数据分析 + 告警（3周）

```
Week 1: 数据分析
  ├── services/analysis.py  → 每日分析、对比、一致性检查
  └── endpoints/analysis.py

Week 2: 告警引擎
  ├── models/alarm.py
  ├── services/alarm.py     → 规则引擎
  └── endpoints/alarms.py

Week 3: 大屏 API + 联调
  ├── endpoints/screens.py  → 三种大屏数据
  └── tests/

交付物：分析 + 告警 + 大屏
```

#### Phase 5: 测试报告 + 缺陷管理（2周）

```
Week 1: 测试任务 + 报告
  ├── models/test.py
  ├── schemas/test.py
  ├── services/report.py    → 报告生成
  └── endpoints/tests.py

Week 2: 缺陷管理 + 全量联调
  ├── endpoints/defects.py
  ├── 前后端全量联调
  └── 部署文档

交付物：完整可部署系统
```

### 3.4 Git 工作流

```
main
├── develop              ← 开发主线
│   ├── feature/auth     ← Phase 1
│   ├── feature/meter    ← Phase 2
│   ├── feature/task     ← Phase 3
│   ├── feature/analysis ← Phase 4
│   └── feature/test     ← Phase 5
```

- 每个 Phase 一个 feature 分支，完成后 PR 合并到 develop
- develop 稳定后合并到 main

### 3.5 代码规范

| 工具 | 用途 | 配置 |
|------|------|------|
| ruff | lint + format | pyproject.toml |
| pytest | 单元测试 + coverage | tests/ |
| pre-commit | 提交前检查 | .pre-commit-config.yaml |

### 3.6 提交规范

```
feat: 新功能
fix: 修复
docs: 文档
refactor: 重构
test: 测试
chore: 构建/工具
```

---

## 四、已确认的决策

| 决策 | 结论 | 说明 |
|------|------|------|
| 响应格式 | 标准 HTTP 状态码 + 业务码 | HTTP 层用标准状态码，业务层用 code 字段区分具体错误 |
| motor 依赖 | 保留 | 暂不卸载，后续按需决定 |
| DLMS 协议栈 | 使用私有库 | Phase 3 时替换当前简化实现 |
| 部署方式 | Docker Compose + systemd 双支持 | 提供两种部署配置，按场景选择 |
