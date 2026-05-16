# MiniHES 实施计划

**目标：** 云端智能电表抄表系统 - DLMS/COSEM 协议栈 + 多通信方式适配

**架构：** vue-vben-admin 前端 + FastAPI 后端 + PostgreSQL + Redis + InfluxDB

**技术栈：** Vue 3, TypeScript, Python 3.12, Ant Design Vue, uv, pnpm

---

## 项目状态

### ✅ 已完成
- [x] 项目结构初始化
- [x] 前端基础框架 (vue-vben-admin)
- [x] 前端全部页面开发 (设备/任务/分析/大屏/测试/系统管理)
- [x] 前端 Mock API 服务
- [x] 后端基础框架 (FastAPI)
- [x] 后端开发环境搭建 (uv + Python 3.12, 所有依赖安装)

### 🚧 进行中
- [ ] 后端 API 开发

### 📋 待实施

---

## 模块计划

### Phase 1: 后端基础框架 + 认证系统
- [ ] FastAPI 项目结构完善
- [ ] PostgreSQL 数据库初始化 (Alembic 迁移)
- [ ] JWT 认证 (python-jose + passlib)
- [ ] RBAC 权限系统
- [ ] 用户/角色/部门 CRUD API

### Phase 2: 样机管理
- [ ] 样机档案 CRUD API
- [ ] 状态流转服务
- [ ] 借用审批工作流
- [ ] 维修记录管理
- [ ] 附件上传

### Phase 3: 采集任务系统
- [ ] APScheduler 定时调度
- [ ] DLMS/Modbus 协议适配器
- [ ] InfluxDB 数据写入
- [ ] 任务监控和日志
- [ ] 数据质量统计

### Phase 4: 数据分析 + 告警
- [ ] 每日分析报告生成
- [ ] 对比分析
- [ ] 数据一致性检查
- [ ] 告警规则引擎
- [ ] WebSocket 实时推送

### Phase 5: 大屏展示 + 测试报告
- [ ] 项目概览大屏 API
- [ ] 项目详情大屏 API
- [ ] 单表监控大屏 API
- [ ] 测试任务管理
- [ ] 测试报告生成
- [ ] 缺陷跟踪

---

## 开发命令

```bash
# 后端
cd backend
uv run uvicorn main:app --reload    # 启动开发服务
uv run pytest                        # 运行测试
uv run alembic revision --autogenerate -m "xxx"  # 生成迁移
uv run alembic upgrade head          # 执行迁移

# 前端
cd frontend
pnpm dev:antd                        # 启动前端
```
