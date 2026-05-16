# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: MiniHES

**云端智能电表抄表系统** - DLMS/COSEM协议栈 + 多通信方式适配

- **前端:** vue-vben-admin 5.7.0 (Vue 3 + TypeScript + Ant Design Vue + Vite)
- **后端:** FastAPI + Python 3.12 (uv 管理)
- **数据库:** PostgreSQL + Redis + InfluxDB
- **包管理:** uv (后端), pnpm (前端)
- **部署:** Docker Compose + systemd 双支持
- **DLMS协议:** 使用私有库（替换当前简化实现）
- **API响应:** 标准 HTTP 状态码 + 业务码（详见 `docs/design/tech-review-and-architecture.md`）

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         MiniHES 云端抄表系统                        │
├─────────────────────────────────────────────────────────────────┤
│  前端 (vue-vben-admin)                                            │
│  ├── 设备管理     ├── 数据监控     ├── 报表分析     ├── 系统管理   │
├─────────────────────────────────────────────────────────────────┤
│  后端 (FastAPI)                                                  │
│  ├── API 层        ├── 服务层        ├── 数据层                   │
├─────────────────────────────────────────────────────────────────┤
│  核心模块                                                         │
│  ├── DLMS 协议栈   ├── 通信适配层     ├── 数据采集引擎             │
│  ├── 设备管理      ├── 数据处理      └── 分析统计                 │
├─────────────────────────────────────────────────────────────────┤
│  通信适配层                                                       │
│  ├── 红外  │ 4G/5G │ NB-IoT │ M-Bus │ LoRaWAN │ G3-PLC          │
├─────────────────────────────────────────────────────────────────┤
│                          ↓                                       │
│                       电表设备                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
MiniHES/
├── frontend/              # vue-vben-admin 前端 (pnpm)
│   ├── apps/
│   │   ├── web-antd/     # 主应用 (Ant Design Vue)
│   │   └── backend-mock/ # Mock API 服务
│   └── packages/          # 共享包
│
├── backend/              # FastAPI 后端 (uv)
│   ├── app/
│   │   ├── api/v1/
│   │   │   └── endpoints/
│   │   │       ├── health.py     # 健康检查
│   │   │       ├── devices.py    # 设备管理 API
│   │   │       ├── collector.py  # 数据采集 API
│   │   │       └── analysis.py   # 分析统计 API
│   │   │
│   │   ├── dlms/                 # DLMS 协议栈
│   │   │   ├── protocol/
│   │   │   │   ├── apdu.py       # APDU 编解码
│   │   │   │   └── acse.py       # ACSE 连接管理
│   │   │   └── obis.py          # OBIS 码定义
│   │   │
│   │   ├── adapters/             # 通信适配层
│   │   │   ├── base.py          # 抽象基类
│   │   │   ├── infrared.py      # 红外适配器
│   │   │   └── cellular.py      # 4G/5G/NB-IoT
│   │   │
│   │   ├── services/             # 业务服务层
│   │   ├── models/               # SQLAlchemy 数据模型
│   │   ├── schemas/              # Pydantic 模型
│   │   ├── core/                 # 配置、安全、认证
│   │   └── db/                   # 数据库会话
│   │
│   ├── pyproject.toml            # uv 项目配置
│   ├── requirements.txt          # 旧依赖文件 (已迁移到 pyproject.toml)
│   └── .venv/                    # Python 3.12 虚拟环境
│
├── tests/                        # 测试
│   ├── e2e/                      # Playwright E2E 测试
│   └── backend/                  # pytest 后端测试
│
└── docs/                         # 项目文档
```

---

## DLMS 协议栈架构

```
┌─────────────────────────────────────────────────────────────┐
│                     DLMS 应用层                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 数据采集  │  │ 负荷控制  │  │ 事件通知  │  │ 参数配置  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                   COSEM 对象模型                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Register │  │ Attribute │  │  Method  │  │ Profile  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                 ACSE / APDU 层                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  Get     │  │  Set     │  │  Action  │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
├─────────────────────────────────────────────────────────────┤
│                    通信适配层                                 │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐               │
│  │红外│ │4G/5G│ │NB-IoT│ │M-Bus│ │LoRa│ │PLC │               │
│  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## 开发指南

### 添加新的通信适配器

1. 继承 `CommunicationAdapter` 基类
2. 实现 `connect()`, `disconnect()`, `send()`, `receive()` 方法
3. 在 `adapters/__init__.py` 注册适配器

```python
# adapters/new_adapter.py
from .base import CommunicationAdapter

class NewAdapter(CommunicationAdapter):
    async def connect(self):
        # 实现连接逻辑
        pass
```

### 添加新的 DLMS 对象

1. 在 `dlms/cosem/` 定义对象类
2. 在 `dlms/obis.py` 注册 OBIS 码

### 数据采集流程

1. 创建采集任务 → `services/collector/scheduler.py`
2. 选择通信适配器 → `adapters/`
3. 构建 DLMS 请求 → `dlms/protocol/`
4. 发送并接收响应 → `adapters/`
5. 解析数据 → `services/processor/parser.py`
6. 存储数据 → `models/`
7. 触发通知 → `services/device/`

---

## 常用 OBIS 码

| OBIS 码 | 描述 | 单位 |
|---------|------|------|
| 1.0.0.0.0.255 | 总正向有功电能 | kWh |
| 1.0.1.8.0.255 | 当前需量 | W |
| 1.0.12.7.0.255 | 相位A电压 | V |
| 1.0.21.7.0.255 | 相位A电流 | A |
| 0.0.1.0.0.255 | 电表状态 | - |

---

## 环境要求

- Python >= 3.11 (通过 uv 管理，当前使用 3.12)
- Node.js >= 18
- uv (Python 包管理器)
- pnpm (前端包管理器)

## 环境变量

```bash
# 后端
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379
DLMS_DEFAULT_TIMEOUT=30
COLLECTOR_MAX_WORKERS=10
```

## 后端依赖

管理命令：
```bash
cd backend
uv add <package>          # 添加运行时依赖
uv add --dev <package>    # 添加开发依赖
uv sync                   # 同步安装所有依赖
uv run <command>          # 在虚拟环境中执行命令
```

运行时依赖：fastapi, uvicorn, pydantic, pydantic-settings, sqlalchemy, alembic, asyncpg, aiomysql, motor, redis, pyserial-asyncio, apscheduler, pandas, numpy, pyarrow, python-dotenv, python-multipart, passlib, python-jose, structlog

开发依赖：pytest, pytest-asyncio, pytest-cov, httpx, ruff, black

## 文档规范

**所有项目文档必须放在 `docs/` 目录下**，按阶段产物和功能模块组织：

```
docs/
├── planning/              # 项目规划
│   ├── development-plan.md        # 开发排期计划
│   ├── project-workflow.md        # 项目开发流程
│   └── phase-overview.md          # 阶段概览
│
├── tasks/                 # 需求文档
│   └── prd-cloud-metering-system.md
│
├── design/                # 设计文档
│   └── tech-review-and-architecture.md
│
├── api/                   # API 文档（按模块）
│   ├── auth.md
│   ├── meters.md
│   ├── tasks.md
│   ├── analysis.md
│   ├── alarms.md
│   └── ...
│
├── guides/                # 开发指南
│   └── testing-strategy.md
│
└── reports/               # 审查报告、复盘
    └── ...
```

**规则**：
- 禁止在项目根目录放文档文件（README.md 除外）
- 禁止在 `docs/` 根目录直接放文件，必须进子目录
- 文件名使用 kebab-case
- 新建文档必须归入对应子目录

## 启动服务

```bash
# 后端
cd backend && uv run uvicorn main:app --reload

# 前端 (vue-vben-admin)
cd frontend && pnpm dev:antd
```
