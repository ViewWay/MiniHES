# MiniHES - 云端智能电表抄表系统

> CloudMeters - 云端多表抄表与实验室测试管理平台

面向公用事业（水、电、气、热）的实验室测试管理平台，支持样机管理、数据采集、数据分析、大屏监控、测试报告等全流程管理。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | vue-vben-admin 5.7.0 (Vue 3 + TypeScript + Ant Design Vue + Vite) |
| 图表 | ECharts |
| 后端 | Python FastAPI |
| 数据库 | PostgreSQL + Redis + InfluxDB (时序数据) |
| 缓存 | Redis |
| 任务队列 | Celery + Redis |

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         MiniHES 云端抄表系统                        │
├─────────────────────────────────────────────────────────────────┤
│  前端 (vue-vben-admin)                                            │
│  ├── 设备管理     ├── 数据分析     ├── 大屏展示                      │
│  ├── 采集任务     ├── 测试管理     ├── 告警管理                      │
├─────────────────────────────────────────────────────────────────┤
│  后端 (FastAPI)                                                   │
│  ├── API 层        ├── 服务层        ├── 数据层                      │
├─────────────────────────────────────────────────────────────────┤
│  核心模块                                                         │
│  ├── DLMS 协议栈   ├── 通信适配层     ├── 数据采集引擎               │
│  ├── 设备管理      ├── 数据处理      └── 分析统计                    │
├─────────────────────────────────────────────────────────────────┤
│  通信适配层                                                       │
│  ├── 红外  │ 4G/5G │ NB-IoT │ M-Bus │ LoRaWAN │ G3-PLC           │
├─────────────────────────────────────────────────────────────────┤
│  数据存储                                                         │
│  ├── PostgreSQL (业务数据)  ├── InfluxDB (时序数据)  ├── Redis (缓存) │
└─────────────────────────────────────────────────────────────────┘
```

## 项目结构

```
MiniHES/
├── frontend/                  # 前端 (vue-vben-admin 5.7.0)
│   ├── apps/web-antd/         # Ant Design Vue 应用
│   │   └── src/
│   │       ├── api/modules/   # API 接口 (7个模块)
│   │       ├── views/         # 页面视图 (23个页面)
│   │       ├── components/    # 共享组件
│   │       ├── composables/   # 组合式函数 (WebSocket)
│   │       ├── store/         # Pinia 状态管理
│   │       └── router/        # 路由配置 (7个模块)
│   ├── packages/              # 共享包
│   └── pnpm-workspace.yaml
│
├── backend/                   # 后端 (FastAPI)
│   └── app/
│       ├── api/v1/endpoints/  # API 端点
│       ├── dlms/              # DLMS/COSEM 协议栈
│       ├── adapters/          # 通信适配层
│       ├── services/          # 业务逻辑
│       ├── models/            # 数据模型
│       ├── schemas/           # Pydantic 模型
│       ├── core/              # 配置、安全
│       └── db/                # 数据库会话
│
├── tasks/                     # 项目文档
│   └── prd-cloud-metering-system.md  # PRD 文档
│
└── CLAUDE.md                  # Claude Code 指引
```

## 业务模块

| 模块 | 功能 |
|------|------|
| 样机管理 | 全生命周期管理（入库→测试→拆表→借用→维修→报废）、批量导入、附件管理 |
| 数据采集 | 定时/循环/一次性任务、多维设备筛选、DLMS/Modbus/MQTT协议 |
| 数据分析 | 11项每日分析检查、今日vs昨日对比、异常检测、PDF报告导出 |
| 大屏展示 | 项目概览、项目详情、单表实时监控（深色主题） |
| 测试管理 | 测试报告生成、PDF导出、邮件分发、缺陷跟踪 |
| 告警系统 | 告警规则配置、实时告警监控、WebSocket推送 |
| 系统管理 | RBAC权限、按钮级权限控制、操作审计日志 |

## 快速开始

### 前端

```bash
cd frontend
pnpm install
pnpm dev:antd        # http://localhost:5666
```

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload   # http://localhost:8000
```

## 环境配置

```bash
# 前端 (frontend/apps/web-antd/.env.development)
VITE_GLOB_API_URL=http://localhost:8000/api/v1

# 后端
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/metering_db
REDIS_URL=redis://localhost:6379/0
INFLUXDB_URL=http://localhost:8086
```

## 通信协议

| 协议 | 适用设备 |
|------|----------|
| DLMS/COSEM | 智能电表 |
| Modbus | 水/气表 |
| MQTT | NB-IoT 设备 |

## License

MIT
