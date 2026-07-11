# MiniHES - 云端智能电表抄表系统

> CloudMeters - 云端多表抄表与实验室测试管理平台

面向公用事业（水、电、气、热）的实验室测试管理平台，支持样机管理、数据采集、数据分析、大屏监控、测试报告等全流程管理。

## 技术栈

> 前端架构详见 [`docs/design/frontend-architecture.md`](docs/design/frontend-architecture.md)，后端架构详见 [`docs/design/tech-review-and-architecture.md`](docs/design/tech-review-and-architecture.md)。

| 层级 | 技术 |
|------|------|
| 前端 | vue-vben-admin 5.7.0 (Vue 3 + TypeScript + Ant Design Vue + Vite) |
| 图表 | ECharts + useChartTheme 主题适配 |
| 后端 | Python FastAPI + SQLAlchemy 2.0 (async) |
| 数据库 | PostgreSQL (业务数据 + 时序数据，使用 `col_meter_reading`/`col_reading_daily_summary` 时序表) |
| 缓存 | Redis |
| 包管理 | uv (后端) + pnpm (前端) |
| CI/CD | GitHub Actions (ruff lint + pytest + vue-tsc typecheck) |

> **存储决策说明**：早期选型曾考虑 InfluxDB 作为时序数据库，经评估后**已弃用**，时序抄读数据统一存入 PostgreSQL 时序表，简化部署与运维。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                       MiniHES 云端抄表系统                        │
├─────────────────────────────────────────────────────────────────┤
│  前端 (vue-vben-admin)                                          │
│  ├── 设备管理     ├── 数据分析     ├── 大屏展示                    │
│  ├── 采集任务     ├── 测试管理     ├── 告警管理                    │
├─────────────────────────────────────────────────────────────────┤
│  后端 (FastAPI)                                                  │
│  ├── API 层 (endpoints)   ├── 服务层 (services)   ├── 数据层      │
│  ├── Schemas 验证         ├── 依赖注入 (DI)       ├── 审计日志     │
├─────────────────────────────────────────────────────────────────┤
│  核心模块                                                        │
│  ├── DLMS 协议栈   ├── 通信适配层    ├── 数据采集引擎              │
│  ├── 设备管理      ├── 数据处理      └── 分析统计                  │
├─────────────────────────────────────────────────────────────────┤
│  通信适配层                                                      │
│  ├── 红外  │ 4G/5G │ NB-IoT │ M-Bus │ LoRaWAN │ G3-PLC          │
├─────────────────────────────────────────────────────────────────┤
│  数据存储                                                        │
│  ├── PostgreSQL (业务数据 + 时序数据)  ├── Redis (缓存)          │
└─────────────────────────────────────────────────────────────────┘
```

## 项目结构

```
MiniHES/
├── frontend/                  # 前端 (vue-vben-admin 5.7.0, pnpm)
│   ├── apps/
│   │   ├── web-antd/         # Ant Design Vue 主应用
│   │   │   └── src/
│   │   │       ├── api/modules/   # API 接口模块
│   │   │       ├── views/         # 页面视图 (大屏/设备/任务/分析等)
│   │   │       ├── composables/   # 组合式函数 (useChartTheme, useWebSocket)
│   │   │       └── constants/     # 主题色常量
│   │   └── backend-mock/     # Mock API 服务
│   └── packages/              # 共享包
│
├── backend/                   # 后端 (FastAPI, uv)
│   └── app/
│       ├── api/v1/endpoints/  # API 端点 (全量 Service 化)
│       ├── services/          # 业务逻辑层 (17 个 service)
│       ├── models/            # SQLAlchemy 数据模型
│       ├── schemas/           # Pydantic 请求/响应模型
│       ├── core/              # 配置、安全、DI、异常处理
│       ├── dlms/              # DLMS/COSEM 协议栈
│       ├── adapters/          # 通信适配层
│       └── db/                # 数据库会话 + seed
│
├── docs/                      # 项目文档
│   ├── tasks/                 # PRD 需求文档
│   ├── design/                # 架构设计文档（前端架构 + 后端架构 + 数据库表结构）
│   ├── planning/              # 开发排期 + 阶段概览
│   ├── guides/                # 开发指南（测试策略等）
│   ├── archive/               # 历史归档（早期 UI 原型等）
│   └── CHANGELOG.md           # 变更日志
│   # 注：API 文档见 FastAPI 启动后的 /docs Swagger UI
│
├── backend/tests/             # pytest 后端测试 (83 个，CI 实际运行)
├── tests/                     # 其他测试
│   ├── backend/               # 早期占位（仅 5 个 stub）
│   └── e2e/                   # Playwright E2E 测试 (9 个，CI 未运行)
│
└── .github/workflows/         # CI/CD (lint + test + typecheck)
```

## 业务模块

| 模块 | 功能 |
|------|------|
| 样机管理 | 全生命周期管理（入库→测试→拆表→借用→维修→报废）、批量导入、附件管理 |
| 数据采集 | 定时/循环/一次性任务、多维设备筛选、DLMS/Modbus/MQTT 协议 |
| 数据分析 | 11 项每日分析检查、今日 vs 昨日对比、异常检测、PDF 报告导出 |
| 大屏展示 | 项目概览、项目详情、单表实时监控（系统主题自适应，亮色/暗色模式） |
| 测试管理 | 测试报告生成、PDF 导出、邮件分发、缺陷跟踪 |
| 告警系统 | 告警规则配置、实时告警监控 |
| 系统管理 | RBAC 权限、按钮级权限控制、操作审计日志 |

## 快速开始

### 前置条件

- Node.js >= 18
- Python >= 3.11
- uv (Python 包管理器)
- pnpm (前端包管理器)
- PostgreSQL + Redis

### 前端

```bash
cd frontend
pnpm install
pnpm dev:antd        # http://localhost:5666
```

### 后端

```bash
cd backend
uv sync               # 安装依赖到 .venv
uv run uvicorn main:app --reload   # http://localhost:8000
```

### 环境变量

```bash
# 前端 (frontend/apps/web-antd/.env.development)
VITE_GLOB_API_URL=/api/v1
VITE_NITRO_MOCK=false       # false=对接真实后端, true=使用 mock

# 后端 (.env)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/metering_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
```

### 初始化数据库

```bash
cd backend
uv run alembic upgrade head          # 执行 migration
uv run python -m app.db.seed         # 导入种子数据
```

默认管理员账号：`admin / 123456`

## 开发规范

### 后端

- **分层架构**：Endpoint → Service → Model，全量 Service 化 + Schema 验证
- **依赖注入**：`DbSession` / `CurrentUser` 通过 FastAPI Depends 注入
- **Lint**：`ruff check app/ tests/` + `ruff format app/ tests/`
- **测试**：`uv run pytest`（83 个测试）

### 前端

- **主题**：禁止自定义背景色，所有组件使用系统主题样式
- **图表**：使用 `useChartTheme()` 的 `themedAxis`/`themedTooltip`/`themedLegend`，不硬编码颜色
- **类型检查**：`pnpm --filter @vben/web-antd run typecheck`

### 提交规范

```
feat: 新功能
fix: 修复
docs: 文档
refactor: 重构
test: 测试
chore: 构建/工具
```

## 通信协议

| 协议 | 适用设备 |
|------|----------|
| DLMS/COSEM | 智能电表 |
| Modbus | 水/气表 |
| MQTT | NB-IoT 设备 |

## License

MIT
