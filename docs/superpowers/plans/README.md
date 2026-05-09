# MiniHES 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 云端智能电表抄表系统 - DLMS/COSEM 协议栈 + 多通信方式适配

**架构：** Nuxt 3 前端 + FastAPI 后端 + PostgreSQL/MongoDB 数据库

**技术栈：** Vue 3, TypeScript, Python, Tailwind CSS, Nuxt UI

---

## 项目状态

### ✅ 已完成
- [x] 项目结构初始化
- [x] 前端基础框架 (Nuxt 3)
- [x] 后端基础框架 (FastAPI)
- [x] UI/UX Skills 配置
- [x] 工作流命令配置

### 🚧 进行中

### 📋 待实施

---

## 模块计划

### Phase 1: DLMS 协议栈
- [ ] APDU 编解码
- [ ] ACSE 连接管理
- [ ] COSEM 接口对象
- [ ] OBIS 码注册表

### Phase 2: 通信适配层
- [ ] 红外适配器
- [ ] 4G/5G/NB-IoT 适配器
- [ ] M-Bus 适配器
- [ ] LoRaWAN 适配器
- [ ] G3-PLC 适配器

### Phase 3: 数据采集服务
- [ ] 定时调度器
- [ ] 执行引擎
- [ ] 设备管理器
- [ ] 数据解析器

### Phase 4: 前端界面
- [ ] 设备管理页面
- [ ] 实时监控面板
- [ ] 数据分析报表

---

## 执行说明

使用 `/feature <功能描述>` 开始新功能开发
使用 `/ui <页面描述>` 设计新界面
使用 `/review` 进行代码审查
