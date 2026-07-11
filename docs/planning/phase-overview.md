# MiniHES 实施计划

**目标：** 云端智能电表抄表系统 - DLMS/COSEM 协议栈 + 多通信方式适配

**架构：** vue-vben-admin 前端 + FastAPI 后端 + PostgreSQL（业务+时序）+ Redis

**技术栈：** Vue 3, TypeScript, Python 3.12, Ant Design Vue, uv, pnpm

> 本文档按实际代码进度同步。最后核对日期：2026-07-03。

---

## 项目状态

### ✅ 已完成
- [x] 项目结构初始化
- [x] 前端基础框架 (vue-vben-admin)
- [x] 前端全部页面开发 (设备/任务/分析/大屏/测试/系统管理)
- [x] 前端 Mock API 服务 (73 个端点)
- [x] 后端基础框架 (FastAPI)
- [x] 后端开发环境搭建 (uv + Python 3.12, 所有依赖安装)
- [x] 后端 API 开发（105 路由 / 16 service / 31 模型 / 66 schema）
- [x] 数据库迁移体系（8 个 Alembic migration）
- [x] JWT 认证 + bcrypt 密码哈希
- [x] RBAC 数据模型（User/Role/Permission 五表）
- [x] RBAC 接口级强制（`require_permission` 依赖 + 15 router 批量挂载 + super 豁免）
- [x] 大屏亮/暗主题适配
- [x] CI/CD（GitHub Actions: ruff + pytest + vue-tsc）
- [x] 后端测试（90 个，CI 通过）

### 🚧 部分完成 / 已知待办
- [ ] 分析模块闭环（`analysis.py` 9 个路由当前返回硬编码 mock，日报/导出"待实现"）
- [ ] DLMS `cosem/` 对象模型层（ACSE/APDU/OBIS 字节级实现已就绪，cosem 目录仅空 docstring）
- [ ] 采集调度引擎（`scheduler.py`/`collector.py` 执行引擎未见，任务 CRUD 已完成）
- [ ] 前端 `dashboard/analytics/` 下 5 个子图组件业务化（当前是 vben 模板 demo）

---

## 模块计划与实际进度

### Phase 1: 后端基础框架 + 认证系统 ✅
- [x] FastAPI 项目结构完善
- [x] PostgreSQL 数据库初始化 (Alembic 迁移，8 个版本)
- [x] JWT 认证 (python-jose + passlib，login/refresh/logout/codes)
- [x] RBAC 权限系统（数据模型层完整）
- [x] 用户/角色/部门 CRUD API（user/role/dept/menu_service）

### Phase 2: 样机管理 ✅
- [x] 样机档案 CRUD API（meter_service 13 方法）
- [x] 状态流转服务（MeterStatusHistory）
- [x] 借用管理（borrow_service 5 方法）
- [x] 维修记录管理（repair_service 4 方法）
- [x] 附件上传（upload_service 5 方法）

### Phase 3: 采集任务系统 🟡
- [x] 任务 CRUD（task_service 12 方法）
- [x] 采集点配置（reference_service 9 方法，OBIS 码）
- [x] 数据入库（PostgreSQL 时序表 `col_meter_reading` + `col_reading_daily_summary`，**已弃用 InfluxDB**）
- [x] DLMS 协议栈核心（ACSE/APDU/OBIS 字节级实现真实可用）
- [x] 通信适配器（TCP cellular + 串口 infrared，真实 IO）
- [ ] APScheduler 调度引擎接入（JobStore=PostgreSQL）
- [ ] DLMS `cosem/` 对象模型层补全
- [x] 任务监控和日志（TaskLog + WebSocket，前端已做重连限制）

### Phase 4: 数据分析 + 告警 🟡
- [ ] 每日分析报告生成（`analysis.py` 9 路由为 mock 占位）
- [ ] 对比分析 / 数据一致性检查（占位）
- [x] 告警规则引擎（alarm_service 11 方法，AlarmRule CRUD）
- [x] 告警查询/处理/统计（alarms/alarm_rules 端点）
- [x] WebSocket 实时推送通道（前端 useWebSocket 已封装）

### Phase 5: 大屏展示 + 测试报告 ✅（基本完成）
- [x] 项目概览大屏（screen/overview.vue）
- [x] 项目详情大屏（screen/project.vue）
- [x] 单表监控大屏（screen/meter.vue，含 gauge + WebSocket）
- [x] 3 个大屏亮色/暗色主题自适应（useChartTheme）
- [x] 测试任务管理（test_service 8 方法）
- [x] 缺陷跟踪（defect_service 4 方法）
- [ ] 测试报告 PDF 导出 / 邮件分发（待实现）

---

## 关键技术决策（实际落地版本）

| 决策点 | 结论 | 说明 |
|--------|------|------|
| 时序数据存储 | **PostgreSQL 时序表** | 早期选型 InfluxDB **已弃用**，改用 `col_meter_reading` + `col_reading_daily_summary` |
| 响应格式 | 标准 HTTP 状态码 + 业务码 | `{code, message, data}`，code 与 HTTP 状态码一致 |
| API 文档 | FastAPI `/docs` Swagger UI | 代码即文档，不维护独立 API 文档 |
| 认证 | JWT Bearer Token | HS256 + bcrypt |
| 分层架构 | endpoints → schemas → services → models → core | 全量 Service 化（仅 system.py 残留 3 处直接 DB 操作） |

---

## 开发命令

```bash
# 后端
cd backend
uv sync                            # 安装依赖
uv run uvicorn main:app --reload   # 启动开发服务
uv run pytest                      # 运行测试（83 个，在 backend/tests/）
uv run alembic upgrade head        # 执行迁移
uv run python -m app.db.seed       # 导入种子数据

# 前端
cd frontend
pnpm install
pnpm dev:antd                      # 启动前端
pnpm --filter @vben/web-antd run typecheck  # 类型检查
```
