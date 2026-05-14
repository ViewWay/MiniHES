# MiniHES - 云端智能电表抄表系统（前端）

> CloudMeters - 云端多表抄表与实验室测试管理平台

## 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.x | 前端框架 |
| TypeScript | 5.x | 类型安全 |
| Ant Design Vue | 4.x | UI 组件库 |
| Vite | 6.x | 构建工具 |
| vue-vben-admin | 5.7.0 | 后台管理框架 |
| ECharts | 5.x | 图表可视化 |
| Pinia | 2.x | 状态管理 |
| WebSocket | - | 实时数据推送 |

## 业务模块

| 模块 | 页面 | 功能 |
|------|------|------|
| 仪表盘 | 数据概览、告警管理 | 统计概览、ECharts趋势图、告警实时监控 |
| 设备管理 | 列表、详情、借用、维修 | 样机全生命周期管理、状态流转、借用审批、批量导入 |
| 采集任务 | 列表、创建、日志、监控 | Cron/Interval/Once任务、多维设备筛选、实时进度 |
| 数据分析 | 每日分析、对比分析、报告 | 11项分析检查、ECharts图表、PDF导出 |
| 大屏展示 | 项目概览、项目详情、单表监控 | 深色主题、实时数据轮询、堆栈/EEPROM监控 |
| 测试管理 | 测试列表、测试报告、缺陷管理 | 报告PDF导出、邮件分发、缺陷状态跟踪 |
| 系统管理 | 用户、角色、日志、告警规则 | RBAC权限、按钮级权限控制、审计日志 |

## 项目结构

```
frontend/apps/web-antd/src/
├── api/modules/          # API 接口模块 (7个)
│   ├── alarm.ts          # 告警管理
│   ├── analysis.ts       # 数据分析
│   ├── meter.ts          # 设备管理
│   ├── project.ts        # 项目管理
│   ├── system.ts         # 系统管理
│   ├── task.ts           # 采集任务
│   └── test.ts           # 测试管理
├── components/           # 共享组件
│   ├── meter/            # StatusBadge, MeterCard, BorrowDialog
│   └── task/             # TaskProgress, LogTimeline
├── composables/          # 组合式函数
│   └── useWebSocket.ts   # WebSocket 实时推送
├── router/routes/modules/ # 路由模块 (7个)
├── store/                # Pinia 状态管理
│   ├── alarm.ts          # 告警 Store
│   ├── meter.ts          # 设备 Store
│   └── task.ts           # 任务 Store
└── views/                # 页面视图 (23个)
    ├── analysis/         # 数据分析
    ├── dashboard/        # 仪表盘
    ├── meter/            # 设备管理
    ├── screen/           # 大屏展示
    ├── system/           # 系统管理
    ├── task/             # 采集任务
    └── test/             # 测试管理
```

## 快速开始

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev:antd

# 构建生产版本
pnpm build:antd
```

## 环境配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VITE_GLOB_API_URL` | 后端 API 地址 | `http://localhost:8000/api/v1` |
| `VITE_APP_TITLE` | 应用标题 | MiniHES 云端智能电表抄表系统 |
| `VITE_PORT` | 开发端口 | 5666 |

## 通信协议支持

- **DLMS/COSEM** — 智能电表标准协议
- **Modbus** — 通用工业协议（水/气表）
- **MQTT** — NB-IoT 物联网协议

## License

MIT
