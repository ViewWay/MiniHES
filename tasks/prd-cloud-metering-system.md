# PRD: 云端多表抄表与实验室测试管理平台

## 1. 项目概述

**项目名称**: CloudMeters - 云端多表抄表与实验室测试管理平台

**项目定位**: 面向公用事业（水、电、气、热）的实验室测试管理平台，支持样机管理、数据采集、数据分析、大屏监控、测试报告等全流程管理。

**核心技术栈**:
| 层级 | 技术选择 |
|------|----------|
| 前端 | vue-vben-admin 5.7.0 (Vue 3 + TypeScript + Ant Design Vue) |
| 后端 | Python FastAPI |
| 数据库 | PostgreSQL + Redis + InfluxDB (时序数据) |
| 缓存 | Redis |
| 任务队列 | Celery + Redis |
| 图表 | ECharts |

**系统规模**: 500-5000 设备，单机 + Redis 架构

---

## 2. 业务场景

### 2.1 实验室测试场景

```
样机全生命周期管理:
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 样机入库 │───▶│ 挂表测试 │───▶│ 测试完成 │───▶│ 归档拆表 │
│ (归档)  │    │ (采集)  │    │ (分析)  │    │ (复用)  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                  │                              │
                  ▼                              ▼
            ┌─────────┐                    ┌─────────┐
            │ 数据分析 │                    │ 样机借用 │
            │ 异常检测 │                    │ 审批流程 │
            └─────────┘                    └─────────┘
```

### 2.2 设备类型与分类

**支持表计类型**: 电表、水表、气表、热量表（可扩展）

**设备分类维度**:

| 维度 | 分类示例 |
|------|----------|
| **按项目** | Coral项目 → coral-01电表 → DCSP/DCPP/CTPP/HVCT/LVCT/MVCT0.2s/MVCT0.5s |
| **按表型** | DCSP, DCPP, CTPP, HVCT, LVCT, MVCT0.2s, MVCT0.5s |
| **按线制** | 单相(BS/DIN), DC, CT, 3P3W, 3P4W |
| **按协议** | DLMS/COSEM, Modbus, MQTT |

---

## 3. 功能模块

### 3.1 设备管理系统（实验室样机管理）

#### 3.1.1 样机状态流转

```
                    ┌─────────────┐
                    │    在库     │◀─────────────────┐
                    └──────┬──────┘                  │
                           │                         │
                    ┌──────▼──────┐                 │
                    │ 挂表测试中  │                 │
                    └──────┬──────┘                 │
                           │                         │
                    ┌──────▼──────┐                 │
                    │测试完成待拆 │                  │
                    └──────┬──────┘                 │
                           │                         │
              ┌────────────┼────────────┐           │
              ▼            ▼            ▼           │
         ┌─────────┐  ┌─────────┐  ┌─────────┐     │
         │  借出   │  │ 维修中  │  │  报废   │     │
         └────┬────┘  └────┬────┘  └─────────┘     │
              │            │                        │
              └────────────┴────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │    在库     │
                    └─────────────┘
```

**样机状态定义**:

| 状态 | 说明 | 可转状态 |
|------|------|----------|
| 在库 | 样机在库，可用 | 挂表测试中、借出、维修中、报废 |
| 挂表测试中 | 正在进行挂表测试 | 测试完成待拆、维修中 |
| 测试完成待拆 | 测试完成，等待拆表 | 在库、维修中 |
| 借出 | 样机已借出 | 在库、维修中 |
| 维修中 | 样机正在维修 | 在库、报废 |
| 报废 | 样机已报废 | - |

#### 3.1.2 样机档案

**归档登记信息**:

| 分类 | 字段 | 说明 |
|------|------|------|
| **基本信息** | 表计型号 | 如: DCSP, DCPP |
| | 厂商 | 表计厂商 |
| | 出厂编号 | 唯一标识 |
| | 数量 | 数量 |
| **版本信息** | 软件版本 | 固件版本号 |
| | 硬件版本 | 硬件版本号 |
| **项目信息** | 项目名 | 所属项目 |
| | 项目测试负责人 | 测试负责人 |
| | 项目研发负责人 | 研发负责人 |
| **位置信息** | 放置位置 | 存放位置 |
| | 框编号 | 测试架编号 |
| **扩展信息** | 协议版本 | DLMS/Modbus版本 |
| | 外观照片 | 设备照片 |
| | 附件清单 | 随机附件 |

#### 3.1.3 样机借用管理

**借用审批流程**:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 申请人  │───▶│部门审批 │───▶│实验室审批│───▶│ 借出登记 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                   │
                                              ┌───▼────┐
                                              │ 归还   │
                                              └────────┘
```

**借用记录**:

| 字段 | 说明 |
|------|------|
| 借用人 | 借用人姓名 |
| 申请时间 | 借用申请时间 |
| 预计归还 | 预计归还日期 |
| 实际归还 | 实际归还日期 |
| 部门审批人 | 部门审批人 |
| 部门审批时间 | 部门审批时间 |
| 实验室审批人 | 实验室审批人 |
| 实验室审批时间 | 实验室审批时间 |
| 审批状态 | 待审批/已批准/已拒绝 |

#### 3.1.4 样机操作功能

| 功能 | 说明 |
|------|------|
| 信息变更 | 修改样机档案信息 |
| 维修记录 | 记录维修历史 |
| 附件管理 | 上传测试报告、照片等附件 |
| 数据导出 | 导出样机清单、借用记录等 |

---

### 3.2 数据采集系统

#### 3.2.1 采集任务类型

```
采集任务分类:
├── 定时任务 (Cron)
│   └── 示例: 每天凌晨2:30执行
│
├── 循环任务 (Interval)
│   └── 示例: 每隔120秒执行
│
└── 一次性任务 (Once)
    └── 执行后自动删除
```

#### 3.2.2 任务执行内容

| 任务类型 | 说明 |
|----------|------|
| 抄读整表 | 抄读表计的全部配置和测量数据 |
| 固件升级 | 远程升级表计固件 |
| 参数下发 | 设置参数、修改配置 |
| 控制命令 | 激活/断电、继电器控制 |
| STS/CTS充值 | 预付费充值 |

#### 3.2.3 任务执行范围

**多维度筛选**:

| 维度 | 说明 | 示例 |
|------|------|------|
| 单设备 | 选择单个设备 | Device-001 |
| 按项目 | 选择整个项目 | Coral项目 |
| 按表型 | 选择表计类型 | DCSP, DCPP |
| 按线制 | 选择线制类型 | 单相BS, 3P4W |
| 自由筛选 | 自由组合筛选 | 项目+表型组合 |

#### 3.2.4 采集场景

**实验室测试采集**:

| 功能 | 说明 |
|------|------|
| 定时采集 | 按设定周期自动抄读 |
| 手动触发 | 测试人员手动触发 |
| 异常告警 | 采集异常时记录并告警 |
| 实时展示 | 采集数据实时展示 |

**远程抄表采集**:

| 功能 | 说明 |
|------|------|
| 批量采集 | 批量抄读多个设备 |
| 单设备采集 | 单个设备立即抄读 |
| 定时任务 | 按计划定时自动抄读 |
| 失败重试 | 采集失败自动重试 |

#### 3.2.5 任务监控

| 监控项 | 说明 |
|--------|------|
| 执行状态 | 待执行/执行中/已完成/失败 |
| 执行结果 | 成功/失败数量统计 |
| 执行日志 | 每个设备的执行详细日志 |
| 失败重试 | 失败任务自动重试机制 |

#### 3.2.6 通信协议

| 协议 | 适用设备 | 说明 |
|------|----------|------|
| DLMS/COSEM | 电表 | 智能电表标准协议 |
| Modbus | 水/气表 | 通用工业协议 |
| MQTT | NB-IoT设备 | 物联网消息协议 |
| 扩展接口 | - | 插件式扩展新协议 |

---

### 3.3 数据分析系统

#### 3.3.1 分析场景

**挂表测试期间每日数据分析**:

| 分析对象 | 检查内容 |
|----------|----------|
| 电能数据 | 是否按周期递增 |
| 时钟 | 时间是否准确 |
| 月结算曲线 | 是否按周期记录 |
| 日结算曲线 | 是否按周期记录 |
| 负荷曲线1 | 是否按周期记录 |
| 负荷曲线2 | 是否按周期记录 |
| 电网质量曲线 | 是否按周期记录 |
| 标准事件 | 事件统计和分析 |
| 窃电事件 | 异常检测 |
| 通信事件 | 通信质量分析 |
| 预付费事件 | 充值和消费分析 |

**异常检测规则**:

| 规则 | 说明 |
|------|------|
| 今日vs昨日对比 | 检测数据突变 |
| 曲线周期检查 | 检测曲线是否按周期增加 |
| 事件异常检测 | 检测异常事件 |

#### 3.3.2 分析输出

| 输出类型 | 说明 |
|----------|------|
| 自动日报 | 每日自动生成测试分析报告 |
| 异常告警 | 异常时产生告警通知 |
| 统计报表 | 按项目/设备生成统计报表 |
| 数据导出 | 导出分析数据 |
| 大屏展示 | 大屏显示分析结果 |

---

### 3.4 大屏展示系统

#### 3.4.1 大屏类型

**三种大屏**:

1. **项目概览大屏** - 展示全部测试项目概览
2. **项目详情大屏** - 单个项目的详细监控
3. **单表监控大屏** - 单块表的实时数据监控

#### 3.4.2 项目概览大屏

| 展示内容 | 说明 |
|----------|------|
| 项目状态 | 各项目的测试状态和进度 |
| 表计统计 | 各项目的表计数量和在线情况 |
| 异常告警 | 异常项目和告警信息 |
| 堆栈监控 | 表计存储栈监控 |
| 事件监控 | 事件统计和趋势 |
| 电能监控 | 电能数据统计 |

#### 3.4.3 项目详情大屏

| 展示内容 | 说明 |
|----------|------|
| 电能曲线 | 各表计的电能曲线图 |
| 事件列表 | 表计事件列表和统计 |
| 堆栈监控 | 堆栈数据监控和告警 |
| 通信状态 | 表计在线状态和通信质量 |
| 电网质量曲线 | 电网质量监控数据 |

#### 3.4.4 单表监控大屏

| 展示内容 | 说明 |
|----------|------|
| 实时数据 | 电压、电流、功率、功率因数、相角等瞬时值 |
| 曲线图表 | 抄读事件曲线 |
| 稳定性分析 | 评估表计运行稳定程度 |
| 堆栈监控 | 堆栈数据监控 |
| EEPROM监控 | EEPROM数据监控 |

---

### 3.5 任务调度系统

**任务类型**:

| 任务类型 | 说明 |
|----------|------|
| 采集任务 | 定时抄表任务 |
| 分析任务 | 数据分析计算任务 |
| 报表任务 | 定时报表生成 |
| 清理任务 | 历史数据清理 |

**调度策略**:

| 策略 | 说明 |
|------|------|
| Cron表达式 | 定时任务 |
| 固定间隔 | 循环任务 |
| 手动触发 | 立即执行 |

---

### 3.6 测试报告系统

#### 3.6.1 测试类型

| 测试类型 | 说明 |
|----------|------|
| 协议测试 | 验证DLMS/Modbus协议一致性 |
| 采集准确性 | 测试数据采集准确性 |
| 功能测试 | 测试各项功能是否正常 |
| 稳定性测试 | 长时间运行稳定性测试 |

#### 3.6.2 测试报告内容

| 内容项 | 说明 |
|--------|------|
| 测试环境 | 测试环境描述 |
| 挂测时长 | 挂表测试时长 |
| 挂测版本 | 测试的软件/硬件版本 |
| 缺陷记录 | 发现的缺陷列表 |
| 缺陷状态 | 缺陷是否已解决 |
| 测试结论 | 测试通过/不通过 |

#### 3.6.3 报告生成与分发

**生成方式**:
- 项目软件测试负责人生成
- 系统自动生成

**分发对象**:
- 项目软件测试负责人
- 项目研发负责人
- 功能测试负责人
- 功能研发负责人
- 测试领导
- 研发领导
- 部门

#### 3.6.4 缺陷管理

| 功能 | 说明 |
|------|------|
| 缺陷记录 | 记录发现的缺陷 |
| 缺陷跟踪 | 跟踪缺陷修复状态 |
| 缺陷验证 | 缺陷验证闭环 |
| 缺陷统计 | 缺陷统计分析 |

---

### 3.7 角色与权限系统

#### 3.7.1 角色定义

```
┌─────────────────────────────────────────────────────────┐
│                    超级管理员                            │
│              实验室管理员 | 系统管理员                    │
├─────────────────────────────────────────────────────────┤
│                      管理员                              │
│              测试负责人 | 研发负责人                      │
├─────────────────────────────────────────────────────────┤
│                      普通用户                            │
│  项目软件测试负责人 | 项目研发负责人 | 功能测试/研发负责人  │
└─────────────────────────────────────────────────────────┘
```

| 角色类型 | 具体角色 | 说明 |
|----------|----------|------|
| 超级管理员 | 实验室管理员 | 实验室最高权限 |
| | 系统管理员 | 系统运维权限 |
| 管理员 | 测试负责人 | 测试管理权限 |
| | 研发负责人 | 研发管理权限 |
| 普通用户 | 项目软件测试负责人 | 项目测试执行 |
| | 项目研发负责人 | 项目研发执行 |
| | 功能测试负责人 | 功能测试执行 |
| | 功能研发负责人 | 功能研发执行 |

#### 3.7.2 权限维度

| 权限类型 | 说明 |
|----------|------|
| 功能权限 | 菜单、页面、按钮的访问权限 |
| 项目数据权限 | 只能看自己负责的项目数据 |
| 操作权限 | 增删改查的操作权限 |
| 字段权限 | 字段级别的可见性控制 |

---

## 4. 数据库设计

### 4.1 PostgreSQL 表结构

#### 4.1.1 核心业务表

| 表名 | 说明 |
|------|------|
| **用户权限** | |
| sys_user | 用户表 |
| sys_role | 角色表 |
| sys_permission | 权限表 |
| sys_user_role | 用户角色关联（多对多） |
| sys_role_permission | 角色权限关联（多对多） |
| **设备管理** | |
| dev_project | 项目表 |
| dev_meter_type | 表计类型表 |
| dev_wire_type | 线制类型表 |
| dev_meter | 样机档案表 |
| dev_meter_point | 采集点配置（OBIS码/点位定义） |
| dev_meter_comm | 设备通信配置 |
| dev_meter_snapshot | 设备实时状态快照 |
| dev_meter_status | 样机状态变更记录 |
| dev_meter_borrow | 样机借用记录 |
| dev_meter_repair | 样机维修记录 |
| dev_meter_attachment | 样机附件 |
| **采集任务** | |
| col_task | 采集任务表 |
| col_task_log | 采集任务执行日志 |
| col_task_device | 任务设备关联 |
| col_data_quality | 数据质量统计 |
| **告警审计** | |
| sys_alarm_rule | 告警规则配置 |
| sys_alarm_record | 告警记录 |
| sys_audit_log | 操作审计日志 |
| **测试管理** | |
| lab_test_task | 测试任务表 |
| lab_test_report | 测试报告表 |
| lab_defect | 缺陷记录表 |
| **系统管理** | |
| sys_data_archive | 数据归档记录 |

#### 4.1.2 核心表详细设计

**dev_meter（样机档案表）**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| serial_number | VARCHAR(50) | 出厂编号（唯一） |
| meter_name | VARCHAR(100) | 表计名称 |
| meter_type_id | BIGINT | 表计类型ID（FK） |
| project_id | BIGINT | 所属项目ID（FK） |
| protocol | VARCHAR(20) | 通信协议（DLMS/Modbus/MQTT） |
| line_type | VARCHAR(20) | 线制类型 |
| manufacturer | VARCHAR(100) | 厂商 |
| model | VARCHAR(100) | 型号 |
| firmware_version | VARCHAR(50) | 固件版本 |
| hardware_version | VARCHAR(50) | 硬件版本 |
| frame_number | VARCHAR(50) | 框编号 |
| location | VARCHAR(100) | 放置位置 |
| current_status | VARCHAR(20) | 当前状态 |
| factory_date | DATE | 出厂日期 |
| purchase_date | DATE | 购买日期 |
| warranty_date | DATE | 质保到期日 |
| notes | TEXT | 备注 |
| created_by | BIGINT | 创建人（FK） |
| updated_by | BIGINT | 更新人（FK） |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**dev_meter_point（采集点配置表）**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| point_code | VARCHAR(50) | 点位编码（OBIS码:1.0.0.0.0.255） |
| point_name | VARCHAR(100) | 点位名称 |
| point_type | VARCHAR(50) | 点位类型（register/attribute/profile） |
| data_type | VARCHAR(20) | 数据类型（numeric/int/string） |
| unit | VARCHAR(20) | 单位（kWh/V/A/W） |
| protocol | VARCHAR(20) | 协议类型 |
| description | TEXT | 描述 |
| storage_target | VARCHAR(20) | 存储目标（influxdb/postgresql/both） |
| retention_days | INT | 保留天数 |
| created_at | TIMESTAMPTZ | 创建时间 |

**dev_meter_comm（通信配置表）**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| meter_id | BIGINT | 设备ID（FK） |
| protocol | VARCHAR(20) | 协议类型 |
| connection_type | VARCHAR(20) | 连接类型（tcp/serial/udp） |
| host | VARCHAR(255) | IP地址 |
| port | INT | 端口号 |
| device_address | VARCHAR(50) | 从站地址/设备ID |
| baud_rate | INT | 波特率（串口） |
| parity | VARCHAR(10) | 校验位 |
| data_bits | INT | 数据位 |
| stop_bits | INT | 停止位 |
| auth_config | JSONB | 认证配置 |
| timeout | INT | 超时时间（秒） |
| retry_times | INT | 重试次数 |
| is_enabled | BOOLEAN | 是否启用 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**dev_meter_snapshot（设备状态快照表）**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| meter_id | BIGINT | 设备ID（FK，唯一） |
| online_status | BOOLEAN | 在线状态 |
| last_comm_time | TIMESTAMPTZ | 最后通信时间 |
| signal_strength | INT | 信号强度（0-100） |
| battery_level | INT | 电池电量（0-100） |
| firmware_version | VARCHAR(50) | 固件版本 |
| error_code | VARCHAR(20) | 错误码 |
| stack_usage | INT | 堆栈使用率 |
| eeprom_write_count | INT | EEPROM写次数 |
| last_data_time | TIMESTAMPTZ | 最后数据时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**col_task（采集任务表）**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| task_name | VARCHAR(100) | 任务名称 |
| task_type | VARCHAR(20) | 任务类型（cron/interval/once） |
| schedule_config | JSONB | 调度配置（Cron表达式或间隔） |
| execution_content | JSONB | 执行内容（抄读哪些点位） |
| filter_config | JSONB | 设备筛选条件 |
| priority | INT | 优先级（1-10） |
| retry_times | INT | 重试次数 |
| timeout | INT | 超时时间（秒） |
| is_enabled | BOOLEAN | 是否启用 |
| last_execute_time | TIMESTAMPTZ | 最后执行时间 |
| next_execute_time | TIMESTAMPTZ | 下次执行时间 |
| created_by | BIGINT | 创建人（FK） |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**col_task_log（采集任务日志表）**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| task_id | BIGINT | 任务ID（FK） |
| start_time | TIMESTAMPTZ | 开始时间 |
| end_time | TIMESTAMPTZ | 结束时间 |
| duration_ms | INT | 执行时长（毫秒） |
| status | VARCHAR(20) | 状态（pending/running/completed/failed） |
| total_devices | INT | 总设备数 |
| success_devices | INT | 成功设备数 |
| failed_devices | INT | 失败设备数 |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMPTZ | 创建时间 |

**col_task_device（任务设备关联表）**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| log_id | BIGINT | 日志ID（FK） |
| task_id | BIGINT | 任务ID（FK） |
| meter_id | BIGINT | 设备ID（FK） |
| status | VARCHAR(20) | 状态（pending/success/failed/timeout） |
| retry_count | INT | 重试次数 |
| error_code | VARCHAR(50) | 错误码 |
| error_message | TEXT | 错误信息 |
| start_time | TIMESTAMPTZ | 开始时间 |
| end_time | TIMESTAMPTZ | 结束时间 |
| duration_ms | INT | 执行时长（毫秒） |
| data_count | INT | 采集数据点数 |
| created_at | TIMESTAMPTZ | 创建时间 |

**col_data_quality（数据质量统计表）**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| meter_id | BIGINT | 设备ID（FK） |
| task_id | BIGINT | 任务ID（FK） |
| stat_date | DATE | 统计日期 |
| total_points | INT | 应采点数 |
| success_points | INT | 成功点数 |
| failed_points | INT | 失败点数 |
| quality_score | DECIMAL(5,2) | 质量分数（0-100） |
| abnormal_count | INT | 异常点数 |
| first_collect_time | TIMESTAMPTZ | 首次采集时间 |
| last_collect_time | TIMESTAMPTZ | 最后采集时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

**sys_alarm_rule（告警规则配置表）**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| rule_name | VARCHAR(100) | 规则名称 |
| rule_type | VARCHAR(50) | 规则类型（threshold/anomaly/communication） |
| point_code | VARCHAR(50) | 关联点位 |
| condition_config | JSONB | 条件配置 |
| severity | VARCHAR(20) | 严重程度（critical/warning/info） |
| is_enabled | BOOLEAN | 是否启用 |
| created_at | TIMESTAMPTZ | 创建时间 |

**sys_alarm_record（告警记录表）**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| meter_id | BIGINT | 设备ID（FK） |
| rule_id | BIGINT | 规则ID（FK） |
| alarm_type | VARCHAR(50) | 告警类型 |
| severity | VARCHAR(20) | 严重程度 |
| alarm_message | TEXT | 告警信息 |
| alarm_value | NUMERIC(20,6) | 告警值 |
| threshold_value | NUMERIC(20,6) | 阈值 |
| is_handled | BOOLEAN | 是否已处理 |
| handled_by | BIGINT | 处理人（FK） |
| handled_at | TIMESTAMPTZ | 处理时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

**sys_audit_log（操作审计日志表）**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| user_id | BIGINT | 用户ID（FK） |
| operation_type | VARCHAR(50) | 操作类型（CREATE/UPDATE/DELETE/LOGIN） |
| resource_type | VARCHAR(50) | 资源类型（meter/task/report） |
| resource_id | BIGINT | 资源ID |
| old_values | JSONB | 旧值 |
| new_values | JSONB | 新值 |
| ip_address | INET | IP地址 |
| user_agent | TEXT | 用户代理 |
| created_at | TIMESTAMPTZ | 创建时间 |

#### 4.1.3 索引设计

**核心索引**:

```sql
-- dev_meter 表索引
CREATE INDEX idx_dev_meter_type ON dev_meter(meter_type_id);
CREATE INDEX idx_dev_meter_project ON dev_meter(project_id);
CREATE INDEX idx_dev_meter_status ON dev_meter(current_status);
CREATE INDEX idx_dev_meter_protocol ON dev_meter(protocol);
CREATE INDEX idx_dev_meter_serial ON dev_meter(serial_number);
CREATE INDEX idx_dev_meter_created ON dev_meter(created_at);

-- 复合索引
CREATE INDEX idx_dev_meter_status_project ON dev_meter(current_status, project_id);

-- col_task 表索引
CREATE INDEX idx_col_task_type ON col_task(task_type);
CREATE INDEX idx_col_task_enabled ON col_task(is_enabled) WHERE is_enabled = TRUE;
CREATE INDEX idx_col_task_next_exec ON col_task(next_execute_time) WHERE is_enabled = TRUE;

-- col_task_log 表索引（分区表）
CREATE INDEX idx_col_task_log_task ON col_task_log(task_id);
CREATE INDEX idx_col_task_log_status ON col_task_log(status);
CREATE INDEX idx_col_task_log_created ON col_task_log(created_at DESC);

-- col_task_device 表索引
CREATE INDEX idx_col_task_device_log ON col_task_device(log_id);
CREATE INDEX idx_col_task_device_meter ON col_task_device(meter_id);
CREATE INDEX idx_col_task_device_status ON col_task_device(status);

-- dev_meter_snapshot 表索引
CREATE INDEX idx_dev_snapshot_online ON dev_meter_snapshot(online_status);
CREATE INDEX idx_dev_snapshot_updated ON dev_meter_snapshot(updated_at);

-- sys_alarm_record 表索引
CREATE INDEX idx_sys_alarm_meter ON sys_alarm_record(meter_id);
CREATE INDEX idx_sys_alarm_severity ON sys_alarm_record(severity);
CREATE INDEX idx_sys_alarm_handled ON sys_alarm_record(is_handled) WHERE is_handled = FALSE;
CREATE INDEX idx_sys_alarm_created ON sys_alarm_record(created_at DESC);

-- sys_audit_log 表索引
CREATE INDEX idx_sys_audit_user ON sys_audit_log(user_id);
CREATE INDEX idx_sys_audit_type ON sys_audit_log(operation_type);
CREATE INDEX idx_sys_audit_resource ON sys_audit_log(resource_type, resource_id);
CREATE INDEX idx_sys_audit_created ON sys_audit_log(created_at DESC);
```

#### 4.1.4 分区表设计

**col_task_log 分区表（按月分区）**:

```sql
-- 分区表定义
CREATE TABLE col_task_log (
    id BIGSERIAL,
    task_id BIGINT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_ms INT,
    status VARCHAR(20) NOT NULL,
    total_devices INT DEFAULT 0,
    success_devices INT DEFAULT 0,
    failed_devices INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 自动创建分区函数
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    partition_date TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    partition_date := to_char(CURRENT_DATE + INTERVAL '1 month', 'YYYY_MM');
    start_date := to_char(CURRENT_DATE, 'YYYY-MM-DD');
    end_date := to_char(CURRENT_DATE + INTERVAL '1 month', 'YYYY-MM-DD');
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS col_task_log_%s PARTITION OF col_task_log
         FOR VALUES FROM (%L) TO (%L)',
        partition_date, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;
```

**col_data_quality 分区表（按月分区）**:

```sql
CREATE TABLE col_data_quality (
    id BIGSERIAL,
    meter_id BIGINT NOT NULL,
    task_id BIGINT,
    stat_date DATE NOT NULL,
    total_points INT DEFAULT 0,
    success_points INT DEFAULT 0,
    failed_points INT DEFAULT 0,
    quality_score DECIMAL(5,2),
    abnormal_count INT DEFAULT 0,
    first_collect_time TIMESTAMPTZ,
    last_collect_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, stat_date)
) PARTITION BY RANGE (stat_date);
```

### 4.2 数据存储架构

#### 4.2.1 存储选型对比

抄读数据是典型的**时序数据**，具有以下特点：

| 特点 | 说明 |
|------|------|
| 时序性 | 每条数据带时间戳，按时间顺序产生 |
| 写多读少 | 持续写入，查询通常是按时间范围聚合 |
| 数据量大 | 5000设备 × 120秒采集 × 86400秒/天 = 大量数据 |
| 结构固定 | (时间, 设备ID, 点位类型, 数值, 质量) |

**存储方案对比**:

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| PostgreSQL | 成熟稳定，支持事务 | 数据表膨胀快，时序查询慢 | 业务数据 |
| MongoDB | 灵活schema，水平扩展 | 时序聚合查询需要全表扫描 | 文档存储 |
| InfluxDB ✅ | 专为时序优化，压缩率高 | 不适合复杂关联查询 | **抄读数据** |
| Redis | 极速读写 | 内存成本高，数据易失 | **实时缓存** |

#### 4.2.2 数据分类存储

```
                    ┌─────────────────────────────────────┐
                    │            应用层                    │
                    └─────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ PostgreSQL  │  │  InfluxDB   │  │    Redis    │
    │ (业务数据)  │  │  (时序数据) │  │   (缓存)    │
    └─────────────┘  └─────────────┘  └─────────────┘
```

| 数据类型 | 存储 | 保留策略 | 说明 |
|----------|------|----------|------|
| **业务数据** | | | |
| 样机档案 | PostgreSQL | 永久 | 设备基本信息 |
| 用户权限 | PostgreSQL | 永久 | RBAC权限数据 |
| 采集任务 | PostgreSQL | 永久 | 任务配置信息 |
| 测试报告 | PostgreSQL | 永久 | 报告和缺陷 |
| **时序数据** | | | |
| 实时抄读（瞬时值） | InfluxDB | 7天 | 电压、电流、功率等 |
| 电能数据 | InfluxDB | 1年 | 总电能、各相电能 |
| 结算曲线 | InfluxDB | 1年 | 月结算、日结算 |
| 负荷曲线 | InfluxDB | 6个月 | 负荷曲线1、2 |
| 电网质量 | InfluxDB | 3个月 | 电网质量曲线 |
| 事件记录 | InfluxDB + PG | 永久 | 各类事件（PG存详情） |
| **缓存数据** | | | |
| 最新数据 | Redis | 实时 | 大屏实时展示 |
| 任务队列 | Redis | 临时 | Celery任务队列 |

### 4.3 InfluxDB 数据模型设计

#### 4.3.1 Measurement 分拆设计

按数据类型分拆 Measurement，避免混在一起导致性能问题：

| Measurement | 说明 | 采集频率 | 保留策略 |
|-------------|------|----------|----------|
| **meter_instant** | 瞬时值数据 | 120秒 | 7天 |
| **meter_energy** | 电能数据 | 120秒 | 1年 |
| **meter_load_profile** | 负荷曲线 | 120秒 | 6个月 |
| **meter_billing_profile** | 结算曲线 | 每日 | 1年 |
| **meter_power_quality** | 电网质量 | 120秒 | 3个月 |
| **meter_event** | 事件记录 | 触发式 | 永久 |

#### 4.3.2 瞬时值 Measurement（高频数据）

```
Measurement: meter_instant
Tags (索引):
  - device_id: 设备ID
  - project_id: 项目ID
  - phase: 相位（A/B/C/avg）
  - meter_type: 表计类型

Fields (值):
  - voltage: 电压（V）
  - current: 电流（A）
  - active_power: 有功功率（W）
  - reactive_power: 无功功率（var）
  - power_factor: 功率因数
  - frequency: 频率（Hz）
  - phase_angle: 相角（度）

Timestamp: 自动索引

保留策略: 7天（原始数据）
降采样:
  - 5分钟聚合 → 保留30天
  - 1小时聚合 → 保留90天
```

#### 4.3.3 电能数据 Measurement

```
Measurement: meter_energy
Tags (索引):
  - device_id: 设备ID
  - project_id: 项目ID
  - energy_type: 电能类型（total/phase_a/phase_b/phase_c）
  - tariff: 费率类型（1/2/3/4）

Fields (值):
  - total: 总电能（kWh）
  - tariff_1: 费率1电能（kWh）
  - tariff_2: 费率2电能（kWh）
  - tariff_3: 费率3电能（kWh）
  - tariff_4: 费率4电能（kWh）

保留策略: 1年
降采样:
  - 1小时聚合 → 保留1年
  - 1天聚合 → 永久保留
```

#### 4.3.4 事件记录 Measurement

```
Measurement: meter_event
Tags (索引):
  - device_id: 设备ID
  - project_id: 项目ID
  - event_type: 事件类型（standard/theft/communication/prepayment）
  - event_code: 事件码

Fields (值):
  - event_value: 事件值
  - duration: 持续时间（秒）

保留策略: 永久
```

#### 4.3.5 降采样策略配置

```sql
-- 保留策略定义
CREATE RETENTION POLICY "rp_raw" ON "metering" DURATION 7d REPLICATION 1 DEFAULT;
CREATE RETENTION POLICY "rp_5m" ON "metering" DURATION 30d REPLICATION 1;
CREATE RETENTION POLICY "rp_1h" ON "metering" DURATION 90d REPLICATION 1;
CREATE RETENTION POLICY "rp_1d" ON "metering" DURATION INF REPLICATION 1;

-- 连续查询（自动降采样）
-- 5分钟聚合
CREATE CONTINUOUS QUERY "cq_instant_5m" ON "metering"
BEGIN
    SELECT mean(*) INTO "metering"."rp_5m"."meter_instant_5m"
    FROM "metering"."rp_raw"."meter_instant"
    GROUP BY time(5m), "device_id", "phase"
END;

-- 1小时聚合
CREATE CONTINUOUS QUERY "cq_instant_1h" ON "metering"
BEGIN
    SELECT mean(*) INTO "metering"."rp_1h"."meter_instant_1h"
    FROM "metering"."rp_5m"."meter_instant_5m"
    GROUP BY time(1h), "device_id", "phase"
END;

-- 1天聚合
CREATE CONTINUOUS QUERY "cq_instant_1d" ON "metering"
BEGIN
    SELECT mean(*) INTO "metering"."rp_1d"."meter_instant_1d"
    FROM "metering"."rp_1h"."meter_instant_1h"
    GROUP BY time(1d), "device_id", "phase"
END;
```

### 4.4 数据一致性保证

#### 4.4.1 跨数据库事务处理

由于采集任务需要同时更新 PostgreSQL（任务状态）和 InfluxDB（时序数据），采用**最终一致性 + 补偿机制**：

```
采集执行流程:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 执行采集    │───▶│ 写入InfluxDB│───▶│ 更新PG状态  │
│ (读取设备)  │    │ (时序数据)  │    │ (任务日志)  │
└─────────────┘    └─────────────┘    └─────────────┘
                       │失败                │失败
                       ▼                    ▼
                ┌─────────────┐    ┌─────────────┐
                │ 记录补偿队列 │    │ 记录补偿队列 │
                └─────────────┘    └─────────────┘
                           │                │
                           ▼                ▼
                    ┌─────────────────────────────┐
                    │    定时补偿任务处理          │
                    │  (每分钟扫描补偿队列)        │
                    └─────────────────────────────┘
```

#### 4.4.2 数据校验机制

```sql
-- 数据一致性检查视图
CREATE OR REPLACE VIEW v_data_consistency_check AS
SELECT
    m.id AS meter_id,
    m.serial_number,
    COUNT(DISTINCT DATE(tcl.start_time)) AS postgres_task_days,
    COUNT(DISTINCT DATE(influx_time)) AS influx_data_days,
    COUNT(DISTINCT DATE(tcl.start_time)) - COUNT(DISTINCT DATE(influx_time)) AS missing_days
FROM dev_meter m
LEFT JOIN col_task_device tcd ON m.id = tcd.meter_id
LEFT JOIN col_task_log tcl ON tcd.log_id = tcl.id
LEFT JOIN (
    -- InfluxDB数据查询（通过外部服务）
    SELECT device_id, time AS influx_time
    FROM influx_data_placeholder
) influx ON m.id = influx.device_id
GROUP BY m.id, m.serial_number;
```

### 4.5 备份和恢复策略

#### 4.5.1 PostgreSQL 备份策略

| 备份类型 | 频率 | 保留 | 说明 |
|----------|------|------|------|
| 全量备份 | 每天02:00 | 30天 | pg_dump |
| WAL归档 | 实时 | 7天 | 增量恢复 |
| 恢复测试 | 每周 | - | 验证备份可用性 |

```bash
# 备份脚本
pg_dump -h localhost -U postgres -d metering_db \
    -F c -f /backup/postgres/full_$(date +%Y%m%d).dump

# WAL归档配置
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
```

#### 4.5.2 InfluxDB 备份策略

| 备份类型 | 频率 | 保留 | 说明 |
|----------|------|------|------|
| 完整备份 | 每天03:00 | 7天 | influx backup |
| 事件导出 | 每天04:00 | 365天 | CSV导出 |

```bash
# InfluxDB 备份
influx backup /backup/influxdb/$(date +%Y%m%d) \
    -bucket metering \
    -host http://localhost:8086 \
    -token ${INFLUX_TOKEN}

# 事件数据导出（长期保留）
influx query 'from(bucket:"metering")
    |> range(start: -30d)
    |> filter(fn: (r) => r._measurement == "meter_event")' \
    > /backup/influxdb/events_$(date +%Y%m%d).csv
```

#### 4.5.3 Redis 备份策略

```bash
# redis.conf 配置
save 900 1
save 300 10
save 60 10000

# RDB + AOF 双持久化
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
```

### 4.6 数据归档策略

```sql
-- 归档存储过程
CREATE OR REPLACE FUNCTION archive_old_task_logs()
RETURNS void AS $$
BEGIN
    -- 归档 90 天前的数据
    INSERT INTO col_task_log_archive
    SELECT * FROM col_task_log
    WHERE created_at < CURRENT_DATE - INTERVAL '90 days';

    -- 删除已归档的数据
    DELETE FROM col_task_log
    WHERE created_at < CURRENT_DATE - INTERVAL '90 days';

    -- 记录归档日志
    INSERT INTO sys_data_archive (
        archive_type, table_name, start_time, end_time, record_count, archive_status
    )
    SELECT
        'postgresql',
        'col_task_log',
        min(created_at),
        max(created_at),
        count(*),
        'completed'
    FROM col_task_log_archive
    WHERE created_at >= CURRENT_DATE - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;
```

### 4.7 数据库监控指标

| 监控项 | 指标 | 告警阈值 |
|--------|------|----------|
| **PostgreSQL** | | |
| 连接数 | numbackends | > 80 |
| 慢查询 | mean_exec_time | > 1000ms |
| 锁等待 | lock_count | > 30秒 |
| 表膨胀 | dead_tuple_ratio | > 20% |
| **InfluxDB** | | |
| 写入性能 | write_points | 监控趋势 |
| 查询性能 | query_duration | > 5秒 |
| 存储空间 | disk_usage | > 80% |
| **Redis** | | |
| 内存使用 | used_memory | > 80% |
| 缓存命中率 | hit_rate | < 80% |
| 连接数 | connected_clients | > 1000 |

---

## 5. API 设计

### 5.1 API 规范

#### 5.1.1 通用响应格式

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "timestamp": "2026-05-14T10:00:00Z"
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "Validation failed",
  "errors": [
    {
      "field": "serial_number",
      "message": "Serial number is required"
    }
  ],
  "timestamp": "2026-05-14T10:00:00Z"
}
```

#### 5.1.2 错误码定义

| 错误码 | 说明 | HTTP状态码 |
|--------|------|------------|
| **通用错误** | | |
| 200 | 成功 | 200 |
| 400 | 请求参数错误 | 400 |
| 401 | 未认证 | 401 |
| 403 | 无权限 | 403 |
| 404 | 资源不存在 | 404 |
| 500 | 服务器内部错误 | 500 |
| **业务错误** | | |
| 10001 | 设备不存在 | 404 |
| 10002 | 设备状态不允许此操作 | 400 |
| 10003 | 设备已被借用 | 400 |
| 10004 | 采集任务正在执行 | 400 |
| 10005 | 采集任务不存在 | 404 |
| 10006 | 审批流程未完成 | 400 |
| 10007 | 项目不存在 | 404 |
| 20001 | 通信超时 | 500 |
| 20002 | 协议解析失败 | 500 |
| 20003 | 设备离线 | 503 |

#### 5.1.3 分页格式

**请求**:
```
GET /api/v1/meters?page=1&page_size=20
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "pages": 5
  }
}
```

### 5.2 设备管理 API

#### 5.2.1 样机入库

**请求**:
```http
POST /api/v1/meters
Content-Type: application/json
Authorization: Bearer {token}

{
  "serial_number": "DLMS2024001",
  "meter_name": "Coral测试表01",
  "meter_type_id": 1,
  "project_id": 1,
  "protocol": "DLMS",
  "line_type": "3P4W",
  "manufacturer": "厂商A",
  "model": "DCSP",
  "firmware_version": "v1.2.0",
  "hardware_version": "v2.0",
  "frame_number": "A-01",
  "location": "实验室1区",
  "factory_date": "2024-01-01",
  "purchase_date": "2024-02-01",
  "warranty_date": "2026-02-01",
  "notes": "备注信息"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 123,
    "serial_number": "DLMS2024001",
    "current_status": "in_stock",
    "created_at": "2026-05-14T10:00:00Z"
  }
}
```

#### 5.2.2 样机列表

**请求**:
```http
GET /api/v1/meters?page=1&page_size=20&project_id=1&status=in_stock
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 123,
        "serial_number": "DLMS2024001",
        "meter_name": "Coral测试表01",
        "project_name": "Coral项目",
        "meter_type": "DCSP",
        "protocol": "DLMS",
        "current_status": "in_stock",
        "online_status": false,
        "location": "实验室1区"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "pages": 5
  }
}
```

#### 5.2.3 样机详情

**请求**:
```http
GET /api/v1/meters/123
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 123,
    "serial_number": "DLMS2024001",
    "meter_name": "Coral测试表01",
    "meter_type_id": 1,
    "meter_type": "DCSP",
    "project_id": 1,
    "project_name": "Coral项目",
    "protocol": "DLMS",
    "line_type": "3P4W",
    "manufacturer": "厂商A",
    "model": "DCSP",
    "firmware_version": "v1.2.0",
    "hardware_version": "v2.0",
    "frame_number": "A-01",
    "location": "实验室1区",
    "current_status": "in_stock",
    "factory_date": "2024-01-01",
    "purchase_date": "2024-02-01",
    "warranty_date": "2026-02-01",
    "notes": "备注信息",
    "created_at": "2026-05-14T10:00:00Z",
    "updated_at": "2026-05-14T10:00:00Z",
    "communication": {
      "id": 456,
      "connection_type": "tcp",
      "host": "192.168.1.100",
      "port": 4059,
      "device_address": "1",
      "timeout": 30,
      "is_enabled": true
    },
    "snapshot": {
      "online_status": false,
      "last_comm_time": null,
      "signal_strength": null,
      "battery_level": null,
      "error_code": null
    }
  }
}
```

#### 5.2.4 状态变更

**请求**:
```http
POST /api/v1/meters/123/status
Content-Type: application/json

{
  "status": "testing",
  "reason": "开始挂表测试",
  "test_project_id": 1
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 789,
    "meter_id": 123,
    "old_status": "in_stock",
    "new_status": "testing",
    "reason": "开始挂表测试",
    "changed_at": "2026-05-14T10:00:00Z"
  }
}
```

#### 5.2.5 借用申请

**请求**:
```http
POST /api/v1/meters/123/borrow
Content-Type: application/json

{
  "borrower_id": 5,
  "expected_return_date": "2026-06-01",
  "borrow_reason": "开发调试需要",
  "department_approver": 10
}
```

**响应**:
```json
{
  "code": 200,
  "message": "Borrow request submitted, waiting for approval",
  "data": {
    "id": 201,
    "meter_id": 123,
    "borrower_id": 5,
    "borrower_name": "张三",
    "expected_return_date": "2026-06-01",
    "borrow_reason": "开发调试需要",
    "approval_status": "pending_department",
    "created_at": "2026-05-14T10:00:00Z"
  }
}
```

### 5.3 采集任务 API

#### 5.3.1 创建任务

**请求**:
```http
POST /api/v1/tasks
Content-Type: application/json

{
  "task_name": "Coral项目120秒采集",
  "task_type": "interval",
  "schedule_config": {
    "interval": 120,
    "unit": "seconds"
  },
  "execution_content": {
    "action": "read",
    "points": ["1.0.0.0.0.255", "1.0.1.8.0.255", "1.0.12.7.0.255"]
  },
  "filter_config": {
    "project_id": 1,
    "meter_types": ["DCSP", "DCPP"],
    "line_types": ["3P4W"]
  },
  "priority": 5,
  "retry_times": 3,
  "timeout": 300,
  "is_enabled": true
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 301,
    "task_name": "Coral项目120秒采集",
    "task_type": "interval",
    "status": "ready",
    "next_execute_time": "2026-05-14T10:02:00Z",
    "created_at": "2026-05-14T10:00:00Z"
  }
}
```

#### 5.3.2 任务列表

**请求**:
```http
GET /api/v1/tasks?page=1&page_size=20&status=running
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 301,
        "task_name": "Coral项目120秒采集",
        "task_type": "interval",
        "status": "running",
        "is_enabled": true,
        "last_execute_time": "2026-05-14T10:00:00Z",
        "next_execute_time": "2026-05-14T10:02:00Z",
        "total_devices": 50,
        "success_rate": 98.5
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

#### 5.3.3 立即执行

**请求**:
```http
POST /api/v1/tasks/301/execute
Content-Type: application/json

{
  "device_ids": [123, 124, 125]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "Task execution started",
  "data": {
    "log_id": 401,
    "task_id": 301,
    "status": "running",
    "total_devices": 3,
    "started_at": "2026-05-14T10:00:00Z"
  }
}
```

#### 5.3.4 执行日志

**请求**:
```http
GET /api/v1/tasks/301/logs?page=1&page_size=20
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 401,
        "task_id": 301,
        "start_time": "2026-05-14T10:00:00Z",
        "end_time": "2026-05-14T10:01:30Z",
        "duration_ms": 90000,
        "status": "completed",
        "total_devices": 50,
        "success_devices": 49,
        "failed_devices": 1,
        "created_at": "2026-05-14T10:01:30Z"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 5.4 数据分析 API

#### 5.4.1 每日分析

**请求**:
```http
GET /api/v1/analysis/daily?meter_id=123&date=2026-05-14
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "meter_id": 123,
    "meter_name": "Coral测试表01",
    "analysis_date": "2026-05-14",
    "energy_data": {
      "total_energy": 125.5,
      "daily_increase": 5.2,
      "increase_rate": 4.33
    },
    "clock_status": {
      "is_accurate": true,
      "deviation_seconds": 2
    },
    "profiles": {
      "daily_billing": {
        "expected_count": 48,
        "actual_count": 48,
        "completeness": 100
      },
      "load_profile_1": {
        "expected_count": 144,
        "actual_count": 144,
        "completeness": 100
      }
    },
    "events": {
      "standard": 0,
      "theft": 0,
      "communication": 2,
      "prepayment": 0
    },
    "abnormal_data": [
      {
        "time": "2026-05-14T10:30:00Z",
        "type": "communication",
        "description": "通信超时"
      }
    ]
  }
}
```

### 5.5 测试报告 API

#### 5.5.1 生成测试报告

**请求**:
```http
POST /api/v1/tests/501/report
Content-Type: application/json

{
  "test_type": "stability",
  "test_environment": "实验室常温环境",
  "test_duration_days": 30,
  "firmware_version": "v1.2.0",
  "hardware_version": "v2.0",
  "conclusion": "pass",
  "notes": "测试通过，未发现重大问题"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 601,
    "test_task_id": 501,
    "report_number": "RPT-20260514-001",
    "test_type": "stability",
    "conclusion": "pass",
    "generated_by": 5,
    "generated_at": "2026-05-14T10:00:00Z",
    "defects": [
      {
        "id": 701,
        "severity": "minor",
        "status": "resolved"
      }
    ]
  }
}
```

### 5.6 认证 API

#### 5.6.1 用户登录

**请求**:
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 5,
      "username": "testuser",
      "name": "测试用户",
      "roles": ["project_test_responsible"],
      "permissions": ["meter:read", "task:read"]
    }
  }
}
```

#### 5.6.2 刷新令牌

**请求**:
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

---

## 6. WebSocket 实时推送设计

### 6.1 连接方式

```
客户端连接: ws://localhost:8000/ws
认证方式: ?token={access_token}
```

### 6.2 订阅主题

| 主题 | 说明 | 推送频率 |
|------|------|----------|
| `meter:snapshot` | 设备状态变化 | 状态变化时 |
| `task:progress` | 任务执行进度 | 每5秒或完成时 |
| `alarm:new` | 新告警通知 | 实时 |
| `data:instant` | 实时采集数据 | 采集完成后 |

### 6.3 消息格式

**客户端订阅**:
```json
{
  "action": "subscribe",
  "topics": ["meter:snapshot:123", "task:progress:301"]
}
```

**服务端推送**:
```json
{
  "topic": "meter:snapshot:123",
  "type": "snapshot",
  "data": {
    "meter_id": 123,
    "online_status": true,
    "voltage_a": 220.5,
    "current_a": 5.2,
    "power_a": 1146.6,
    "timestamp": "2026-05-14T10:00:00Z"
  }
}
```

**告警推送**:
```json
{
  "topic": "alarm:new",
  "type": "alarm",
  "data": {
    "alarm_id": 801,
    "meter_id": 123,
    "meter_name": "Coral测试表01",
    "severity": "warning",
    "alarm_type": "communication",
    "message": "设备通信超时",
    "created_at": "2026-05-14T10:00:00Z"
  }
}
```

---

## 7. 数据字典

### 7.1 设备状态枚举

| 状态码 | 状态名称 | 说明 |
|--------|----------|------|
| `in_stock` | 在库 | 样机在库，可用 |
| `testing` | 挂表测试中 | 正在进行挂表测试 |
| `test_complete` | 测试完成待拆 | 测试完成，等待拆表 |
| `borrowed` | 借出 | 样机已借出 |
| `repairing` | 维修中 | 样机正在维修 |
| `scrapped` | 报废 | 样机已报废 |

### 7.2 任务状态枚举

| 状态码 | 状态名称 | 说明 |
|--------|----------|------|
| `ready` | 就绪 | 任务已创建，等待执行 |
| `running` | 执行中 | 任务正在执行 |
| `paused` | 已暂停 | 任务已暂停 |
| `completed` | 已完成 | 任务执行完成 |
| `failed` | 失败 | 任务执行失败 |

### 7.3 任务类型枚举

| 类型码 | 类型名称 | 说明 |
|--------|----------|------|
| `cron` | 定时任务 | 使用Cron表达式 |
| `interval` | 循环任务 | 固定间隔执行 |
| `once` | 一次性任务 | 执行后删除 |

### 7.4 审批状态枚举

| 状态码 | 状态名称 | 说明 |
|--------|----------|------|
| `pending_department` | 待部门审批 | 等待部门负责人审批 |
| `pending_lab` | 待实验室审批 | 部门通过，等待实验室审批 |
| `approved` | 已批准 | 审批通过 |
| `rejected` | 已拒绝 | 审批拒绝 |
| `cancelled` | 已取消 | 申请人取消 |

### 7.5 告警严重程度枚举

| 程度码 | 程度名称 | 说明 |
|--------|----------|------|
| `critical` | 严重 | 需立即处理 |
| `warning` | 警告 | 需要关注 |
| `info` | 信息 | 一般通知 |

---

## 8. 前端设计规范

### 8.1 路由结构（vue-vben-admin）

```
src/
├── router/
│   ├── modules/
│   │   ├── meter.ts        # 设备管理路由
│   │   ├── task.ts         # 采集任务路由
│   │   ├── analysis.ts     # 数据分析路由
│   │   ├── screen.ts       # 大屏展示路由
│   │   ├── test.ts         # 测试报告路由
│   │   └── system.ts       # 系统管理路由
│   └── index.ts
├── views/
│   ├── meter/
│   │   ├── list.vue        # 设备列表
│   │   ├── detail.vue      # 设备详情
│   │   ├── borrow.vue      # 借用管理
│   │   └── repair.vue      # 维修记录
│   ├── task/
│   │   ├── list.vue        # 任务列表
│   │   ├── create.vue      # 创建任务
│   │   ├── logs.vue        # 执行日志
│   │   └── monitor.vue     # 任务监控
│   ├── analysis/
│   │   ├── daily.vue       # 每日分析
│   │   ├── compare.vue     # 对比分析
│   │   └── report.vue      # 分析报告
│   ├── screen/
│   │   ├── overview.vue    # 项目概览大屏
│   │   ├── project.vue     # 项目详情大屏
│   │   └── meter.vue       # 单表监控大屏
│   ├── test/
│   │   ├── list.vue        # 测试列表
│   │   ├── report.vue      # 测试报告
│   │   └── defect.vue      # 缺陷管理
│   └── system/
│       ├── user.vue        # 用户管理
│       ├── role.vue        # 角色管理
│       └── log.vue         # 操作日志
└── components/
    ├── meter/
    │   ├── MeterCard.vue   # 设备卡片
    │   ├── StatusBadge.vue # 状态标签
    │   └── BorrowDialog.vue # 借用弹窗
    └── task/
        ├── TaskProgress.vue # 任务进度
        └── LogTimeline.vue  # 日志时间线
```

### 8.2 权限指令

```typescript
// v-permission 指令使用示例
<template>
  <a-button v-permission="'meter:create'">新增设备</a-button>
  <a-button v-permission="'task:execute'">立即执行</a-button>
</template>
```

### 8.3 状态管理（Pinia）

```typescript
// stores/meter.ts
export const useMeterStore = defineStore('meter', () => {
  const meters = ref<Meter[]>([])
  const currentMeter = ref<Meter | null>(null)
  const loading = ref(false)

  const fetchMeters = async (params: QueryParams) => {
    loading.value = true
    const { data } = await api.getMeters(params)
    meters.value = data.items
    loading.value = false
  }

  return { meters, currentMeter, loading, fetchMeters }
})
```

---

## 9. 用户故事
POST   /api/v1/tests/{id}/defects  # 添加缺陷
PUT    /api/v1/defects/{id}        # 更新缺陷
```

---

## 6. 用户故事

### US-001: 样机入库登记

**作为** 实验室管理员，**我想要** 登记新入库的样机信息，**以便** 系统管理样机资产。

**验收标准**:
- [ ] 支持表单录入样机基本信息
- [ ] 支持上传样机照片
- [ ] 支持批量导入样机
- [ ] 入库后状态为"在库"

---

### US-002: 挂表测试

**作为** 测试工程师，**我想要** 将样机状态变更为"挂表测试中"，**以便** 开始测试。

**验收标准**:
- [ ] 支持选择样机变更状态
- [ ] 记录变更时间
- [ ] 关联测试项目

---

### US-003: 创建采集任务

**作为** 测试工程师，**我想要** 创建定时采集任务，**以便** 自动抄读样机数据。

**验收标准**:
- [ ] 支持选择任务类型（定时/循环/一次性）
- [ ] 支持设置执行时间
- [ ] 支持多维度筛选设备
- [ ] 支持选择执行内容（抄表/升级等）

---

### US-004: 每日数据分析

**作为** 测试负责人，**我想要** 查看每日分析报告，**以便** 了解测试进度和异常。

**验收标准**:
- [ ] 自动生成每日分析报告
- [ ] 显示电能数据变化
- [ ] 显示曲线完整性
- [ ] 标记异常数据
- [ ] 支持导出PDF

---

### US-005: 样机借用

**作为** 研发人员，**我想要** 申请借用样机，**以便** 进行开发调试。

**验收标准**:
- [ ] 支持提交借用申请
- [ ] 支持部门审批
- [ ] 支持实验室审批
- [ ] 审批通过后可借出
- [ ] 支持归还登记

---

### US-006: 生成测试报告

**作为** 测试负责人，**我想要** 生成测试报告，**以便** 总结测试结果。

**验收标准**:
- [ ] 自动填充测试信息
- [ ] 显示缺陷列表
- [ ] 支持手动编辑
- [ ] 支持导出PDF
- [ ] 支持邮件发送

---

### US-007: 大屏监控

**作为** 实验室管理员，**我想要** 在大屏上看到测试概况，**以便** 掌握整体情况。

**验收标准**:
- [ ] 项目概览大屏显示所有项目
- [ ] 实时更新数据
- [ ] 异常项目高亮显示
- [ ] 支持点击跳转详情

---

## 10. 非功能需求

### 7.1 性能要求

| 指标 | 要求 |
|------|------|
| 并发设备 | 500-5000设备 |
| 采集响应 | < 5秒 |
| 大屏刷新 | < 3秒 |
| API响应 | < 500ms (P95) |

### 7.2 可靠性

| 指标 | 要求 |
|------|------|
| 采集成功率 | > 99% |
| 系统可用性 | > 99.5% |
| 数据持久化 | 不丢失 |

### 7.3 安全性

| 要求 | 说明 |
|------|------|
| 认证 | JWT + Token刷新 |
| 授权 | RBAC + 数据权限 |
| 审计 | 操作日志记录 |
| 加密 | 敏感数据加密存储 |

---

## 11. 项目里程碑

| 阶段 | 内容 | 交付物 | 时间估算 |
|------|------|--------|----------|
| Phase 1 | 基础框架 + 权限系统 | 登录、用户管理、RBAC | 2周 |
| Phase 2 | 样机管理 + 借用流程 | 样机CRUD、借用审批 | 3周 |
| Phase 3 | 采集任务系统 | 任务创建、执行、监控 | 4周 |
| Phase 4 | 数据分析 + 大屏 | 每日分析、三种大屏 | 3周 |
| Phase 5 | 测试报告 + 缺陷管理 | 测试报告、缺陷跟踪 | 2周 |

**总计**: 14周（约3.5个月）

### 11.1 Phase 1 依赖

```
Phase 1: 基础框架 + 权限系统
├── 前端
│   ├── vue-vben-admin 初始化
│   ├── 登录页面
│   └── 用户管理页面
└── 后端
    ├── FastAPI 项目初始化
    ├── PostgreSQL 数据库初始化
    ├── JWT 认证
    └── RBAC 权限系统
```

### 11.2 Phase 2 依赖

```
Phase 2: 样机管理 + 借用流程
├── 依赖: Phase 1 完成
├── 前端
│   ├── 设备列表/详情页面
│   ├── 借用申请/审批页面
│   └── 状态流转组件
└── 后端
    ├── 设备 CRUD API
    ├── 状态流转服务
    └── 审批工作流
```

### 11.3 Phase 3 依赖

```
Phase 3: 采集任务系统
├── 依赖: Phase 1 完成
├── 后端
│   ├── Celery 任务调度
│   ├── DLMS/Modbus 协议适配器
│   └── InfluxDB 数据写入
└── 前端
    ├── 任务创建页面
    ├── 任务监控页面
    └── 执行日志页面
```

---

## 12. 风险与挑战

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| DLMS协议复杂 | 开发周期长 | 参考开源库、分阶段实现 |
| 时序数据量大 | 存储性能 | InfluxDB优化、数据降采样 |
| 实时性要求高 | 系统压力 | 异步处理、Redis缓存 |

---

## 13. 附录

### 13.1 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| DLMS/COSEM | Device Language Message Specification | 智能电表国际标准协议 |
| OBIS | Object Identification System | 对象识别系统，用于标识表计数据对象 |
| Modbus | Modbus | 工业通信协议 |
| STS | Standard Transfer Specification | 标准传输规范，用于预付费 |
| CTS | Common Transfer Specification | 通用传输规范 |
| InfluxDB | InfluxDB | 时序数据库 |
| Celery | Celery | Python 分布式任务队列 |
| RBAC | Role-Based Access Control | 基于角色的访问控制 |
| JWT | JSON Web Token | JSON 格式的 Web 令牌 |
| WebSocket | WebSocket | 全双工通信协议 |

### 13.2 参考资料

| 资源 | 链接 |
|------|------|
| DLMS/COSEM 蓝皮书 | https://dlms.com/ |
| vue-vben-admin 文档 | https://doc.vben.pro/ |
| FastAPI 官方文档 | https://fastapi.tiangolo.com/ |
| InfluxDB 文档 | https://docs.influxdata.com/ |
| Celery 文档 | https://docs.celeryq.dev/ |

### 13.3 环境变量配置

```bash
# 后端 .env 配置
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/metering_db
REDIS_URL=redis://localhost:6379/0
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=my-super-secret-token
INFLUXDB_ORG=metering
INFLUXDB_BUCKET=metering

SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# 采集配置
COLLECTOR_MAX_WORKERS=10
COLLECTOR_DEFAULT_TIMEOUT=30
COLLECTOR_RETRY_TIMES=3

# 前端 .env 配置
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

### 13.4 非功能需求测试方案

#### 13.4.1 性能测试

```
工具: Locust / JMeter

测试场景:
1. 5000设备并发采集
   - 模拟5000设备同时采集
   - 目标: 响应时间 < 5秒

2. API 压力测试
   - 模拟1000并发用户
   - 目标: P95响应时间 < 500ms

3. 大屏刷新测试
   - 100个并发用户查看大屏
   - 目标: 刷新时间 < 3秒
```

#### 13.4.2 可靠性测试

```
测试场景:
1. 采集成功率测试
   - 运行24小时
   - 目标: 成功率 > 99%

2. 系统可用性测试
   - 30天持续运行
   - 目标: 可用性 > 99.5%

3. 数据持久化测试
   - 模拟异常断电
   - 验证数据不丢失
```

#### 13.4.3 安全测试

```
测试场景:
1. 认证测试
   - Token 过期处理
   - 刷新 Token 机制

2. 授权测试
   - 跨项目数据访问控制
   - API 权限验证

3. 注入攻击测试
   - SQL 注入防护
   - XSS 防护
```

---

**文档版本**: v1.1
**最后更新**: 2026-05-14
**更新内容**: 补充 API 格式、错误码、数据字典、WebSocket 设计、前端规范
