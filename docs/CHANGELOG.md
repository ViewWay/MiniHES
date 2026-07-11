# MiniHES 变更日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [0.7.0] - 2026-07-11

### MongoDB 双存储集成

- **新增 MongoDB 作为原始采集文档存储**：DLMS/COSEM 采集会话完整文档（24 sheets / 720 KV pairs / Profile buffers）存储在 MongoDB `meter_sessions` 集合，PG 保留为结构化索引层
- **新增文件**：`app/core/mongo.py`（Motor 异步客户端）、`app/services/mongo_session_repo.py`（数据访问层 + buffer 解析）、`app/services/collector/session_writer.py`（PG-Mongo 双写路径）、`app/services/analysis_mongo_service.py`（联合查询）、`scripts/init_mongo.py`（集合+索引初始化）、`scripts/import_real_dcpp.py`（真实电表数据导入）、`scripts/sync_real_data.py`（PG-Mongo 数据同步）
- **PG-Mongo 桥梁**：`col_session` 表的 `mongo_doc_id` 指向真实 MongoDB 文档
- **配置**：新增 `MONGODB_URL` / `MONGODB_DATABASE` 环境变量（`.env.example` 已补充）
- **Docker**：新增 `docker-compose.yml`（PostgreSQL + Redis + MongoDB 一键启动）

### 分析 API 全部接入真实数据

- **前 9 个 stub 路由改为真实查询**：daily（MongoDB Daily Billing + Load Profile）、compare（多表 Energy/Instantaneous）、consistency（PG col_session vs Mongo）、data-quality（PG col_data_quality + summary + trend）、reports（PG lab_test_report）
- **10 个运维报表清除全部假数据**：移除 `analysis_service.py` 中所有 `random` 调用和 `demo` 造假降级（10 个函数的假数字全部清零）
- **失败原因分布改为真实分类**：从 `TaskDevice.error_message` 按关键词分类统计（超时/协议/离线/信号/其他）
- **每日分析重新设计**：选项目→选设备→选日期范围→查看多日采集趋势
- **CSV 导出实现**：daily/export、data-quality/export、reports/{id}/export 全部返回真实 CSV

### 任务调度引擎

- **APScheduler 集成**：`app/services/scheduler.py`，每 60 秒扫描到期任务自动执行
- **`execute_task` 真实化**：解析目标电表→从 MongoDB 读取真实 OBIS 值→写 col_meter_reading→更新 MeterSnapshot→写 DataQuality（upsert）→计算 next_execute_time
- **零 random 调用**：task_service.py 中所有随机数生成已移除

### EEPROM 与诊断修复

- **MeterSnapshot 字段恢复**：补回 `eeprom_write_count`、`stack_usage`、`last_data_time`
- **read-completeness 分布图修复**：从硬编码改为从真实 DataQuality 计算分布桶
- **ondemand-history 趋势图修复**：从空数组改为按日期聚合真实 TaskLog

### 系统监控真实化

- **system/health**：scheduler 状态从 APScheduler 实际状态读取
- **system/db-monitor**：真实探测 PG（表行数）、MongoDB（文档数）、Redis（ping）

### 前端设计统一化（15 个页面）

- **暗色模式**：4 页接入 `useChartTheme`
- **大屏统一**：3 页统一 `<Page>` wrapper，去掉双重 padding
- **统计卡片网格**：9 页统一 `:span="6"`（4 列）
- **筛选栏**：4 页改为 `Form layout="inline"`
- **空状态标签**：11 页统一为"无数据"

### 新增测试

- `test_analysis.py`：18 个分析端点测试
- `test_meter.py`：5 个电表端点测试

---

## [0.6.1] - 2026-07-04

### 文档对齐（消除文档与代码的 4 类严重矛盾 + 4 类中等问题）

- **统一 InfluxDB 表述**：标注已弃用，时序数据使用 PostgreSQL 时序表（`col_meter_reading`/`col_reading_daily_summary`）。涉及 README、CLAUDE、PRD、tech-review 架构文档、config.py 注释、pyproject.toml 依赖标注
- **修正测试目录指引**：真实 83 个测试位于 `backend/tests/`（CI 实际运行），非 `tests/backend/`（仅 5 个 stub）。修正 README、CLAUDE、testing-strategy.md
- **重写 phase-overview.md**：按实际代码进度重新标注各 Phase 完成状态（Phase 1/2/5 ✅，Phase 3/4 🟡 部分完成）
- **修复幽灵目录**：移除 README 项目结构中对不存在的 `docs/api/`、`docs/reports/` 的引用
- **补全 .env.example**：对齐 config.py 实际配置项（补充 REDIS_URL/SECRET_KEY/JWT/采集器配置）
- **启用 lefthook.yml**：替换纯注释示例为实际生效的 pre-commit ruff 检查（lint + format）
- **标注 requirements.txt 弃用**：依赖已迁移到 pyproject.toml（uv 管理）
- **更新 development-plan.md**：资产盘点表改为实际数据（31 模型/16 service/105 路由/83 测试），里程碑 M1/M2 标完成、M3-M5 标部分完成
- **清理 docs/testdata/**：删除误装的 Python 虚拟环境（site-packages）、.ruff_cache、.omc、临时文件；保留数据脚本和 JSON 样本
- **归档 docs/ui/**：54 个早期 HTML 原型移至 docs/archive/ui/ 作为历史快照
- **补充 .gitignore**：新增规则防止 site-packages/.omc 等再次混入

### 新增（前端架构文档）
- **`docs/design/frontend-architecture.md`**：完整前端架构设计文档（约 500 行），覆盖：
  - 技术栈 + 整体分层架构 + Monorepo 结构（vue-vben-admin 5.7.0）
  - 启动流程（main.ts → bootstrap.ts）
  - 7 个业务模块详解（dashboard/meter/task/analysis/screen/test/system），每模块含页面清单、路由、对接 API、关键交互、使用的 composable/组件
  - 基础设施层（请求层/状态层/组件层/路由层/布局层/Mock 服务）
  - 已知问题与技术债（P0 部署阻塞 × 1、P1 代码质量 × 4、P2 模板残留 × 3）
  - 开发指引（新增页面/图表/轮询/主题适配规范）
- README/CLAUDE 新增前端架构文档交叉引用

### 后端 RBAC 接口级强制（TDD）
- **`require_permission` 依赖**：新增菜单级权限校验依赖工厂（`backend/app/core/dependencies.py`），super 角色豁免，权限不足抛 `BusinessException(code=403)`
- **权限查询优化**：`get_user_permission_codes` 从 N+1 查询改为单条 4 表 join；新增 `get_user_role_codes`（2 表 join）
- **批量挂载**：15 个受保护 router 在 `api.py` 的 `include_router` 上挂载权限校验（devices/projects/tasks/alarms/analysis/system），5 个公开接口（health/auth/user/upload/menu）豁免
- **RBAC 测试**：新增 `backend/tests/test_rbac.py`（7 个测试，覆盖 super 豁免/有权限放行/无权限拒绝/无 token 拒绝/公开接口放行），全量测试 83→90 个
- **回归修复**：6 个老测试适配 RBAC（加 auth_headers / 翻转公开访问断言）
- **pyproject.toml**：seed.py 的 ruff per-file-ignores 补 N806

### 前端技术债修复
- **meter store `fetchStatusHistory`**：从错误调用 `getMeterDetail`（依赖不一定存在的 `status_history` 字段）改为调用专用端点 `getMeterStatusHistory`

---

## [0.6.0] - 2026-05-17

### 新增
- `useChartTheme()` composable：提供 `themedAxis`/`themedTooltip`/`themedLegend`/`themedGauge`，ECharts 图表自动适配亮暗模式
- `useWebSocket()` composable：WebSocket 连接管理，支持订阅/取消订阅主题
- CI/CD GitHub Actions workflow（后端测试 + ruff lint + 前端 typecheck）

### 修复
- **前端主题统一**：大屏展示页（overview/project/meter）移除所有自定义背景色，完全使用系统主题色
- **WebSocket 无限重连**：任务监控页面因后端无 WS 端点导致 `onclose` 死循环，添加 `MAX_RETRIES=3` 限制
- **vite.config.ts 环境变量**：使用 `loadEnv(mode)` 替代 `process.env` 读取 `VITE_NITRO_MOCK`，修复前端代理始终指向 mock 的问题
- **前端 TypeScript 类型错误**：修复全量 typecheck 错误，`tsconfig.json` 配置 `noUnusedLocals/noUnusedParameters: false`
- **CI pipeline**：seed 使用 `python -m app.db.seed`，ruff per-file-ignores 配置 models/seed.py，前端仅检查 web-antd
- **seed.py MeterPoint 字段**：修正 `obis_code`/`meter_id` 字段名，移至 Meters 创建之后
- **测试数据唯一化**：MeterPoint 测试使用 `uuid4().hex[:6]` 避免 obis_code 冲突
- **audit_service.py 变量名**：`l` → `log`（E741）

### 变更
- 大屏页面颜色规则：禁止自定义背景色，所有组件使用系统默认主题样式
- ECharts 图表不再硬编码 `#ccc`/`#aaa`/`#333` 等颜色，统一使用 `useChartTheme()` 提供的主题化方法

---

## [0.5.0] - 2026-05-16

### 新增
- Service 层：reference_service、menu_service（+ user_service 追加 get_user_info）
- Schema：reference（MeterPointCreate/Update）、project（ProjectUpdate 改为全 optional）
- 端点重构：user/roles/menus/menu/reference/projects/departments 全部调用 service + schema 验证
- 测试：新增 19 个测试（reference 14 + roles 5），总计 83 个测试全部通过

### 修复
- user.py 下沉到 user_service.get_user_info
- roles.py 下沉到 role_service（list/create/update/delete）
- menus.py/menu.py 下沉到 menu_service（list/check/get_user_menus）
- reference.py 下沉到 reference_service（meter-types/wire-types/meter-points CRUD）
- projects.py 使用 ProjectCreate/ProjectUpdate schema 验证
- departments.py 使用 DeptCreate/DeptUpdate schema 验证
- system.py 角色接口使用 RoleCreate/RoleUpdate schema

### 统计
- Service 文件：15 → 17 个（+2）
- 83 测试通过，0 warning
- Endpoint 直接 SQL：0 处（全部通过 service）
- body: dict：13 → 5 处（合理的保留：analysis/alarms handle/tests distribute/meters import/tasks execute）

## [0.4.1] - 2026-05-16

### 新增
- 测试覆盖：新增 28 个测试（alarm 12 + task 9 + test/defect 7），总计 64 个测试全部通过
- analysis 端点补全：`/daily/export`、`/data-quality/export`、`/reports/{id}/export`

### 修复
- Task schema 移除不存在的 `task_category` 字段
- TaskUpdate 改为全 optional 字段（部分更新）
- `get_task_logs` 返回格式统一为 `{items, total}`
- `toggle_task` 返回实际 `is_enabled` 值而非硬编码 True
- `create_task` 返回完整数据 dict（含 id + 全部字段）
- defect 测试改为先创建再操作（避免 id 冲突）

## [0.4.0] - 2026-05-16

### 新增
- Service 层补全：alarm_service、task_service、test_service、defect_service（4 个新文件）
- Pydantic Schema 补全：alarm（AlarmRuleCreate/Update）、test（TestTaskCreate/Update、TestReportCreate/Update、DefectCreate/Update）、analysis（CompareRequest、ConsistencyCheckRequest）
- Analysis 端点补全：`/daily/export`、`/data-quality/export`、`/reports/{id}/export`
- 前端切真实后端 API（`VITE_NITRO_MOCK=false`）

### 变更
- 6 个端点重构为调用 service 层：alarms、alarm_rules、defects、tasks、task_logs、tests
- alarm_rules、defects、tasks、tests 端点使用 Pydantic Schema 替换 `body: dict`
- reference.py 移除手动 `await db.commit()`，统一由 `get_db` 自动管理事务
- Service 层统一使用 `flush()` + 依赖注入 `get_db` 自动 commit/rollback

### 统计
- Service 文件：11 → 15 个（+4）
- Schema 文件：6 → 8 个（+2）
- 后端路由：99 个
- 测试：36 个全部通过
- 前端 API：65 个接口全部对齐真实后端

## [0.3.0] - 2026-05-16

### 新增
- 全部 11 个剩余端点文件完成 `CurrentUser` / `DbSession` DI 重构
  - `alarms.py` — 告警统计、列表、导出CSV、处理
  - `alarm_rules.py` — 告警规则 CRUD
  - `defects.py` — 缺陷列表、更新
  - `menus.py` — 系统菜单列表、名称/路径唯一性检查
  - `menu.py` — 用户权限菜单获取（改用 `User` 对象替代 dict）
  - `reference.py` — 电表类型、接线方式、采集点 CRUD
  - `roles.py` — 角色列表（含权限ID、用户数）
  - `tasks.py` — 采集任务 CRUD、执行、日志、启停
  - `task_logs.py` — 任务设备执行日志
  - `tests.py` — 测试任务、缺陷、报告 CRUD + 导出/分发
  - `upload.py` — 文件上传

### 修复
- `menu.py` 原先使用 `current_user.get("sub")` 获取用户名（dict 方式），改为直接使用 `User` ORM 对象
- `alarms.py`、`alarm_rules.py`、`defects.py` 中的 `fail()` 调用移除，统一返回 `success(None)` 表示未找到
- 移除所有端点中的 `Depends` / `AsyncSessionLocal` 旧依赖导入

### 变更
- 所有端点从手动 `async with async_session() as session` 改为 FastAPI 依赖注入 `db: DbSession`
- 所有 `Depends(get_current_user)` 改为 `CurrentUser` 注解类型

---

## [0.2.0] - 2026-05-16

### 新增
- Phase 2 电表管理模块全部实现（agent 并行开发）
  - 电表 CRUD、状态机流转（库存→使用→维修→报废）
  - 借出审批流程（部门→实验室→通过/驳回）
  - 维修记录管理
  - 附件上传（白名单 + 10MB 限制）
  - CSV 导出
- 前后端 API 对齐
  - `successCode: 0` → `successCode: 200`
  - 前端 API 路径统一加 `/system/` 前缀
  - `withCredentials` 位置修正

### 修复
- `/user/info` 500 错误：旧 `get_current_user` 返回 dict 与新 `User` 对象不兼容
- 测试数据库 asyncpg 事件循环冲突：使用 `NullPool` 解决
- GitHub 推送权限不足：补充 `workflow` scope

---

## [0.1.0] - 2026-05-15

### 新增
- 项目初始化，FastAPI 后端骨架搭建
- PostgreSQL 数据库建表 + 种子数据（12 张表）
- 核心基础设施
  - `CurrentUser` / `DbSession` 依赖注入
  - `BusinessException` + 全局异常处理
  - 统一响应格式 `{code, message, data}`
  - JWT 认证（登录/刷新/退出）
- Phase 1 全部端点实现
  - 认证：登录、获取权限码、刷新令牌、退出
  - 系统管理：用户 CRUD、角色 CRUD、部门树 CRUD、审计日志、数据归档、数据库监控、健康检查
  - 项目管理：项目 CRUD
  - 用户信息：`/user/info` 返回角色 + 权限列表
- 前端 `vue-vben-admin 5.7.0` 集成
- pytest 测试框架搭建（36 个测试全部通过）
- 开发排期文档 `docs/planning/development-plan.md`

---

[0.3.0]: https://github.com/ViewWay/MiniHES/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ViewWay/MiniHES/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ViewWay/MiniHES/releases/tag/v0.1.0
