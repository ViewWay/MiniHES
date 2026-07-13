"""采集服务子包 — 配置注册表 + 类型定义 + 模板服务。

模块结构：
    types.py         — DeviceType / TaskCategory 枚举 + 有效组合矩阵
    registry.py      — ConfigRegistry 配置注册表（启动时注册所有组合）
    bootstrap.py     — 注册初始化（调用 registry.register_all）
    template_service.py — OBIS 模板 CRUD（Phase 4）
"""
