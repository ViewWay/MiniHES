# MiniHES 数据库表结构文档

> PostgreSQL 数据库，共 32 张表，按模块分为 6 组。

---

## 目录

- [系统默认登录账号](#系统默认登录账号)
- [1. 系统管理模块（sys_）](#1-系统管理模块sys_)
- [2. 设备管理模块（dev_）](#2-设备管理模块dev_)
- [3. 数据采集模块（col_）](#3-数据采集模块col_)
- [4. 告警管理模块（sys_alarm_）](#4-告警管理模块sys_alarm_)
- [5. 实验室管理模块（lab_）](#5-实验室管理模块lab_)
- [6. 数据归档模块（sys_data_）](#6-数据归档模块sys_data_)
- [ER 关系概览](#er-关系概览)

---

## 系统默认登录账号

Seed 数据预置 3 个用户，所有密码统一为 `123456`。

| 用户名 | 密码 | 姓名 | 角色 | 部门 | 邮箱 |
|--------|------|------|------|------|------|
| admin | 123456 | 超级管理员 | 超级管理员 + 工程师 | 总部 | admin@minihes.com |
| engineer | 123456 | 张工程师 | 工程师 | 研发部 | engineer@minihes.com |
| tester | 123456 | 李测试员 | 测试员 | 测试部 | tester@minihes.com |

**角色权限矩阵：**

| 权限菜单 | 超级管理员(super) | 工程师(admin) | 测试员(user) |
|---------|:--:|:--:|:--:|
| 仪表盘 | ✅ | ✅ | ✅ |
| 设备管理 | ✅ | ✅ | ✅ |
| 项目管理 | ✅ | ✅ | |
| 采集任务 | ✅ | ✅ | |
| 告警管理 | ✅ | ✅ | |
| 数据分析 | ✅ | ✅ | |
| 系统管理 | ✅ | ✅ | |

---

## 1. 系统管理模块（sys_）

### sys_user — 用户表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| username | varchar(50) | | | 登录用户名 |
| password_hash | varchar(255) | | | bcrypt 密码哈希 |
| name | varchar(50) | | | 显示姓名 |
| email | varchar(100) | | | 邮箱 |
| phone | varchar(20) | | | 手机号 |
| avatar | varchar(500) | | `''` | 头像 URL |
| department_id | integer | ✓ | | 所属部门 → sys_user.id |
| is_active | boolean | | `true` | 是否启用 |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

### sys_role — 角色表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| name | varchar(50) | | | 角色名称 |
| code | varchar(50) | | | 角色编码 (UNIQUE) |
| description | text | | `''` | |
| sort_order | integer | | `0` | 排序 |
| status | varchar(20) | | `''` | |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

### sys_user_role — 用户角色关联表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| user_id | integer | | | → sys_user.id CASCADE |
| role_id | integer | | | → sys_role.id CASCADE |

**UNIQUE:** `(user_id, role_id)`

### sys_permission — 权限表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| name | varchar(100) | | | 权限名称 |
| code | varchar(100) | | | 权限编码 (UNIQUE) |
| type | varchar(20) | | `''` | menu/button/api |
| parent_id | integer | ✓ | | 父级 → sys_permission.id SET NULL |
| path | varchar(200) | | `''` | 路由路径 |
| icon | varchar(100) | | `''` | 图标 |
| sort_order | integer | | `0` | |
| status | varchar(20) | | `''` | |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

### sys_role_permission — 角色权限关联表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| role_id | integer | | | → sys_role.id CASCADE |
| permission_id | integer | | | → sys_permission.id CASCADE |

**UNIQUE:** `(role_id, permission_id)`

### sys_department — 部门表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| name | varchar(100) | | | 部门名称 |
| code | varchar(50) | | | 部门编码 (UNIQUE) |
| parent_id | integer | ✓ | | 父级 → sys_department.id |
| sort_order | integer | | `0` | |
| leader | varchar(50) | | `''` | 负责人 |
| status | varchar(20) | | `''` | |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

### sys_audit_log — 操作审计日志表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| user_id | integer | | | 操作用户 → sys_user.id |
| username | varchar(50) | | | 用户名快照 |
| operation_type | varchar(50) | | | LOGIN/CREATE/UPDATE/DELETE |
| resource_type | varchar(50) | | | 资源类型 (meter/task/system…) |
| resource_id | integer | | `0` | 资源 ID |
| old_values | json | ✓ | | 变更前值 |
| new_values | json | ✓ | | 变更后值 |
| ip_address | varchar(50) | | | 客户端 IP |
| user_agent | varchar(500) | | | 浏览器标识 |
| created_at | timestamptz | | `now()` | INDEX |

---

## 2. 设备管理模块（dev_）

### dev_project — 项目表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| name | varchar(200) | | | 项目名称 (UNIQUE) |
| description | text | | `''` | |
| test_lead_id | integer | ✓ | | 测试负责人 → sys_user.id |
| dev_lead_id | integer | ✓ | | 开发负责人 → sys_user.id |
| start_date | date | ✓ | | 开始日期 |
| end_date | date | ✓ | | 结束日期 |
| status | varchar(20) | | `''` | planning/active/testing/completed |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

### dev_meter_type — 电表类型表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| name | varchar(100) | | | 类型名称 |
| code | varchar(50) | | | 类型编码 (UNIQUE) |
| description | text | | `''` | |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

Seed 数据: `single_phase`(单相电能表), `three_phase_4w`(三相四线), `three_phase_3w`(三相三线)

### dev_wire_type — 接线方式表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| name | varchar(100) | | | 方式名称 |
| code | varchar(50) | | | 方式编码 (UNIQUE) |
| description | text | | `''` | |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

### dev_meter — 电表设备表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| serial_number | varchar(50) | | | 表号 (UNIQUE, INDEX) |
| meter_name | varchar(100) | | | 设备名称 |
| meter_type_id | integer | ✓ | | → dev_meter_type.id SET NULL |
| project_id | integer | ✓ | | → dev_project.id SET NULL INDEX |
| protocol | varchar(20) | | `'DLMS'` | 通信协议 |
| line_type | varchar(20) | | `'single_phase'` | 接线方式 |
| manufacturer | varchar(100) | | `''` | 制造商 |
| model | varchar(100) | | `''` | 型号 |
| firmware_version | varchar(50) | | `''` | 固件版本 |
| hardware_version | varchar(50) | | `''` | 硬件版本 |
| frame_number | varchar(50) | | `''` | 表架号 |
| location | varchar(200) | | `''` | 存放位置 |
| current_status | varchar(20) | `'in_stock'` | 设备状态 INDEX |
| factory_date | date | ✓ | | 出厂日期 |
| purchase_date | date | ✓ | | 采购日期 |
| warranty_date | date | ✓ | | 质保日期 |
| notes | text | | `''` | 备注 |
| created_by | integer | ✓ | | → sys_user.id SET NULL |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

**状态枚举:** in_stock / in_use / online / offline / repairing / returned

### dev_meter_point — 测量点定义表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id CASCADE |
| obis_code | varchar(30) | | | OBIS 码 |
| class_id | integer | | `1` | COSEM 类 ID |
| attribute_id | integer | | `2` | 属性 ID |
| point_name | varchar(100) | | | 测量点名称 |
| module | varchar(50) | | `''` | 模块分类 (Energy/Instantaneous/Clock…) |
| point_type | varchar(50) | `'register'` | register/profile/attribute |
| data_type | varchar(20) | `'numeric'` | numeric/int/string |
| unit | varchar(20) | | `''` | 单位 (kWh/V/A/W/Hz…) |
| scaler | integer | | `0` | 缩放因子 |
| is_collectible | boolean | | `true` | 是否可采集 |
| description | text | | `''` | |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

**UNIQUE:** `(meter_id, obis_code, attribute_id)`

> 同一 OBIS 码可对应多个 attribute_id（如 Clock 的 time/timezone/status 各是不同属性）。

### dev_meter_comm — 电表通信配置表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id CASCADE (UNIQUE) |
| protocol | varchar(20) | | `'DLMS'` | 协议 |
| connection_type | varchar(20) | | `'tcp'` | tcp/serial |
| host | varchar(255) | | `''` | IP 地址或串口路径 |
| port | integer | | `4059` | 端口号 |
| device_address | varchar(50) | | `''` | 设备地址 |
| baud_rate | integer | | `9600` | 波特率 |
| parity | varchar(10) | | `'none'` | 校验 |
| data_bits | integer | | `8` | 数据位 |
| stop_bits | integer | | `1` | 停止位 |
| auth_config | json | ✓ | | 认证配置 |
| timeout | integer | | `30` | 超时(秒) |
| retry_times | integer | | `3` | 重试次数 |
| is_enabled | boolean | | `true` | |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

与 dev_meter 一对一关系。

### dev_meter_snapshot — 电表实时快照表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id CASCADE (UNIQUE) |
| online_status | boolean | | `false` | 在线状态 |
| last_comm_time | timestamptz | ✓ | | 最后通信时间 |
| signal_strength | integer | ✓ | | 信号强度 (dBm) |
| firmware_version | varchar(50) | | `''` | 当前固件版本 |
| error_code | varchar(20) | | `''` | 错误码 |
| stack_usage | integer | ✓ | | 栈使用量 |
| eeprom_write_count | integer | ✓ | | EEPROM 写入次数 |
| last_data_time | timestamptz | ✓ | | 最后数据时间 |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

与 dev_meter 一对一关系。

### dev_meter_status — 电表状态变更记录表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id CASCADE INDEX |
| old_status | varchar(20) | | `''` | 原状态 |
| new_status | varchar(20) | | | 新状态 |
| reason | varchar(200) | | `''` | 变更原因 |
| changed_by | integer | ✓ | | 操作人 → sys_user.id SET NULL |
| created_at | timestamptz | | `now()` | |

### dev_meter_borrow — 电表借还记录表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id RESTRICT INDEX |
| borrower_id | integer | ✓ | | 借用人 → sys_user.id SET NULL |
| borrow_reason | varchar(200) | | | 借用原因 |
| expected_return_date | date | ✓ | | 预计归还日期 |
| actual_return_date | date | ✓ | | 实际归还日期 |
| dept_approver_id | integer | ✓ | | 部门审批人 → sys_user.id SET NULL |
| lab_approver_id | integer | ✓ | | 实验室审批人 → sys_user.id SET NULL |
| approval_status | varchar(20) | `'pending_department'` | 审批状态 |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

**审批状态:** pending_department → approved_department → approved_lab → returned

### dev_meter_repair — 电表维修记录表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id RESTRICT INDEX |
| description | text | | | 故障描述 |
| cost | numeric(12,2) | | `0` | 维修费用 |
| status | varchar(20) | `'in_progress'` | in_progress/completed |
| repaired_by | integer | ✓ | | 维修人 → sys_user.id SET NULL |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

### dev_meter_attachment — 电表附件表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id CASCADE INDEX |
| filename | varchar(200) | | | 文件名 |
| file_path | varchar(500) | | | 存储路径 |
| size | integer | | `0` | 文件大小(bytes) |
| uploaded_by | integer | ✓ | | → sys_user.id SET NULL |
| created_at | timestamptz | | `now()` | |

---

## 3. 数据采集模块（col_）

### col_task — 采集任务表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| task_name | varchar(100) | | | 任务名称 |
| task_type | varchar(20) | | | cron/interval/once |
| schedule_config | json | | | 调度配置 `{"cron":"0 8 * * *"}` |
| execution_content | json | | | 执行内容 |
| filter_config | json | | | 过滤配置 |
| priority | integer | | `0` | 优先级(1最高) |
| retry_times | integer | | `0` | 重试次数 |
| timeout | integer | | `30` | 超时(秒) |
| is_enabled | boolean | | `false` | |
| last_execute_time | timestamptz | ✓ | | 上次执行时间 |
| next_execute_time | timestamptz | ✓ | | 下次执行时间 INDEX |
| created_by | integer | ✓ | | → sys_user.id SET NULL |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

**INDEX:** `(is_enabled, next_execute_time)` — 调度器查询优化

### col_task_log — 任务执行日志表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| task_id | integer | | | → col_task.id CASCADE |
| start_time | timestamptz | | | 开始时间 |
| end_time | timestamptz | ✓ | | 结束时间 |
| duration_ms | integer | | `0` | 耗时(ms) |
| status | varchar(20) | | | running/completed/failed |
| total_devices | integer | | `0` | 总设备数 |
| success_devices | integer | | `0` | 成功设备数 |
| failed_devices | integer | | `0` | 失败设备数 |
| error_message | text | ✓ | | 错误信息 |
| created_at | timestamptz | | `now()` | |

### col_task_device — 任务设备执行明细表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| log_id | integer | | | → col_task_log.id CASCADE |
| task_id | integer | | | → col_task.id CASCADE |
| meter_id | integer | | | → dev_meter.id RESTRICT |
| status | varchar(20) | | | success/failed/timeout |
| retry_count | integer | | `0` | 重试次数 |
| error_code | varchar(50) | | `''` | 错误码 |
| error_message | text | ✓ | | 错误信息 |
| start_time | timestamptz | ✓ | | 开始时间 |
| end_time | timestamptz | ✓ | | 结束时间 |
| duration_ms | integer | | `0` | 耗时(ms) |
| data_count | integer | | `0` | 采集数据条数 |
| created_at | timestamptz | | `now()` | |

### col_session — 采集会话表（PG-MongoDB 桥梁）

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id RESTRICT |
| project_id | integer | ✓ | | → dev_project.id SET NULL |
| task_id | integer | ✓ | | → col_task.id SET NULL |
| mongo_db | varchar(200) | | `''` | MongoDB 数据库名 |
| mongo_collection | varchar(200) | | `''` | MongoDB 集合名 |
| mongo_doc_id | varchar(100) | | `''` | MongoDB 文档 ID |
| source | varchar(20) | | `'auto'` | auto/manual/import |
| source_file | varchar(500) | | `''` | 来源文件 |
| started_at | timestamptz | ✓ | | 开始时间 |
| finished_at | timestamptz | ✓ | | 结束时间 |
| duration_ms | integer | | `0` | 耗时(ms) |
| status | varchar(20) | `'pending'` | pending/running/completed/failed INDEX |
| total_read | integer | | `0` | 总读取数 |
| total_success | integer | | `0` | 成功数 |
| total_failed | integer | | `0` | 失败数 |
| sheet_count | integer | | `0` | Sheet 数量 |
| connection_type | varchar(20) | | `''` | HDLC/TCP/WPDU/FEP |
| communication | varchar(20) | | `''` | 通信方式 (4G/NB-IoT/…) |
| meter_ip | varchar(50) | | `''` | 电表 IP |
| ping_status | boolean | | `false` | Ping 是否通 |
| error_summary | text | | `''` | 错误摘要 |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

**INDEX:** `(meter_id, started_at)`, `(project_id, started_at)`

### col_meter_reading — 抄表读数记录表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id RESTRICT |
| point_id | integer | | | → dev_meter_point.id RESTRICT |
| task_id | integer | ✓ | | → col_task.id SET NULL |
| reading_value | numeric(18,6) | | | 读数值 |
| reading_time | timestamptz | | | 读取时间 INDEX |
| quality | varchar(20) | | `'good'` | good/suspect/bad |
| source | varchar(20) | | `'auto'` | auto/manual |
| created_at | timestamptz | | `now()` | |

**INDEX:** `(meter_id, point_id, reading_time)` — 查询优化

### col_reading_daily — 日统计汇总表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id RESTRICT |
| point_id | integer | | | → dev_meter_point.id RESTRICT |
| stat_date | date | | INDEX | 统计日期 |
| min_value | numeric(18,6) | | | 最小值 |
| max_value | numeric(18,6) | | | 最大值 |
| avg_value | numeric(18,6) | | | 平均值 |
| first_value | numeric(18,6) | | | 首次值 |
| last_value | numeric(18,6) | | | 末次值 |
| reading_count | integer | | `0` | 读数条数 |
| delta | numeric(18,6) | ✓ | | 增量值 |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

**UNIQUE:** `(meter_id, point_id, stat_date)`

### col_data_quality — 数据质量统计表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id RESTRICT |
| task_id | integer | ✓ | | → col_task.id SET NULL |
| stat_date | date | | | 统计日期 |
| total_points | integer | | | 总测点数 |
| success_points | integer | | | 成功数 |
| failed_points | integer | | | 失败数 |
| quality_score | numeric(5,2) | ✓ | | 质量评分(0-100) |
| abnormal_count | integer | | `0` | 异常数 |
| first_collect_time | timestamptz | ✓ | | 首次采集时间 |
| last_collect_time | timestamptz | ✓ | | 末次采集时间 |
| created_at | timestamptz | | `now()` | |

**UNIQUE:** `(meter_id, stat_date)`

---

## 4. 告警管理模块（sys_alarm_）

### sys_alarm_rule — 告警规则表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| rule_name | varchar(100) | | | 规则名称 |
| rule_type | varchar(50) | | | communication/threshold/anomaly |
| point_code | varchar(50) | | `''` | 关联测点 OBIS |
| condition_config | json | ✓ | | 触发条件配置 |
| severity | varchar(20) | | | info/warning/critical |
| is_enabled | boolean | | `true` | |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

### sys_alarm_record — 告警记录表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| meter_id | integer | | | → dev_meter.id |
| rule_id | integer | ✓ | | → sys_alarm_rule.id |
| alarm_type | varchar(50) | | | communication/threshold/anomaly/stack/eeprom |
| severity | varchar(20) | | | info/warning/critical |
| alarm_message | text | | | 告警描述 |
| alarm_value | numeric(20,6) | ✓ | | 触发值 |
| threshold_value | numeric(20,6) | ✓ | | 阈值 |
| is_handled | boolean | | `false` | 是否已处理 |
| handled_by | integer | ✓ | | 处理人 → sys_user.id |
| handled_at | timestamptz | ✓ | | 处理时间 |
| created_at | timestamptz | | `now()` | |

---

## 5. 实验室管理模块（lab_）

### lab_test_task — 测试任务表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| test_name | varchar(100) | | | 测试名称 |
| test_type | varchar(50) | | | type_approval/protocol_conformance/stability/functional/performance |
| project_id | integer | ✓ | | → dev_project.id |
| status | varchar(20) | | | planned/running/completed/cancelled |
| description | text | | `''` | |
| start_time | timestamptz | ✓ | | |
| expected_end_time | timestamptz | ✓ | | |
| created_by | integer | ✓ | | → sys_user.id |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

### lab_test_report — 测试报告表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| test_id | integer | | | → lab_test_task.id (UNIQUE) |
| report_number | varchar(50) | | | 报告编号 (UNIQUE) |
| test_type | varchar(50) | | `''` | |
| test_environment | varchar(200) | | `''` | 测试环境 |
| test_duration_days | integer | | `0` | 测试天数 |
| firmware_version | varchar(50) | | `''` | |
| hardware_version | varchar(50) | | `''` | |
| conclusion | varchar(20) | | `''` | pass/fail/conditional |
| notes | text | | `''` | |
| generated_by | integer | ✓ | | → sys_user.id |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

### lab_defect — 缺陷记录表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| test_id | integer | | | → lab_test_task.id |
| title | varchar(200) | | | 缺陷标题 |
| description | text | | `''` | 详细描述 |
| severity | varchar(20) | | | critical/major/minor |
| status | varchar(20) | | | open/in_progress/resolved/closed |
| meter_id | integer | ✓ | | → dev_meter.id |
| detected_at | timestamptz | ✓ | | 发现时间 |
| resolved_by | integer | ✓ | | → sys_user.id |
| resolved_at | timestamptz | ✓ | | 解决时间 |
| created_at | timestamptz | | `now()` | |

---

## 6. 数据归档模块（sys_data_）

### sys_data_archive — 数据归档记录表

| 列名 | 类型 | 可空 | 默认值 | 说明 |
|------|------|:--:|--------|------|
| id | integer | | 自增 PK | |
| archive_type | varchar(20) | | | postgresql/mongodb |
| table_name | varchar(100) | | | 归档表名 |
| start_time | timestamptz | | | 数据起始时间 |
| end_time | timestamptz | | | 数据结束时间 |
| record_count | integer | | `0` | 记录数 |
| archive_status | varchar(20) | | | pending/running/completed/failed |
| created_at | timestamptz | | `now()` | |
| updated_at | timestamptz | | `now()` | |

---

## ER 关系概览

```
sys_user ─┬── sys_user_role ──── sys_role ── sys_role_permission ── sys_permission
          ├── sys_department
          └─────────────────────────────────────────────────────┐
                                                                │
dev_project ←── dev_meter ──┬── dev_meter_comm     (1:1)       │
          │                 ├── dev_meter_snapshot  (1:1)       │
          │                 ├── dev_meter_status    (1:N)       │
          │                 ├── dev_meter_point     (1:N)       │
          │                 ├── dev_meter_borrow    (1:N)       │
          │                 ├── dev_meter_repair    (1:N)       │
          │                 ├── dev_meter_attachment(1:N)       │
          │                 └── dev_meter_type      (N:1)       │
          │                                                   │
          ├── lab_test_task ──┬── lab_test_report               │
          │                   └── lab_defect                    │
          │                                                   │
col_task ──── col_task_log ──── col_task_device                │
          │                                                   │
col_session ──── dev_meter (桥接 MongoDB)                      │
          │                                                   │
col_meter_reading ── dev_meter_point ── col_reading_daily      │
                                                              │
sys_alarm_rule ── sys_alarm_record ── dev_meter               │
sys_audit_log ────────────────────────── sys_user ─────────────┘
sys_data_archive
col_data_quality
```

---

## 外键删除策略总结

| 策略 | 应用场景 |
|------|---------|
| **CASCADE** | 父记录删除时自动删子记录（meter→point/comm/snapshot/status, task→log→device） |
| **RESTRICT** | 有引用数据时禁止删除父记录（reading→meter, borrow→meter, repair→meter） |
| **SET NULL** | 父记录删除时置空外键（user→created_by, project→meter, task→session） |
