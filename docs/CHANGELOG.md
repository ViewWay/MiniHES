# MiniHES 变更日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

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
