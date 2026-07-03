# MiniHES 开发排期计划

> 项目启动: 2026-05-16 | 预计交付: 2026-08-14 | 总工期: 13 周

---

## 一、项目概况

### 1.1 当前资产盘点

> 最后核对：2026-07-03（对齐实际代码）

| 维度 | 实际状态 | 完成率 |
|------|---------|--------|
| 前端页面 | 60 个 .vue（含 35 个业务页 + 16 个 _core + 9 个 system）+ 53 个 .ts | 95% |
| Mock API | 73 个 mock 端点（backend-mock 保留，前端可切换真实/mock） | - |
| 数据库表 | 32 张表（含 alembic_version）+ 数千行种子数据，8 个 migration | 100% |
| 后端 Model | 31 个 SQLAlchemy 模型（user/meter/meter_point/task/alarm/test/system/project/session） | 100% |
| 后端 Schema | 10 个文件 / 66 个 Pydantic 类 | 95% |
| 后端 Service | 16 个 service 文件（全量 Service 化，仅 system.py 残留 3 处直接 DB） | 95% |
| 后端 Endpoint | 20 个文件 / 105 个路由 | 90%（analysis 9 路由为 mock） |
| 后端测试 | 83 个测试（backend/tests/，CI 通过） | 70% |
| E2E 测试 | 9 个 Playwright spec（tests/e2e/，CI 未运行） | 20% |
| DLMS 协议栈 | ACSE/APDU/OBIS 字节级实现真实；cosem/ 对象模型空壳 | 60% |
| 通信适配器 | TCP cellular + 串口 infrared 真实 IO | 80% |

### 1.2 核心风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Service 层从零开始 | 最大工作量 | 按模块渐进式开发，优先跑通核心链路 |
| Endpoint 需重构 | 现有逻辑在路由层，需下沉到 Service | 新建 service 文件，逐步迁移 |
| 前端 mock 格式与后端真实格式不一致 | 联调效率 | Phase 1 先对齐响应格式 |
| DLMS 私有库接入 | Phase 3 阻塞 | 先用模拟数据，后续替换 |
| 前端 code:0 vs 后端 code:200 | 数据解析失败 | 统一为 `{code, message, data}` |

### 1.3 技术决策（已确认）

- 响应格式：`{code: int, message: str, data: any}`，code 与 HTTP 状态码一致
- 抄读数据存储：PostgreSQL 时序表（`col_meter_reading` + `col_reading_daily`），不用 InfluxDB
- API 文档：FastAPI 自带 `/docs` Swagger UI，代码即文档
- 认证：JWT Bearer Token
- 分层：endpoints → schemas → services → models → core

---

## 二、阶段排期

### 甘特图

```
          5月                    6月                    7月                    8月
W3  W4  W5  W6  │  W1  W2  W3  W4  │  W1  W2  W3  W4  │  W1  W2  W3  W4
─────────────────┼──────────────────┼──────────────────┼─────────────────
[P1■■■■■■■■■■■■■]│                  │                  │
                 │[P2■■■■■■■■■■■■■■]│                  │
                 │                  │[P3■■■■■■■■■■■■■■■■■■■■■]│
                 │                  │         [P4■■■■■■■■■■■■■■]│
                 │                  │                  │[P5■■■■■■■■■■■■■■]
                 │                  │                  │         [P6■■■■■■■■■■■■■■]

■ 开发   □ 联调   ○ 测试
```

### 里程碑

| 里程碑 | 日期 | 交付物 | 前后端联调 | 状态 |
|--------|------|--------|-----------|------|
| M1 | 05/30 | 认证 + 系统管理 + 项目管理 | auth/system/project | ✅ 完成 |
| M2 | 06/13 | 样机 + 借用 + 维修 + 采集点 | devices | ✅ 完成 |
| M3 | 07/04 | 采集任务 + DLMS + 数据入库 | tasks/collector | 🟡 进行中（任务 CRUD + DLMS 核心已完成；调度引擎/cosem 待补） |
| M4 | 07/18 | 分析报表 + 告警 + 大屏 | analysis/alarms | 🟡 部分完成（告警+大屏已完成；analysis 报表待闭环） |
| M5 | 08/01 | 测试报告 + 缺陷 + 全量联调 | 全部模块 | 🟡 部分完成（test/defect 已完成；报告 PDF 导出待实现） |
| M6 | 08/14 | 上线 | - | 📋 待实施 |

---

## 三、Phase 详细排期

### Phase 1: 基础框架 + 认证系统（05/16 - 05/30，2 周）

**目标**: 前端能登录真实后端，调用受保护接口

#### Week 1: 基础设施 + 认证（05/16 - 05/22）

| 日期 | 任务 | 具体工作 | 产出文件 | 验收标准 |
|------|------|---------|---------|---------|
| 05/16 (五) | 配置完善 | `core/config.py` 补全 JWT/Redis/DB/CORS 配置；`.env.example` | config.py, .env.example | `Settings()` 加载无报错 |
| 05/16 (五) | 数据库管理 | `core/database.py` 连接池参数调优（pool_size=20, pool_pre_ping=True） | database.py | 异步连接 PostgreSQL 正常 |
| 05/19 (一) | 统一响应 | `core/response.py` 实现 ok/created/fail 便捷方法 | response.py | 现有 endpoint 迁移到统一格式 |
| 05/19 (一) | 全局异常 | `core/exceptions.py` BusinessException + validation_handler + 404_handler | exceptions.py | 参数校验失败返回标准格式 |
| 05/19 (一) | JWT 安全 | `core/security.py` JWT encode/decode + bcrypt 密码哈希 | security.py | Token 签发验证通过 |
| 05/20 (二) | 依赖注入 | `core/dependencies.py` get_db / get_current_user / require_permissions | dependencies.py | 受保护接口未登录返回 401 |
| 05/20 (二) | 认证 Schema | `schemas/auth.py` LoginRequest / TokenResponse / RefreshRequest | auth.py | Pydantic 验证生效 |
| 05/21 (三) | 认证 Service | `services/auth.py` login(验证密码+签发token) / logout(黑名单) / refresh(续签) | auth_service.py | 三接口逻辑完整 |
| 05/21 (三) | 认证 Endpoint | 重构 `endpoints/auth.py` 调用 service 层 | auth.py | Swagger 可测试登录 |
| 05/22 (四) | 种子数据 | `scripts/seed_users.py` 管理员/操作员/测试角色 | seed_users.py | 预置 admin/admin123 可登录 |
| 05/22 (四) | **联调检查点** | 前端 auth 模块切真实 API | - | 前端登录/登出/刷新 正常 |

#### Week 2: 系统管理 + 项目管理（05/23 - 05/30）

| 日期 | 任务 | 具体工作 | 产出文件 | 验收标准 |
|------|------|---------|---------|---------|
| 05/23 (五) | 系统 Schema | `schemas/system.py` User/Role/Department/Menu/AuditLog 的 CRUD 模型 | system.py | 分页/创建/更新模型完整 |
| 05/23 (五) | 系统 Service | `services/user_service.py` / `services/role_service.py` / `services/dept_service.py` | 3 个 service | CRUD + 权限检查 |
| 05/26 (一) | 系统 Endpoint | 重构 `endpoints/user.py` / `roles.py` / `departments.py` / `menus.py` 调用 service | 4 个 endpoint | 用户/角色/部门/菜单 CRUD |
| 05/26 (一) | 审计日志 | `services/audit_service.py` 操作记录自动写入 | audit_service.py | 关键操作有审计记录 |
| 05/27 (二) | 项目 Schema | `schemas/project.py` 补全 Project CRUD 模型 | project.py | 验证规则完整 |
| 05/27 (二) | 项目 Service | `services/project_service.py` 项目 CRUD + MeterType/WireType 管理 | project_service.py | 项目+基础数据 CRUD |
| 05/28 (三) | 项目 Endpoint | 重构 `endpoints/projects.py` 调用 service | projects.py | 项目管理 API |
| 05/28 (三) | 采集点/类型 | `endpoints/meter_types.py` / `endpoints/wire_types.py` / `endpoints/meter_points.py` | 3 个 endpoint | 基础数据 API |
| 05/29 (四) | 后端测试 | `tests/backend/api/test_auth.py` / `test_system.py` / `test_projects.py` | 3 个测试文件 | 覆盖 CRUD + 异常流 |
| 05/30 (五) | **M1 联调** | 前端 system + project 模块切真实 API | - | auth/system/project 全通 |
| 05/30 (五) | Swagger 导出 | 验证 `/docs` 所有 Phase 1 接口 | - | 接口文档可分享 |

**Phase 1 交付清单**:
- [x] 基础设施层完整（config/database/response/exceptions/security/dependencies）
- [x] 认证系统（login/logout/refresh/codes）
- [x] 系统管理（用户/角色/部门/菜单/审计）
- [x] 项目管理（项目/电表类型/线制类型/采集点）
- [x] 前端 auth/system/project 联调完成
- [x] Phase 1 测试全部通过（83 个测试 CI 绿）
- [x] `/docs` Swagger UI 接口文档可访问

---

### Phase 2: 样机管理（06/02 - 06/13，2 周）

**目标**: 完整的样机生命周期管理

#### 已有基础（可复用）

`endpoints/meters.py` 已有 16 个路由，大部分有基础 SQL 查询逻辑，但：
- 缺 schema 验证（接收 `body: dict`）
- 缺 service 抽象（逻辑直接写在路由里）
- 缺错误处理（返回 `success(None)` 而非 404）
- 缺事务管理

#### Week 1: 样机 CRUD + 状态流转（06/02 - 06/06）

| 日期 | 任务 | 具体工作 | 产出文件 |
|------|------|---------|---------|
| 06/02 (一) | 样机 Schema | `schemas/meter.py` 完善 16 个模型：CreateMeterRequest/UpdateMeterRequest/MeterDetail/MeterListParams/BorrowRequest/BorrowApproval/RepairRequest/AttachmentUpload 等 | meter.py |
| 06/02 (一) | 样机 Service | `services/meter_service.py` CRUD + 状态机校验（库存↔在用↔维修↔报废合法流转检查） | meter_service.py |
| 06/03 (二) | 样机 Endpoint | 重构 `endpoints/meters.py` 调用 service，加 schema 验证 | meters.py |
| 06/03 (二) | 导入导出 | `services/meter_service.py` export_csv（已有）/ import_csv（补全） | meter_service.py |
| 06/04 (三) | 状态历史 | `services/meter_service.py` 状态变更记录 + `endpoints/meters.py` status-history API | meter_service.py |
| 06/04 (三) | 通信参数 | `services/meter_service.py` 通信参数更新（MeterComm） | meter_service.py |
| 06/05 (四) | 借用 Service | `services/borrow_service.py` 申请→部门审批→经理审批→归还 完整流程 | borrow_service.py |
| 06/05 (四) | 借用 Endpoint | 重构 `endpoints/borrows.py` 调用 service | borrows.py |
| 06/06 (五) | 维修 Service | `services/repair_service.py` 维修记录 CRUD + 状态流转 | repair_service.py |
| 06/06 (五) | 维修 Endpoint | 维修相关路由调用 service | meters.py |

#### Week 2: 附件 + 联调 + 测试（06/09 - 06/13）

| 日期 | 任务 | 具体工作 | 产出文件 |
|------|------|---------|---------|
| 06/09 (一) | 文件上传 | `services/upload_service.py` 文件上传（本地存储/MinIO）+ 大小/类型限制 | upload_service.py |
| 06/09 (一) | 附件管理 | `endpoints/upload.py` 重构调用 service | upload.py |
| 06/10 (二) | 采集点配置 | `services/meter_point_service.py` 采集点 CRUD + OBIS 码配置 | meter_point_service.py |
| 06/10 (二) | 采集点 Endpoint | 采集点 API 对接 | meter_points 相关 |
| 06/11 (三) | **联调** | 前端设备管理模块切真实 API（样机列表/详情/创建/编辑/借用/维修/附件） | - |
| 06/12 (四) | 后端测试 | `tests/backend/api/test_meters.py` / `test_borrows.py` / `test_uploads.py` | 3 个测试文件 |
| 06/13 (五) | **M2 联调** | 前端 devices 模块全通 | - |
| 06/13 (五) | Bug 修复 | 联调问题修复 | - |

**Phase 2 交付清单**:
- [ ] 样机 CRUD + 状态流转
- [ ] 借用审批流程（部门→经理→归还）
- [ ] 维修记录管理
- [ ] 文件上传/附件管理
- [ ] 采集点配置
- [ ] 导入导出 CSV
- [ ] 前端 devices 模块联调完成
- [ ] Phase 2 测试全部通过

---

### Phase 3: 采集任务系统（06/16 - 07/04，3 周）

**目标**: 任务调度 + 数据采集 + 数据入库 + 实时监控

#### Week 1: 任务 CRUD + 基础调度（06/16 - 06/20）

| 日期 | 任务 | 具体工作 | 产出文件 |
|------|------|---------|---------|
| 06/16 (一) | 任务 Schema | `schemas/task.py` 完善：TaskCreate/TaskUpdate/TaskDetail/TaskListParams/TaskLogDetail | task.py |
| 06/16 (一) | 任务 Service | `services/task_service.py` CRUD + 启停控制 + 任务绑设备 | task_service.py |
| 06/17 (二) | 任务 Endpoint | 重构 `endpoints/tasks.py` 调用 service，加 schema 验证 | tasks.py |
| 06/17 (二) | 任务日志 | `services/task_log_service.py` 日志查询 + 统计 | task_log_service.py |
| 06/18 (三) | 调度引擎 | `services/scheduler.py` APScheduler 集成（PostgreSQL JobStore），Cron/Interval 触发 | scheduler.py |
| 06/18 (三) | 调度管理 | 任务启停 → APScheduler job 注册/移除，task toggle 对接调度器 | scheduler.py |
| 06/19 (四) | 任务设备关联 | `services/task_service.py` TaskDevice 绑定/解绑 | task_service.py |
| 06/19 (四) | 执行引擎骨架 | `services/collector_service.py` 采集执行入口（先跑通流程，DLMS 后续接入） | collector_service.py |
| 06/20 (五) | 模拟采集 | `services/collector_service.py` 模拟采集流程（生成测试数据写入 col_meter_reading） | collector_service.py |

#### Week 2: 数据入库 + DLMS（06/23 - 06/27）

| 日期 | 任务 | 具体工作 | 产出文件 |
|------|------|---------|---------|
| 06/23 (一) | 数据入库 | `services/reading_service.py` 抄读数据写入 col_meter_reading（批量插入） | reading_service.py |
| 06/23 (一) | 日汇总 | `services/reading_service.py` 定时聚合 → col_reading_daily（min/max/avg/delta） | reading_service.py |
| 06/24 (二) | DLMS 接入 | `dlms/` 接入私有库或完善现有协议栈，替换模拟采集 | dlms/ |
| 06/24 (二) | 适配器连接池 | `adapters/base.py` 连接池管理，复用连接 | adapters/ |
| 06/25 (三) | 采集流程 | 创建任务→选择设备→DLMS抄读→数据解析→入库 全链路 | collector_service.py |
| 06/25 (三) | 异常处理 | 超时/断连/解析失败 → 重试（retry_times）+ 日志记录 | collector_service.py |
| 06/26 (四) | WebSocket | `api/v1/endpoints/ws.py` 采集进度实时推送 | ws.py |
| 06/26 (四) | 前端对接 | 前端 tasks 模块切真实 API | - |
| 06/27 (五) | 任务监控 | `endpoints/tasks.py` 执行中任务状态/进度查询 | tasks.py |

#### Week 3: 联调 + 测试（06/30 - 07/04）

| 日期 | 任务 | 具体工作 | 产出文件 |
|------|------|---------|---------|
| 06/30 (一) | 前端联调 | 采集任务列表/详情/创建/执行/日志 切真实 API | - |
| 07/01 (二) | 数据验证 | 检查 col_meter_reading / col_reading_daily 数据正确性 | - |
| 07/01 (二) | 调度测试 | 定时任务执行、暂停、恢复、取消 全流程 | - |
| 07/02 (三) | 后端测试 | `tests/backend/api/test_tasks.py` / `test_scheduler.py` / `test_collector.py` | 3 个测试文件 |
| 07/03 (四) | **M3 联调** | 前端 tasks/collector 模块全通 | - |
| 07/03 (四) | Bug 修复 | 联调问题修复 | - |
| 07/04 (五) | Buffer | 遗留问题处理 | - |

**Phase 3 交付清单**:
- [ ] 任务 CRUD + 启停控制
- [ ] APScheduler 定时调度
- [ ] 采集执行引擎（DLMS 或模拟）
- [ ] 抄读数据入库（col_meter_reading）
- [ ] 日汇总聚合（col_reading_daily）
- [ ] WebSocket 实时推送
- [ ] 前端 tasks 模块联调完成
- [ ] Phase 3 测试全部通过

---

### Phase 4: 数据分析 + 告警（07/07 - 07/18，2 周）

**目标**: 数据分析报表 + 告警规则引擎

#### Week 1: 数据分析（07/07 - 07/11）

| 日期 | 任务 | 具体工作 | 产出文件 |
|------|------|---------|---------|
| 07/07 (一) | 分析 Schema | `schemas/analysis.py` DailyAnalysis/CompareRequest/ConsistencyResult/DataQuality/Report | analysis.py |
| 07/07 (一) | 每日分析 Service | `services/analysis_service.py` 从 col_reading_daily 读取 → 按日聚合 | analysis_service.py |
| 07/08 (二) | 多表对比 | `services/analysis_service.py` 多电表同时段数据对比 | analysis_service.py |
| 07/08 (二) | 一致性检查 | `services/analysis_service.py` 电能平衡/负荷曲线异常检测 | analysis_service.py |
| 07/09 (三) | 数据质量 | `services/analysis_service.py` 完整性/准确性/及时性/一致性评分 | analysis_service.py |
| 07/09 (三) | 报告管理 | `services/report_service.py` 报告列表/生成/下载 | report_service.py |
| 07/10 (四) | 分析 Endpoint | 重构 `endpoints/analysis.py` 调用 service，读真实数据 | analysis.py |
| 07/10 (四) | 前端联调 | analysis 模块切真实 API | - |
| 07/11 (五) | 大屏数据 | `endpoints/analysis.py` 补充 dashboard 聚合 API（总电表数/在线率/今日电量/告警数） | analysis.py |

#### Week 2: 告警引擎 + 联调（07/14 - 07/18）

| 日期 | 任务 | 具体工作 | 产出文件 |
|------|------|---------|---------|
| 07/14 (一) | 告警 Schema | `schemas/alarm.py` AlarmRuleCreate/AlarmRuleUpdate/AlarmRecordDetail | alarm.py |
| 07/14 (一) | 告警 Service | `services/alarm_service.py` 规则 CRUD + 触发检查 | alarm_service.py |
| 07/15 (二) | 告警引擎 | `services/alarm_engine.py` 定时扫描：阈值/趋势/离线 三种规则匹配 | alarm_engine.py |
| 07/15 (二) | 告警通知 | 告警触发 → 记录生成 → WebSocket 推送 | alarm_engine.py |
| 07/16 (三) | 告警 Endpoint | 重构 `endpoints/alarms.py` + `endpoints/alarm_rules.py` | 2 个 endpoint |
| 07/16 (三) | 前端联调 | alarms 模块切真实 API | - |
| 07/17 (四) | 后端测试 | `tests/backend/api/test_analysis.py` / `test_alarms.py` | 2 个测试文件 |
| 07/18 (五) | **M4 联调** | analysis + alarms 全通 | - |
| 07/18 (五) | Bug 修复 | 联调问题修复 | - |

**Phase 4 交付清单**:
- [ ] 每日电量/需量/功率分析
- [ ] 多表数据对比
- [ ] 数据一致性检查
- [ ] 数据质量评分
- [ ] 告警规则管理
- [ ] 告警引擎（阈值/趋势/离线）
- [ ] 大屏聚合数据 API
- [ ] 前端 analysis + alarms 联调完成
- [ ] Phase 4 测试全部通过

---

### Phase 5: 测试报告 + 缺陷管理 + 全量联调（07/21 - 08/01，2 周）

**目标**: 完整闭环，全部前端切真实 API

#### Week 1: 测试报告 + 缺陷（07/21 - 07/25）

| 日期 | 任务 | 具体工作 | 产出文件 |
|------|------|---------|---------|
| 07/21 (一) | 测试 Schema | `schemas/test.py` TestTaskCreate/TestTaskDetail/DefectCreate/DefectDetail | test.py |
| 07/21 (一) | 测试 Service | `services/test_service.py` 测试任务 CRUD + 状态流转 | test_service.py |
| 07/22 (二) | 报告 Service | `services/report_service.py` 报告生成（PDF/Excel 导出） | report_service.py |
| 07/22 (二) | 测试 Endpoint | 重构 `endpoints/tests.py` 调用 service | tests.py |
| 07/23 (三) | 缺陷 Service | `services/defect_service.py` 缺陷 CRUD + 状态流转（新建→处理→验证→关闭） | defect_service.py |
| 07/23 (三) | 缺陷 Endpoint | 重构 `endpoints/defects.py` 调用 service | defects.py |
| 07/24 (四) | 前端联调 | test/defect 模块切真实 API | - |
| 07/25 (五) | 后端测试 | `tests/backend/api/test_tests.py` / `test_defects.py` | 2 个测试文件 |

#### Week 2: 全量联调 + 收尾（07/28 - 08/01）

| 日期 | 任务 | 具体工作 | 产出文件 |
|------|------|---------|---------|
| 07/28 (一) | 全量联调 | 所有前端模块确认使用真实 API，移除 mock 依赖 | - |
| 07/28 (一) | 格式对齐 | 确认前端 code:0 已全部替换为标准 code:200 格式 | - |
| 07/29 (二) | 边界测试 | 空数据/大数据量/并发/异常参数 边界场景测试 | - |
| 07/29 (二) | 集成测试 | `tests/backend/integration/` 全链路集成测试 | integration/ |
| 07/30 (三) | Docker | `docker-compose.yml` 全服务编排（FastAPI + PostgreSQL + Redis） | docker-compose.yml |
| 07/30 (三) | 部署文档 | `docs/deployment.md` 部署指南 | deployment.md |
| 07/31 (四) | **M5 全量联调** | 全部模块真实 API 可用 | - |
| 07/31 (四) | 回归测试 | 已完成模块回归验证 | - |
| 08/01 (五) | Buffer | 遗留问题处理 | - |

**Phase 5 交付清单**:
- [ ] 测试任务 CRUD + 报告生成
- [ ] 缺陷 CRUD + 状态流转
- [ ] 前端全部模块切真实 API
- [ ] Mock 服务移除
- [ ] Docker Compose 一键部署
- [ ] 部署文档
- [ ] 全量集成测试通过

---

### Phase 6: 非功能性需求 + 上线（08/04 - 08/14，2 周）

**目标**: 打磨质量，交付上线

#### Week 1: 非功能性需求（08/04 - 08/08）

| 日期 | 任务 | 具体工作 |
|------|------|---------|
| 08/04 (一) | 性能优化 | 数据库查询优化（N+1 检查）、索引添加、大列表虚拟滚动 |
| 08/04 (一) | 前端打磨 | 骨架屏 loading、防抖节流、懒加载 |
| 08/05 (二) | 代码清理 | 清除 console.log / debugger、dead code、未使用依赖 |
| 08/05 (二) | Lint | ruff format + ruff check 全量修复 |
| 08/06 (三) | 产品体验 | 多浏览器真机体验（Chrome/Firefox/Edge），记录 todolist |
| 08/06 (三) | 代码 Review | 6 维度审查（正确性/安全/性能/可维护/架构/测试） |
| 08/07 (四) | 视觉走查 | 像素级还原检查、响应式适配 |
| 08/07 (四) | 安全检查 | XSS/SQL注入/CSRF 防护、密钥安全、输入验证 |
| 08/08 (五) | 提测 | 转测通知（PRD/接口/测试用例/已知问题） |

#### Week 2: 测试 + 上线（08/11 - 08/14）

| 日期 | 任务 | 具体工作 |
|------|------|---------|
| 08/11 (一) | QA 测试 | QA 按测试用例全量测试 |
| 08/11 (一) | Bug 修复 | P0/P1 Bug 限时修复 |
| 08/12 (二) | Bug 修复 | P2 Bug 修复 + 回归测试 |
| 08/12 (二) | 回归 | 已修复 Bug 回归验证 |
| 08/13 (三) | 预发布 | staging 环境部署验证 |
| 08/13 (三) | 上线准备 | 发布 checklist、回退方案、监控配置 |
| 08/14 (四) | **M6 上线** | 先发后端 → 再发前端 → 监控观察 |
| 08/14 (四) | 复盘 | 上线总结 + 后续迭代规划 |

**Phase 6 交付清单**:
- [ ] 性能优化完成（Lighthouse ≥ 80）
- [ ] 代码 Review 无 Critical 问题
- [ ] QA Bug 全部处理
- [ ] 多浏览器兼容验证
- [ ] 生产环境部署成功
- [ ] 监控告警配置完成

---

## 四、资源分配

### 后端开发工作量统计

| 模块 | Service 文件 | Schema 补全 | Endpoint 重构 | 测试文件 | 预估工时 |
|------|-------------|------------|--------------|---------|---------|
| 认证 | 1 | 1 | 1 | 1 | 4d |
| 系统管理 | 3 | 1 | 4 | 1 | 5d |
| 项目管理 | 1 | 1 | 3 | 1 | 3d |
| 样机管理 | 3 | 1 | 1 | 3 | 7d |
| 采集任务 | 4 | 1 | 1 | 3 | 8d |
| 数据分析 | 2 | 1 | 1 | 2 | 5d |
| 告警 | 2 | 1 | 2 | 1 | 4d |
| 测试缺陷 | 2 | 1 | 2 | 2 | 4d |
| 基础设施 | - | - | - | - | 3d |
| **合计** | **18** | **8** | **15** | **14** | **43d ≈ 9 周** |

### 前端联调工作量统计

| 模块 | Mock API 数量 | 需对齐的接口 | 预估工时 |
|------|-------------|------------|---------|
| auth | 4 | login/logout/refresh | 0.5d |
| system | 12 | users/roles/dept/menu/audit | 1.5d |
| project | 5 | projects/meter-types/wire-types | 1d |
| devices | 16 | meters/borrows/repairs/attachments | 2d |
| tasks | 8 | tasks/logs/execute/toggle | 2d |
| analysis | 6 | daily/compare/consistency/quality/reports | 1.5d |
| alarms | 5 | alarms/rules/stats | 1d |
| tests | 9 | tests/reports/defects | 1.5d |
| **合计** | **65** | **65** | **11d ≈ 2 周** |

---

## 五、每日站会节奏

### 站会问题（每日 10 分钟）

1. 昨天完成了什么？
2. 今天计划做什么？
3. 有什么阻塞？

### 每周检查点

| 时间 | 事项 |
|------|------|
| 每周五 16:00 | 阶段进度 Review，更新本文档完成度 |
| 每个 M 里程碑 | 演示 Demo，确认下一阶段计划 |
| 风险触发时 | 即时同步，调整排期 |

---

## 六、质量门禁

### 每个 Phase 合并前必须满足

| 门禁 | 标准 |
|------|------|
| 代码质量 | ruff check 0 error |
| 测试覆盖 | 新增代码覆盖率 ≥ 70% |
| 接口文档 | `/docs` Swagger UI 可访问 |
| 联调验证 | 对应前端模块切真实 API 可用 |
| 代码 Review | 无 Critical 级别问题 |

### 上线门禁

| 门禁 | 标准 |
|------|------|
| 全量测试 | pytest + vitest + E2E 全通过 |
| 性能 | Lighthouse Performance ≥ 80 |
| 安全 | 无 OWASP Top 10 漏洞 |
| 兼容 | Chrome/Firefox/Edge 最新版 |
| 部署 | Docker Compose 一键部署成功 |
