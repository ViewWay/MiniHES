# MiniHES 前端架构设计

> **文档定位**：本文档详述 MiniHES 前端（`frontend/apps/web-antd`）的实际架构，按"分层架构 → 基础设施 → 业务模块 → 已知问题"组织，作为开发、维护、扩展前端的权威参考。
>
> **最后核对**：2026-07-04（对齐 vue-vben-admin 5.7.0 / web-antd 实际代码）

---

## 一、技术栈与整体架构

### 1.1 技术选型

| 层级 | 技术 | 版本 |
|------|------|------|
| 框架 | Vue 3（Composition API + `<script setup>`） | catalog `^3.5.32` |
| UI 库 | Ant Design Vue | catalog `^4.2.6` |
| 图表 | ECharts（经 `@vben/plugins/echarts` 封装） | catalog `^6.0.0` |
| 路由 | Vue Router | catalog `^5.0.4` |
| 状态 | Pinia + 持久化插件 | catalog `^3.0.4` |
| 工具 | @vueuse/core, dayjs | `^14.2.1`, `^1.11.20` |
| 构建 | Vite | catalog `^8.0.10` |
| 类型 | TypeScript | catalog `^6.0.3` |
| 包管理 | pnpm + turbo（monorepo） | `pnpm@10.33`, `turbo@^2.9.6` |
| 脚手架 | vue-vben-admin 5.7.0（二次定制） | - |

### 1.2 整体分层架构

```
main.ts (入口)
  └─ bootstrap.ts (应用装配)
       ├─ adapter/        ← antd 组件适配到 Vben Form/弹窗体系
       ├─ app.vue         ← ConfigProvider(主题算法 + 语言) 全局注入
       ├─ @vben/stores    ← Pinia + persistedstate (access/user 全局 store)
       │    └─ store/     ← 本地业务 store (auth/alarm/meter/task)
       ├─ @vben/access    ← v-access 权限指令
       └─ router/         ← 路由 + 守卫
            ├─ routes/core.ts        ← 根布局 + 登录页 + 404
            ├─ routes/modules/*.ts   ← 7 个业务路由模块（自动导入）
            └─ guard.ts              ← 访问守卫（token + 动态路由生成）

请求层    api/request.ts   ← RequestClient (axios-based, @vben/request)
          api/modules/*.ts ← 7 个业务模块共 60+ 个 API 函数

组件层    composables/     ← useChartTheme + useWebSocket
          components/      ← 业务组件 (meter/ 下 3 个)
          constants/       ← 状态映射/主题色/轮询间隔

视图层    views/           ← 7 个业务模块 47 个 .vue + _core 14 个 + demos 1 个
```

### 1.3 视图层代码规模

| 模块 | .vue 数 | 功能 |
|------|---------|------|
| `_core/` | 14 | vben 框架自带（登录/注册/404/about/profile/fallback） |
| `dashboard/` | 7 | 数据概览 + 告警工作台（含 5 个模板 demo 桩） |
| `system/` | 9 | 用户/角色/日志/项目/采集点/告警规则/DB监控/健康/归档 |
| `analysis/` | 5 | 每日分析/对比/报告/一致性/数据质量 |
| `meter/` | 4 | 列表/详情/借用/维修 |
| `task/` | 4 | 列表/创建/日志/监控 |
| `screen/` | 3 | 项目概览/项目详情/单表监控（大屏） |
| `test/` | 3 | 测试列表/报告/缺陷 |
| `demos/` | 1 | antd 组件 demo（模板残留） |
| **合计** | **60 .vue + 53 .ts = 113 源文件** | |

---

## 二、Monorepo 结构（vue-vben-admin 5.7.0）

### 2.1 workspace 组织

```
frontend/
├── apps/
│   ├── web-antd/          ★ 本项目唯一主应用（已深度定制）
│   ├── backend-mock/      ★ Nitro mock 服务（70+ 端点，对接全部业务模块）
│   ├── web-ele/           ✗ 上游模板残留（仅 _core/dashboard/demos）
│   ├── web-naive/         ✗ 上游模板残留
│   ├── web-tdesign/       ✗ 上游模板残留
│   └── web-antdv-next/    ✗ 上游模板残留
├── packages/
│   ├── @core/             ← 无框架依赖的原子层（@vben-core/*）
│   │   ├── base/          design / icons / shared / typings
│   │   ├── ui-kit/        form / layout / menu / popup / shadcn / tabs-ui（基于 reka-ui）
│   │   ├── composables
│   │   └── preferences
│   ├── effects/           ← 业务效果层（@vben/*）
│   │   ├── access         权限控制
│   │   ├── common-ui      通用组件
│   │   ├── hooks          组合式函数
│   │   ├── layouts        后台布局（BasicLayout 等）
│   │   ├── plugins        echarts / tiptap / vxe-table / motion 集成
│   │   └── request        axios 请求客户端封装
│   └── constants / icons / locales / preferences / stores / styles / types / utils
├── internal/              ← 工具链（node-utils / tsconfig / vite-config / lint-configs）
└── scripts/               ← turbo-run / vsh CLI
```

> **说明**：本项目采用「在上游 vue-vben-admin monorepo 基础上只定制 `web-antd` + `backend-mock`」的模式。其余 4 个 UI 框架变体（web-ele/web-naive/web-tdesign/web-antdv-next）是上游多 UI 框架模板的残留，`src/views/` 下仅有 `_core`/`dashboard`/`demos` 三个模板目录，无任何 MiniHES 业务代码，实际不使用。

### 2.2 web-antd 依赖的 @vben/* 包（14 个）

```
@vben/access          权限（v-access 指令 + generateAccess 动态路由）
@vben/common-ui       通用 UI（loading 指令、tippy、通知组件）
@vben/constants       常量
@vben/hooks           业务组合式函数
@vben/icons           图标封装
@vben/layouts         后台布局组件
@vben/locales         i18n（zh-CN / en-US）
@vben/plugins         echarts / motion 等插件集成
@vben/preferences     偏好设置（主题/布局/语言运行时配置，含 isDark）
@vben/request         请求客户端（axios 封装）
@vben/stores          全局 store（accessStore / userStore）
@vben/styles          全局样式
@vben/types           类型定义
@vben/utils           工具函数
```

依赖链：`web-antd` → `@vben/effects/*` → `@vben-core/*`。构建时 turbo 通过 `^build` 保证 @core 先于 effects 先于 app 编译。

### 2.3 关键命令

```bash
# 根目录（frontend/）
pnpm dev:antd              # 启动 web-antd（mode=development）
pnpm build:antd            # 构建 web-antd（8GB 堆内存，turbo 拓扑序）
pnpm check:type            # 全 workspace 类型检查（turbo run typecheck）
pnpm lint                  # vsh lint
pnpm test:unit             # vitest run --dom

# web-antd 内（apps/web-antd/）
pnpm dev                   # 等价于根的 dev:antd
pnpm typecheck             # vue-tsc 单独检查 web-antd
pnpm test:e2e              # playwright test（testDir=./tests/e2e）
```

---

## 三、启动流程（main.ts → bootstrap.ts）

```
main.ts
 ├─ initPreferences(namespace)    ← 偏好设置初始化（含 preferencesExtension 扩展字段）
 └─ dynamic import('./bootstrap')
      └─ bootstrap(namespace)
           ├─ initComponentAdapter / initSetupVbenForm  ← antd 组件适配 Vben 表单
           ├─ createApp(App)
           │    └─ app.vue: ConfigProvider(theme=算法, locale) → <App><RouterView/></App>
           ├─ registerLoadingDirective(v-loading / v-spinning)
           ├─ setupI18n(zh-CN / en-US)
           ├─ initStores(Pinia + persistedstate)
           │    ├─ @vben/stores: useAccessStore(token/codes/routes/menus/loginExpired)
           │    │               useUserStore(userInfo)
           │    └─ 本地 store/: auth / alarm / meter / task
           ├─ registerAccessDirective(v-access)
           ├─ initTippy / MotionPlugin
           ├─ app.use(router) → createRouterGuard
           │    ├─ setupCommonGuard (进度条 + meta.loaded)
           │    └─ setupAccessGuard (token 校验 + 首次登录动态生成菜单)
           └─ app.mount('#app')
```

**app.vue 主题算法**：`isDark`（来自 `@vben/preferences`）→ `theme.darkAlgorithm` / `theme.defaultAlgorithm`；`preferences.app.compact` → 叠加 `theme.compactAlgorithm`。

**preferencesExtension 扩展字段**：`enableFormFullscreen` / `tenantMode` / `defaultTableSize` / `reportTitle`。

---

## 四、业务模块设计（views/）

### 4.1 dashboard/ — 仪表盘

**模块职责**：首页数据概览 + 告警工作台。

| 页面 | 路由 | 功能 | API | composable | 特殊组件 |
|------|------|------|-----|-----------|---------|
| `analytics/index.vue` | `/dashboard/analytics` | 数据概览（affixTab 固定） | `getMeterList`/`getAlarmList`/`getAlarmStats`/`getProjectList`/`getTaskList`（Promise.allSettled 并发） | `useChartTheme` | EchartsUI 折线图、Statistic、Progress、Table |
| `workspace/index.vue` | `/dashboard/workspace` | 告警管理 | `getAlarmList`/`getAlarmStats`/`handleAlarm`/`exportAlarms` | 自行实现轮询 | Table、Modal、DatePicker.RangePicker、Statistic |

**关键交互**：
- analytics：4 类统计并发拉取；近 7 天采集成功率趋势折线图；最近告警表（5 条）；项目进度表（含 Progress）；主题切换自动重渲染
- workspace：4 列统计卡（总告警/未处理/严重/警告）；筛选条（级别/类型/状态/日期）；分页表；处理弹窗；**轮询** `POLL_INTERVALS.ALARM`（30s），`visibilitychange` 页面隐藏时停止

> **⚠️ 模板残留 demo**：`analytics/analytics-trends.vue`、`analytics-visits.vue`、`analytics-visits-data.vue`、`analytics-visits-sales.vue`、`analytics-visits-source.vue` 这 5 个子组件是 vben 自带的图表 demo 桩（硬编码数据、无 API 调用），**未被 index.vue 引用**。建议后续业务化或清理，详见第七章。

---

### 4.2 meter/ — 仪表管理

**模块职责**：设备全生命周期（入库→测试→借用→维修→报废）。

| 页面 | 路由 | 功能 | 关键 API |
|------|------|------|---------|
| `list.vue` | `/meter/list` | 设备列表 | `getMeterList`/`createMeter`/`changeMeterStatus`/`importMeters`/`exportMeters` |
| `detail.vue` | `/meter/detail/:id`（hideInMenu） | 设备详情（5 Tab） | `getMeterDetail`/`updateMeter`/`changeMeterStatus`/`getMeterStatusHistory`/`uploadMeterAttachment`/`updateMeterComm` |
| `borrow.vue` | `/meter/borrow` | 借用审批流 | `getBorrowRecords`/`approveBorrow`/`createBorrowRequest`/`returnBorrow` |
| `repair.vue` | `/meter/repair` | 维修记录 | `getRepairRecords`/`addRepairRecord` |

**list.vue 关键交互**：
- 搜索条（关键词/状态/项目）；分页表
- **状态流转**：`statusFlowMap` 定义 in_stock→testing/borrowed/repairing/scrapped 合法迁移，Popconfirm 确认后调 `changeMeterStatus`
- **批量导入**：Upload 上传 .xlsx/.xls/.csv + 预览表 + `importMeters`
- **导出**：`exportMeters` Blob 下载 .xlsx
- 权限：`v-access:code="'meter:create'"`

**detail.vue 关键设计**：
- 5 Tab：基本信息 / 通信配置 / 实时状态 / 状态变更记录（Timeline）/ 附件管理
- 借用走 `BorrowDialog` 业务组件（`#/components/meter/BorrowDialog.vue`）
- 状态流转按钮按 `statusFlowOptions` 动态渲染
- 自定义组件：`StatusBadge`（`#/components/meter/StatusBadge.vue`）

**borrow.vue 审批流**：5 态（pending_department / pending_lab / approved / rejected / cancelled），新建申请 → 批准/拒绝 Popconfirm → 归还操作。

---

### 4.3 task/ — 采集任务

**模块职责**：任务调度全流程（创建→执行→监控→日志）。

| 页面 | 路由 | 功能 | 关键 API / composable |
|------|------|------|----------------------|
| `list.vue` | `/task/list` | 任务列表 | `getTaskList`/`executeTask`/`toggleTask`/`deleteTask` |
| `create.vue` | `/task/create` | 创建任务（3 步向导） | `createTask` + `getProjectList`/`getMeterTypes`/`getWireTypes`/`getMeterList` |
| `logs.vue` | `/task/logs` | 执行日志 | `getTaskLogs`/`getTaskDeviceLog` |
| `monitor.vue` | `/task/monitor` | 实时监控 | `getTaskList`/`getTaskDetail` + **`useWebSocket`** |

**create.vue 三步向导**：
1. Step 1 基本配置：名称 / 分类 RadioGroup / 类型 RadioGroup / 调度（interval|cron）/ 优先级 / 重试 / 超时 / 立即启用
2. Step 2 设备筛选：项目 / 表型 / 线制多选 → 设备表 Checkbox 全选/清除（`filteredDevices` computed 过滤）
3. Step 3 执行内容：操作类型 Select + OBIS 码多选（11 个 DLMS 点位定义）+ 确认 Descriptions

**monitor.vue 实时能力**（**唯一使用 `useWebSocket` 的页面**）：
- 5 统计卡（活跃/执行中/已完成/失败/平均成功率）
- 轮询 `POLL_INTERVALS.TASK_MONITOR`（5s）自动刷新
- WebSocket：`wsConnect()` + `wsSubscribe('task:progress', cb)` 实时更新任务状态/成功率/设备数，新任务触发 `fetchData()`
- `onUnmounted` 调 `wsUnsubscribe` 清理

**logs.vue**：从 `route.query.task_id` 取任务 ID；日期范围筛选；**轮询** `POLL_INTERVALS.TASK_LOGS`（10s，可开关）+ `visibilitychange` 控制；设备执行详情弹窗（`getTaskDeviceLog`）。

---

### 4.4 analysis/ — 数据分析

**模块职责**：数据分析中心（5 个页面）。

| 页面 | 路由 | 功能 | 图表数 |
|------|------|------|--------|
| `daily.vue` | `/analysis/daily` | 每日分析 | 2（电能趋势 area 图 + 曲线完整性柱状图） |
| `compare.vue` | `/analysis/compare` | 多设备对比 | 2（电能对比多线图 + 偏差率/完整率双柱状图） |
| `report.vue` | `/analysis/report` | 分析报告 | 2（质量评分趋势 + 异常数量趋势） |
| `consistency.vue` | `/analysis/consistency` | 一致性检查 | 1（一致性分布环形饼图） |
| `data-quality.vue` | `/analysis/data-quality` | 数据质量 | 1（近 7 日质量评分趋势柱状图） |

**共性特征**：
- 均使用 `useChartTheme`（daily 用 `watchThemeAndRerender`，其余直接 `useEcharts`）
- 均支持项目筛选（`getProjectList`）
- 多个页面在 API 数据不足时用 `generateDemoXxx()` 兜底 mock（daily/compare/data-quality）

**daily.vue 11 项检查项**（对齐 PRD 3.3.1）：电能 / 时钟 / 日结算 / 月结算 / 负荷曲线 / 电网质量 / 事件等。支持从 `route.query.meter_id`/`date` 跳转自动查询。PDF 导出（`exportDailyReport`）。

**compare.vue**：多设备选择（至少 2 台）+ 日期范围（含 presets：最近 7 天/30 天/本月，用 dayjs 计算）。

**consistency.vue**：PG 任务天数 vs 时序数据天数 vs 缺失天数对比 + "执行检查"按钮（`triggerConsistencyCheck`）。

> **⚠️ 注意**：`analysis.py` 后端 9 个路由当前返回硬编码 mock（详见后端文档），前端这些页面在真实 API 接通前依赖 `generateDemoXxx()` 兜底。后端闭环是 Phase 4 待办。

---

### 4.5 screen/ — 大屏展示

**模块职责**：可视化大屏（3 个页面，均用 `useChartTheme`，`watch(isDark)` 重渲染）。

| 页面 | 路由 | 菜单可见性 | 功能 |
|------|------|-----------|------|
| `overview.vue` | `/screen/overview` | 显示 | 项目概览大屏 |
| `project.vue` | `/screen/project`（query.id 传参） | hideInMenu | 项目详情大屏 |
| `meter.vue` | `/screen/meter/:id?`（path 传参） | hideInMenu | 单表实时监控 |

**overview.vue**：6 统计卡（项目/设备/在线/离线/告警/在线率）+ 3 图表（堆栈使用率堆叠柱状图、在线率环形饼图、告警趋势柱状图）+ 项目状态表（跳转 `/screen/project?id=`）+ 事件统计 4 卡。

**project.vue**：6 统计卡 + 4 图表（能耗曲线 / 通信状态饼图 / 堆栈监控横向柱状图 / 电能质量曲线）+ 设备列表表（跳转 `/screen/meter/:id`）。大量 `generateMockSeries()`/`Math.random()` mock 图表数据。

**meter.vue**（单表实时监控，**最复杂的实时页面**）：
- 6 统计卡（电压 ABC / 频率 / 堆栈使用 / EEPROM 写入）
- 3 图表：实时电压/电流双 Y 轴折线图、稳定性评分 **gauge 仪表盘**（`themedGauge`）、读数事件 24h 柱状图
- **3 秒轮询**：`setInterval(pollData, POLL_INTERVALS.METER_REALTIME)`，`jitter()` 模拟数据波动，`updateRtChart()` 用 `useEcharts` 的 `updateData` **增量更新**（保留 60 个数据点滚动，非全量重渲染）
- A/B/C 相详情 Descriptions + 堆栈监控卡（Progress + 三级阈值）+ EEPROM 监控卡（老化/磨损/正常三级）
- `onUnmounted` 清除轮询定时器

---

### 4.6 test/ — 测试管理

**模块职责**：测试任务 + 测试报告 + 缺陷管理。

| 页面 | 路由 | 菜单可见性 | 功能 |
|------|------|-----------|------|
| `list.vue` | `/test/list` | 显示 | 测试任务列表（创建/筛选） |
| `report.vue` | `/test/report/:id?` | hideInMenu（activePath=/test/list） | 测试报告详情 |
| `defect.vue` | `/test/defect` | 显示 | 缺陷管理 |

**list.vue**：3 筛选（类型/状态/项目）；创建测试任务弹窗（4 种类型：protocol/accuracy/function/stability，5 种状态：pending/running/completed/failed/cancelled）；跳转报告 `/test/report/:id`。

**report.vue**：
- 报告详情（报告编号/类型/环境/时长/固件/硬件版本）+ 缺陷列表子表
- 编辑报告弹窗（7 字段）
- **邮件分发弹窗**：7 种收件人 CheckboxGroup（项目测试/研发负责人/功能测试/测试领导/研发领导/部门 + 附言）
- PDF 导出（`exportTestReport`）

**defect.vue**：2 筛选（严重程度/状态）；状态流转 `statusTransitions` 定义 open→in_progress→resolved→closed **单向流转**，按当前状态动态渲染流转按钮；3 级严重程度（critical/major/minor）。

---

### 4.7 system/ — 系统管理

**模块职责**：系统配置与运维中心（9 个页面）。

| 页面 | 路由 | 功能 | 关键组件 |
|------|------|------|---------|
| `user.vue` | `/system/user` | 用户管理 | Table + Modal + 多选角色 Select + 重置密码 |
| `role.vue` | `/system/role` | 角色管理 | Table + **Tree（checkable 权限树）** + 独立分配权限弹窗 |
| `log.vue` | `/system/log` | 操作日志 | Table（**含 expandedRowRender 展开行**展示 JSON 差异）+ 导出 |
| `project.vue` | `/system/project` | 项目管理 | Table + Modal（3 态：active/completed/archived） |
| `meter-point.vue` | `/system/meter-point` | 采集点配置 | Table + Modal（OBIS 点号/类型/数据类型/单位/协议/存储目标） |
| `alarm-rule.vue` | `/system/alarm-rule` | 告警规则 | Table + Switch 列内启停 + 条件配置 JSON |
| `db-monitor.vue` | `/system/db-monitor` | 数据库监控 | **4 个 EchartsUI** + 4 告警 Alert + 30s 轮询 |
| `health.vue` | `/system/health` | 系统健康 | 6 服务状态卡 + 15s 轮询 + 总览 Banner |
| `data-archive.vue` | `/system/data-archive` | 数据归档 | 4 统计卡 + 手动归档弹窗 |

**role.vue 权限树**：`Tree` 组件 `checkable`，`fieldNames` 映射 `{name→title, id→key, children→children}`；`defaultPermissions` 5 组兜底（设备/任务/分析/测试/系统管理）；独立"分配权限"弹窗调 `updateRole` 提交 `permission_ids`。

**db-monitor.vue**（图表密集页）：
- 4 图表：PG 连接数趋势（area + markLine 告警阈值）/ 时序写入速率 area / Redis 内存 gauge / Redis 命中率 gauge
- 4 告警 Alert 横幅（PG 连接数>80、PG 慢查询>1000、Redis 内存>80%、Redis 命中率<80%）
- 3 数据库卡片（PG / 时序库 / Redis）
- **30s 轮询** `setInterval(fetchData, POLL_INTERVALS.DB_MONITOR)`
- 用 `useChartTheme`（含 `themedGauge`）
- API 失败时用完整 demo 数据兜底

**health.vue**：
- 总览 Banner（圆形状态指示器 OK/!/? + 健康/部分异常/故障 Tag）
- 6 服务状态卡（Frontend/Backend API/PostgreSQL/时序库/Redis/Celery Worker）
- `overallHealth` computed 三级判定（全在线=绿/关键服务离线=红/部分离线=黄），`criticalServices = ['Backend API', 'PostgreSQL']`
- **15s 轮询** `setInterval(fetchData, POLL_INTERVALS.HEALTH)`

---

## 五、跨模块技术栈共性

| 维度 | 事实 |
|------|------|
| **UI 组件** | ant-design-vue 全局使用（Table/Form/Modal/Card/Statistic/Tag/Select/Steps/Tabs/Timeline/Tree/Upload/Popconfirm/Descriptions/Progress/Badge/Alert/DatePicker 等） |
| **图表** | `@vben/plugins/echarts` 的 EchartsUI + useEcharts；15 个页面用图表，9 个页面用 `useChartTheme` |
| **图表主题** | `useChartTheme` composable（themedAxis/themedTooltip/themedLegend/themedGauge/watchThemeAndRerender），亮/暗模式自适应 |
| **实时通信** | `useWebSocket` composable（topic 订阅 + 3 次重连退避），**仅 task/monitor.vue 使用** |
| **轮询模式** | 5 个页面用 `setInterval` 轮询（dashboard/workspace、task/logs、task/monitor、system/db-monitor、system/health），间隔由 `POLL_INTERVALS` 常量统一管理 |
| **导出下载** | 统一模式：Blob + `window.URL.createObjectURL` + 动态 `<a>` 标签点击，6 个页面有导出 |
| **权限控制** | `v-access:code="'xxx:yyy'"` 指令（meter list/task list/system user+role） |
| **分页** | 统一 `{current, pageSize, total, showSizeChanger, showTotal}` + `DEFAULT_PAGE_SIZE` 常量 |
| **状态映射** | `#/constants` 集中定义（METER_STATUS_MAP/TASK_STATUS_MAP/ALARM_SEVERITY_MAP/PROTOCOL_OPTIONS 等） |
| **Mock 兜底** | screen/* / analysis/* / system/db-monitor+health 在 API 失败时用 demo/mock 数据兜底 |
| **路由传参** | 3 种：path `:id`（meter detail、screen/meter）/ path `:id?`（test/report）/ query（screen/project、task/logs、analysis/daily） |

---

## 六、基础设施层设计

### 6.1 请求层（api/）

**封装基础**：基于 `@vben/request`（workspace 包，内部封装 axios）。`api/request.ts` 实例化两个客户端：

| 实例 | 用途 | 配置 |
|------|------|------|
| `requestClient` | 业务请求（api/modules 全部走它） | `responseReturn: 'data'`（自动解包 `.data` 字段） |
| `baseRequestClient` | 认证专用（refresh/logout） | 无拦截器，避免循环依赖 |

**拦截器链**（注册顺序即执行顺序）：

1. **请求拦截器**：注入 `Authorization: Bearer <token>`（token 来自 `useAccessStore().accessToken`）+ `Accept-Language: <locale>`
2. **响应拦截器 1**（业务码解包）：`defaultResponseInterceptor({ codeField:'code', dataField:'data', successCode:200 })`
3. **响应拦截器 2**（token 过期）：`authenticateResponseInterceptor` —— 过期时调 `refreshTokenApi()` 刷新并写回 store；重认证时按 `loginExpiredMode` 弹模态或跳登录页
4. **响应拦截器 3**（错误兜底）：`errorMessageResponseInterceptor` —— 用 antd `message.error()` 展示错误

**API 模块清单**（`api/modules/`，7 文件 60+ 函数）：

| 模块 | 函数数 | 主要端点域 |
|------|--------|-----------|
| `meter.ts` | 16 | `/meters` CRUD + 状态 + 借用 + 维修 + 附件 + 通信 + 导入导出 |
| `system.ts` | 13 | `/system/users` + `/system/roles` + `/system/audit-logs` + `/system/db-monitor` + `/system/health` + `/system/data-archive` |
| `project.ts` | 10 | `/projects` CRUD + `/meter-types` + `/wire-types` + `/meter-points` CRUD |
| `test.ts` | 10 | `/tests` + `/tests/:id/report` + `/defects` + 导出/分发 |
| `alarm.ts` | 8 | `/alarms` 查询/处理/统计/导出 + `/alarm-rules` CRUD |
| `task.ts` | 8 | `/tasks` CRUD + 执行 + 启停 + `/tasks/:id/logs` |
| `analysis.ts` | 8 | `/analysis/daily` + `/analysis/compare` + `/analysis/reports` + `/analysis/consistency` + `/analysis/data-quality` |

**框架核心**（`api/core/`，4 文件）：`auth.ts`（login/refresh/logout/codes）、`user.ts`（getUserInfo）、`menu.ts`（getAllMenus → 动态路由生成）。`api/index.ts` 用 `export *` 聚合 `core/` + 全部 `modules/`。

> **端点路径规律**：所有 `api/modules/*` 函数的 URL **不带 `/api/v1` 前缀**——前缀由 `apiURL`（从 `VITE_GLOB_API_URL` 解析）在 baseURL 层注入。

### 6.2 状态层（store/）

**全局 store**（来自 `@vben/stores`，由 `initStores` 注册）：
- `useAccessStore`：token / accessCodes / accessRoutes / menus / loginExpired（持久化）
- `useUserStore`：userInfo

**本地业务 store**（`store/`，4 文件，setup 风格 defineStore）：

| Store | id | 核心状态 | 关键 actions |
|-------|-----|---------|-------------|
| `auth.ts` | `'auth'` | `loginLoading` | `authLogin`（login→setToken→并行拉用户+权限码→跳转）、`logout`、`fetchUserInfo` |
| `alarm.ts` | `'alarm'` | `alarms` / `total` / `loading` / `stats` / `statsLoading` | `fetchAlarms` / `handleAlarm`（本地更新+刷 stats）/ `fetchAlarmStats` |
| `meter.ts` | `'meter'` | `meters` / `currentMeter` / `total` / `loading` + 缓存字段（meterTypes/projects/wireTypes，**有缓存：len>0 跳过**） | `fetchMeters` / `fetchMeterDetail` / `fetchMeterTypes`（缓存）/ `fetchProjects`（缓存）/ `updateMeterStatus` |
| `task.ts` | `'task'` | `tasks` / `total` / `loading` / `currentTask` / `taskLogs` | `fetchTasks` / `fetchTaskDetail` / `fetchTaskLogs` / **`updateTaskInList(id, updates)`**（供 WebSocket 实时更新本地列表） |

**统一模式**：`loading` ref 包裹 async fetch；列表接口解析 `res.items`/`res.total`；item 接口均带 `[key:string]:any` 开放索引签名。

### 6.3 组件层（composables/ + components/ + constants/）

#### composables/useChartTheme.ts

```
useChartTheme() → {
  chartColors,      // ComputedRef<{text, textSecondary, axisLine, splitLine, tooltipBg, ...}>，按 isDark 切换调色板
  isDark,           // ComputedRef<boolean>（来自 @vben/preferences）
  themedAxis(direction: 'x'|'y', overrides?),   // ECharts axis 配置工厂
  themedTooltip(overrides?),                     // {trigger:'axis', backgroundColor, borderColor, textStyle}
  themedLegend(overrides?),                      // {textStyle:{color}}
  themedGauge(overrides?),                       // 仪表盘样式（axisTick/splitLine/axisLabel/detail）
  watchThemeAndRerender(renderFn, immediate=false) // watch(isDark, renderFn)
}
```

**使用方（9 处）**：`analysis/daily`、`dashboard/analytics/index`、`system/db-monitor`、`screen/{meter,overview,project}` + 另外 3 处（analysis 内部其他页直接用 useEcharts）。

#### composables/useWebSocket.ts

```
WSMessage { topic: string; type: string; data: any }
MAX_RETRIES = 3

useWebSocket() → {
  connected,        // Ref<boolean>
  lastMessage,      // Ref<WSMessage|null>
  connect(),        // 协议自适应 wss/ws，URL: ${protocol}//${host}/ws?token=${token}（剥离 /api/vN 后缀）
  subscribe(topic, callback),    // 注册回调 + 发送 {action:'subscribe', topics:[topic]}
  unsubscribe(topic),           // 删回调 + 发送 {action:'unsubscribe'}
  disconnect()      // 清 timer + 阻止重连 + close
}
// onclose 退避 5s 重连（< MAX_RETRIES）
// 自动 onUnmounted(() => disconnect())
```

**使用方（1 处）**：`views/task/monitor.vue`（subscribe `'task:progress'`）。

#### components/meter/（3 个业务组件）
- `StatusBadge.vue` — 设备状态徽章（meter detail 用）
- `BorrowDialog.vue` — 借用申请弹窗（meter detail 用）
- `MeterCard.vue` — 设备卡片

#### constants/（4 文件 + barrel）

| 文件 | 关键导出 |
|------|---------|
| `common.ts` | `DEFAULT_PAGE_SIZE=20`、`METADATA_FETCH_SIZE=200`、`POLL_INTERVALS={ALARM:30000, TASK_MONITOR:5000, TASK_LOGS:10000, HEALTH:15000, DB_MONITOR:30000, METER_REALTIME:3000}`、`THEME_COLORS={SUCCESS,WARNING,ERROR,...}`（antd v4 色板） |
| `alarm.ts` | `ALARM_SEVERITY_MAP`、`ALARM_TYPE_MAP`、`ALARM_SEVERITY_OPTIONS` |
| `meter.ts` | `METER_STATUS_MAP`（10 状态）、`PROTOCOL_OPTIONS`、`STATUS_FLOW_OPTIONS`（状态机迁移） |
| `task.ts` | `TASK_STATUS_MAP`、`TASK_TYPE_MAP`、`TASK_CATEGORY_MAP`、`LOG_STATUS_MAP` |

### 6.4 路由层（router/）

**组织方式**：
- `routes/index.ts` 用 `import.meta.glob('./modules/**/*.ts', { eager: true })` + `mergeRouteModules` 合并业务路由为 `dynamicRoutes`
- `access.ts` 用 `import.meta.glob('../views/**/*.vue')` 作为动态组件映射表（后端菜单返回字符串路径 → 解析为组件）
- 分层：`routes`（初始化，含 coreRoutes + 404）vs `accessRoutes`（需权限校验）

**守卫**（`guard.ts`）：
- `setupCommonGuard`：进度条 + meta.loaded 记录
- `setupAccessGuard`（核心）：core 路由放行 → 无 token 跳登录（带 redirect）→ 已登录但未校验时 `fetchUserInfo()` + `generateAccess()` 动态生成菜单/路由

**meta 字段约定**：`title` / `icon`（lucide:xxx）/ `order`（排序，dashboard=-1 最前，system=10 最后）/ `hideInMenu` / `hideInBreadcrumb` / `hideInTab` / `affixTab`（固定 tab）/ `activePath`（详情页高亮父菜单）/ `ignoreAccess`（绕过权限）。

**业务路由模块**（`router/routes/modules/*.ts`，7 个）：

| 模块 | order | 子路由数 | 子路由 name |
|------|-------|---------|------------|
| `dashboard.ts` | -1 | 2 | Analytics（affixTab）、Workspace |
| `meter.ts` | 1 | 4 | MeterList、MeterDetail（hideInMenu）、MeterBorrow、MeterRepair |
| `task.ts` | 2 | 4 | TaskList、TaskCreate、TaskLogs、TaskMonitor |
| `analysis.ts` | 3 | 5 | AnalysisDaily、AnalysisCompare、AnalysisReport、Consistency、DataQuality |
| `screen.ts` | 4 | 3 | ScreenOverview、ScreenProject（hideInMenu）、ScreenMeter（hideInMenu） |
| `test.ts` | 5 | 3 | TestList、TestReport（hideInMenu）、TestDefect |
| `system.ts` | 10 | 9 | SystemUser、SystemRole、SystemLog、ProjectManage、MeterPoint、AlarmRule、DbMonitor、SystemHealth、DataArchive |

`routes/core.ts`：Root（`/`，BasicLayout，redirect→homePath）+ Authentication（`/auth`，AuthPageLayout，含 Login/CodeLogin/QrCodeLogin/ForgetPassword/Register）+ FallbackNotFound（`/:path(.*)*`）。

### 6.5 布局层（layouts/）

**布局组件主体来自 `@vben/layouts`**，web-antd 仅做插槽级定制（3 文件）：

| 文件 | 职责 |
|------|------|
| `layouts/index.ts` | 导出 `BasicLayout`（懒加载本地 `./basic.vue`）、`AuthPageLayout`（懒加载 `./auth.vue`）、`IFrameView`（来自 @vben/layouts） |
| `layouts/basic.vue` | 包装 @vben/layouts 的 BasicLayout，注入插槽：`#user-dropdown`（用户菜单）、`#notification`（通知）、`#extra`（登录过期模态）、`#lock-screen`（锁屏）+ 水印（useWatermark，内容默认 username-realName） |
| `layouts/auth.vue` | 包装 AuthPageLayout，传 appName/logo/pageTitle |

Root 路由挂 `basic.vue` 作为所有业务页父容器，子路由自动套用 BasicLayout。

### 6.6 Mock 服务（backend-mock/）

**规模**：基于 **Nitro** 框架，`api/` 下约 **70+ 个端点 .ts 文件**，覆盖全部业务模块（meters/tasks/tests/system/analysis/alarms/projects/auth 等）。配置在 `nitro.config.ts`，对 `/api/**` 开启 CORS。

**Mock / 真实后端切换**（由 `apps/web-antd/vite.config.ts` 自行实现的 proxy 控制）：

```ts
// apps/web-antd/vite.config.ts
const isMock = env.VITE_NITRO_MOCK !== 'false';
const realApiUrl = env.VITE_REAL_API_URL || 'http://localhost:8000';
// proxy: /api → isMock ? 'http://localhost:5320/api' : `${realApiUrl}/api`
```

| 环境变量文件 | `VITE_NITRO_MOCK` | 实际指向 |
|-------------|-------------------|---------|
| `.env.development` | `false` | 真实后端 `http://localhost:8000`（当前默认） |
| `.env.development`（改为 true） | `true` | 本地 Nitro Mock `:5320` |
| `.env.production` | — | `https://mock-napi.vben.pro/api`（⚠️ vben 官方 mock，**部署前必须改**） |

---

## 七、已知问题与技术债

> 以下为代码探查中发现的潜在问题，按优先级排列。**不影响当前功能运行**，但建议在后续迭代中处理。

### 7.1 🔴 部署阻塞

#### P0-1：`.env.production` 指向 vben 官方 mock

**位置**：`apps/web-antd/.env.production` → `VITE_GLOB_API_URL=https://mock-napi.vben.pro/api`

**影响**：生产构建会指向 vben 官方的公开 mock 服务，而非 MiniHES 真实后端。**部署前必须修改**为实际后端地址。

**修复**：将 `VITE_GLOB_API_URL` 改为生产环境真实 API 地址。

### 7.2 🟡 代码质量

#### P1-1：`constants/index.ts` 导出不存在的文件

**位置**：`src/constants/index.ts` 中 `export * from './auth'`，但目录下**不存在 `auth.ts`**（仅有 alarm/common/meter/task 四个文件）。

**影响**：`import { ... } from '#/constants'` 时该行解析失败（可能是 `store/index.ts` 的复制粘贴遗留）。

**建议**：删除 `constants/index.ts` 中的 `export * from './auth'` 行。

#### P1-2：`echarts` 未在 web-antd package.json 声明

**位置**：`echarts ^6.0.0` 在 `pnpm-workspace.yaml` catalog 中声明，但 `apps/web-antd/package.json` 的 dependencies 未直接列出。

**影响**：被 15 个 view 直接 `import 'echarts'`，当前通过 workspace transitive 解析可用，但迁移/独立构建时有丢失风险。

**建议**：在 `apps/web-antd/package.json` 的 dependencies 显式添加 `"echarts": "catalog:"`。

#### P1-3：`meter` store 的 `fetchStatusHistory` 调错端点

**位置**：`store/meter.ts` 的 `fetchStatusHistory` 实际调用 `getMeterDetail`（而非 `api/modules/meter.ts` 中专门的 `getMeterStatusHistory` 端点），靠 `res.status_history` 取值。

**影响**：存在未使用或误用专用端点的情况。

**建议**：改为调用 `getMeterStatusHistory(id)` 端点。

#### P1-4：`layouts/basic.vue` 通知硬编码 mock

**位置**：`layouts/basic.vue` 的 `#notification` 插槽硬编码 4 条 mock 通知（采集任务完成/设备通信告警/数据质量报告/维修工单），未接 `useAlarmStore` 或 WebSocket。

**影响**：顶栏通知不反映真实告警数据，与 `useWebSocket` 的实时能力未打通。

**建议**：接入 `useAlarmStore` 或 WebSocket 实时推送。

### 7.3 🟢 模板残留（待清理/业务化）

#### P2-1：dashboard/analytics 下 5 个 demo 桩组件

**文件**：`analytics-trends.vue`、`analytics-visits.vue`、`analytics-visits-data.vue`、`analytics-visits-sales.vue`、`analytics-visits-source.vue`

**状态**：vben 框架自带的图表 demo（硬编码数据、无 API 调用），**未被 index.vue 引用**。

**建议**：业务化为真实的访问/趋势统计，或直接删除。

#### P2-2：demos/antd 目录

**文件**：`demos/antd/index.vue`（antd message/notification 组件演示）

**状态**：纯组件展示，无业务价值。

**建议**：删除。

#### P2-3：4 个上游 UI 框架变体 app

**位置**：`apps/web-ele`、`apps/web-naive`、`apps/web-tdesign`、`apps/web-antdv-next`

**状态**：vue-vben-admin 多 UI 框架模板残留，`src/views/` 下仅有 `_core`/`dashboard`/`demos`，无 MiniHES 业务代码。

**建议**：如确认不会切换 UI 框架，可删除以减小仓库体积；若保留作为升级参考，需在文档中标注"非本项目使用"。

---

## 八、开发指引

### 8.1 新增业务页面

1. 在 `views/<module>/` 下新建 `.vue` 文件
2. 在 `router/routes/modules/<module>.ts` 添加路由（设置 meta.title/icon/order）
3. 在 `api/modules/<module>.ts` 添加 API 函数（或新建模块文件 + 更新 `api/index.ts` barrel）
4. 如需状态管理，在 `store/` 新建 store（参考现有 setup 风格）
5. 如有状态枚举/映射，在 `constants/` 添加（参考现有 MAP/OPTIONS 命名）

### 8.2 新增图表页面

1. 使用 `@vben/plugins/echarts` 的 `EchartsUI` + `useEcharts`
2. **必须**调用 `useChartTheme()` 获取主题化配置（`themedAxis`/`themedTooltip`/`themedLegend`）
3. 调用 `watchThemeAndRerender(renderFn)` 确保亮/暗切换时重绘
4. **禁止**硬编码颜色（`#ccc`/`#333` 等），统一用 `chartColors` 或主题方法

### 8.3 新增轮询页面

1. 使用 `POLL_INTERVALS` 常量定义间隔（勿硬编码魔法数字）
2. 配合 `document.visibilitychange` 事件，页面隐藏时停止轮询
3. `onUnmounted` 必须清除 `setInterval`

### 8.4 主题适配规则

> 承接 v0.6.0 的"大屏主题适配"决策：

- **禁止自定义背景色**，所有组件使用系统主题样式
- ECharts 图表不硬编码颜色，统一用 `useChartTheme()` 提供的主题化方法
- `watch(isDark, ...)` 监听主题变化重渲染图表

---
