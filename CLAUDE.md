# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: MiniHES

**云端智能电表抄表系统** - DLMS/COSEM协议栈 + 多通信方式适配

- **前端:** vue-vben-admin 5.7.0 (Vue 3 + TypeScript + Ant Design Vue + Vite)
- **后端:** FastAPI + Python
- **数据库:** PostgreSQL + Redis + InfluxDB

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         MiniHES 云端抄表系统                        │
├─────────────────────────────────────────────────────────────────┤
│  前端 (Nuxt 3)                                                   │
│  ├── 设备管理     ├── 数据监控     ├── 报表分析                   │
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
├── frontend/              # Nuxt 3 前端
│   ├── pages/
│   │   ├── devices/       # 设备管理页面
│   │   ├── monitor/       # 数据监控页面
│   │   └── analysis/      # 分析报表页面
│   └── components/
│
└── backend/              # FastAPI 后端
    ├── app/
    │   ├── api/v1/
    │   │   ├── endpoints/
    │   │   │   ├── devices.py      # 设备管理 API
    │   │   │   ├── collector.py    # 数据采集 API
    │   │   │   └── analysis.py     # 分析统计 API
    │   │   └── api.py
    │   │
    │   ├── dlms/                   # DLMS 协议栈
    │   │   ├── protocol/
    │   │   │   ├── apdu.py         # APDU 编解码
    │   │   │   ├── acse.py         # ACSE 连接管理
    │   │   │   └── cosem.py        # COSEM 接口
    │   │   ├── obis.py            # OBIS 码定义
    │   │   └── detector.py         # 自动检测
    │   │
    │   ├── adapters/               # 通信适配层
    │   │   ├── base.py            # 抽象基类
    │   │   ├── infrared.py        # 红外适配器
    │   │   ├── cellular.py        # 4G/5G/NB-IoT
    │   │   ├── mbus.py            # M-Bus
    │   │   ├── lora.py            # LoRaWAN
    │   │   └── plc.py             # G3-PLC
    │   │
    │   ├── services/
    │   │   ├── collector/         # 数据采集服务
    │   │   │   ├── scheduler.py   # 定时任务
    │   │   │   └── executor.py    # 执行引擎
    │   │   ├── device/            # 设备管理服务
    │   │   │   ├── manager.py     # 设备管理器
    │   │   │   └── registry.py    # 设备注册
    │   │   ├── processor/         # 数据处理服务
    │   │   │   └── parser.py      # 数据解析
    │   │   └── analyzer/          # 分析统计服务
    │   │
    │   ├── models/                # 数据模型
    │   │   ├── device.py          # 设备模型
    │   │   ├── meter.py           # 电表模型
    │   │   └── reading.py         # 抄读数据模型
    │   │
    │   ├── schemas/               # Pydantic 模型
    │   ├── core/                  # 配置、安全
    │   └── db/                    # 数据库会话
    │
    └── tests/
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

## 环境变量

```bash
# 后端
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379
DLMS_DEFAULT_TIMEOUT=30
COLLECTOR_MAX_WORKERS=10
```

## 启动服务

```bash
# 后端
cd backend && uvicorn main:app --reload

# 前端 (vue-vben-admin)
cd frontend && pnpm dev:antd
```
