# 落地 54 个报表设计稿 — 实施计划

## 目标
将 `docs/archive/ui/` 中的报表原型落地为真实功能。用户选择：**全面铺开**（每个分组选 1-2 个高价值报表）、**真实数据+少量mock**、**扩展「数据分析」菜单**。

## 架构原则（基于现有代码规范）
- **后端**：遵循 `success(data)` 响应封装、`DbSession` 注入、service 层 `select()`+`func.count()` 分页模式、`{"items":[],"total":n}` 分页约定
- **前端**：遵循 `views/analysis/*.vue` + `api/modules/analysis.ts` + `router/routes/modules/analysis.ts` 自动注册模式；ECharts 用 `useEcharts`+`useChartTheme`；表格用 Ant Design Vue `Table` + `@change` 分页
- **响应拦截器**已自动解包 `data` 字段，组件直接拿 `res.items`/`res.total`

---

## 第一批 MVP（10 个高价值报表，数据基础已具备）

| # | 报表 | 设计稿 | 数据来源 | 新增字段 |
|---|------|--------|----------|----------|
| 1 | **R-01 通信成功率** | `comm-success-failure-rate.html` | `TaskLog`(success/failed_devices) + `TaskDevice`(status/retry) | 无 |
| 2 | **UC-8 未通信设备** | `non-comm-devices.html` | `MeterSnapshot`(online_status/last_comm_time) + `Meter` | 无 |
| 3 | **R-07 抄表完整率** | `read-completeness.html` | `DataQuality`(total/success/failed_points) | 无 |
| 4 | **R-10 重试分析** | `retry-analysis.html` | `TaskDevice`(retry_count/error_code) | 无 |
| 5 | **R-12 未确认告警** | `open-alarms.html` | `Alarm`(is_handled/severity) | 无 |
| 6 | **R-13 告警趋势** | `alarm-trend-volume.html` | `Alarm`(created_at/severity/alarm_type) | 无 |
| 7 | **R-16 设备健康** | `device-health-model.html` | `MeterSnapshot`(online_status/signal_strength/error_code) + `Meter`(model/firmware) | 无 |
| 8 | **R-18 电池/信号老化** | `battery-status-aging.html` | `MeterSnapshot`(signal_strength/stack_usage) — **降级**：原型是电池，我们用信号强度替代 | 无 |
| 9 | **R-30 间隔负荷曲线** | `interval-consumption-trend.html` | `col_meter_reading`(时序) + `col_reading_daily` | 无 |
| 10 | **R-11 按需抄表历史** | `ondemand-history.html` | `TaskLog` + `Task`(task_type='ondemand') | 无 |

---

## 后端改动（4 个文件）

### 1. 新建 `backend/app/services/analysis_service.py`（核心）
包含 10 个报表查询函数，每个返回统一结构：
```python
async def get_comm_success_rate(db: AsyncSession, *, date_from, date_to, page=1, page_size=20) -> dict:
    # 返回 { "summary": {kpi...}, "charts": {chart_name: {labels, series}}, "items": [...], "total": n }
```
- 所有函数遵循现有 `meter_service.py` 模式：`select()` + `func.count()`、keyword-only filters、`_to_dict` 序列化
- 数据不足时（查询返回空），用合理 mock 值兜底并在 `summary.demo = true` 标注

### 2. 修改 `backend/app/api/v1/endpoints/analysis.py`
新增 10 个路由（不改动已有的 daily/compare/consistency/data-quality/reports）：
```
GET /analysis/comm-success-rate    R-01
GET /analysis/non-comm-devices     UC-8
GET /analysis/read-completeness    R-07
GET /analysis/retry-analysis       R-10
GET /analysis/open-alarms          R-12  (注意：与 alarms endpoint 不同，这是报表视图)
GET /analysis/alarm-trend          R-13
GET /analysis/device-health        R-16
GET /analysis/battery-aging        R-18  (信号强度降级版)
GET /analysis/consumption-trend    R-30
GET /analysis/ondemand-history     R-11
```
每个 endpoint 注入 `db: DbSession`，解析 `Query` 过滤参数（date_from/date_to/page/page_size/project_id），委托 service，`return success(data)`。

### 3. 修改 `backend/app/schemas/analysis.py`
新增各报表的 Query 参数 schema（可选，也可直接在 endpoint 用 Query 声明）。

### 4. 不需要改 `backend/app/api/v1/api.py`
analysis router 已注册 `require_permission("analysis")`，新路由自动继承。

---

## 前端改动（3 类文件）

### 1. 修改 `frontend/apps/web-antd/src/api/modules/analysis.ts`
新增 10 个 API 函数 + 对应的 TS interface（Params）。

### 2. 新建 10 个页面文件 `frontend/apps/web-antd/src/views/analysis/`
| 文件 | 报表 |
|------|------|
| `comm-success-rate.vue` | R-01 通信成功率 |
| `non-comm-devices.vue` | UC-8 未通信设备 |
| `read-completeness.vue` | R-07 抄表完整率 |
| `retry-analysis.vue` | R-10 重试分析 |
| `open-alarms-report.vue` | R-12 未确认告警报表 |
| `alarm-trend.vue` | R-13 告警趋势 |
| `device-health.vue` | R-16 设备健康 |
| `battery-aging.vue` | R-18 信号老化 |
| `consumption-trend.vue` | R-30 负荷曲线 |
| `ondemand-history.vue` | R-11 按需抄表 |

每个页面统一结构（参照现有 `daily.vue`/`data-quality.vue`）：
```
<Page auto-content-height>
  ├─ 筛选栏 Card（DatePicker/Select/搜索按钮）
  ├─ KPI 卡片 Row（Statistic 组件 ×4-5）
  ├─ 图表区 Row/Col（EchartsUI + useEcharts + useChartTheme）
  └─ 数据表格 Card（Table + 服务端分页 + Tag 状态渲染）
</Page>
```

### 3. 重构 `frontend/apps/web-antd/src/router/routes/modules/analysis.ts`
将扁平结构改为按设计稿分组，保留已有 5 个页面：
```ts
Analysis (数据分析) order:3
├─ 基础分析 (children)
│   ├─ 每日分析 daily        [已有]
│   ├─ 对比分析 compare      [已有]
│   ├─ 分析报告 report       [已有]
│   ├─ 一致性检查 consistency [已有]
│   └─ 数据质量 data-quality  [已有]
├─ 通信与抄表 (children)
│   ├─ 通信成功率 comm-success-rate      [新]
│   ├─ 未通信设备 non-comm-devices        [新]
│   ├─ 抄表完整率 read-completeness       [新]
│   ├─ 重试分析 retry-analysis            [新]
│   └─ 按需抄表 ondemand-history          [新]
├─ 告警与诊断 (children)
│   ├─ 未确认告警 open-alarms-report      [新]
│   ├─ 告警趋势 alarm-trend               [新]
│   ├─ 设备健康 device-health             [新]
│   └─ 信号老化 battery-aging             [新]
└─ 用电分析 (children)
    └─ 负荷曲线 consumption-trend          [新]
```

---

## 执行顺序（建议按此分批提交）

**批次 1：后端全部 10 个接口**（一个 commit）
- 新建 `analysis_service.py` + 修改 `analysis.py` endpoint
- 可用 `curl` 或 Swagger 逐个验证接口返回结构

**批次 2：前端路由+API 模块**（一个 commit）
- 重构 `analysis.ts` 路由分组
- 新增 `analysis.ts` API 函数

**批次 3-4：前端页面**（每批 5 个页面，各一个 commit）
- 批次 3：通信与抄表组（5 页）
- 批次 4：告警诊断 + 用电分析（5 页）

---

## 关键设计决策

1. **报表不新建权限**：全部复用 `analysis` 权限，不细分到单个报表
2. **mock 兜底策略**：service 层查询返回空时填充 mock 数据，`summary.demo=true` 让前端显示「演示数据」标记
3. **图表统一用 ECharts**（非设计稿的 Chart.js），复用现有 `useChartTheme` 支持暗色模式
4. **R-18 电池报表降级**：当前无电池数据，改用 `signal_strength` 做信号老化报表，保持数据真实性
5. **GIS 类报表（11个）暂不做**：需要引入地图组件库和地理数据，留到第二批
6. **客户档案类报表（R-27/33/34/35）暂不做**：需要客户系统数据对接，留到第二批

---

## 不在本次范围
- GIS 地图报表（需地图库+地理数据）
- 客户/合规报表（需 CIS 系统对接）
- 固件管理报表（需固件升级流程）
- 审计日志报表（需审计中间件）
- 导出功能（后续迭代）
