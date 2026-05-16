import asyncio
import random
from datetime import datetime, timedelta, timezone

from app.core.database import AsyncSessionLocal as async_session  # noqa: N813
from app.core.database import Base, engine
from app.core.security import get_password_hash
from app.models.alarm import Alarm, AlarmRule
from app.models.meter import (
    Meter,
    MeterBorrow,
    MeterComm,
    MeterRepair,
    MeterSnapshot,
    MeterStatusHistory,
    MeterType,
    WireType,
)
from app.models.meter_point import MeterPoint, MeterReading, ReadingDailySummary
from app.models.project import Project
from app.models.session import CollectionSession
from app.models.system import AuditLog, DataArchive
from app.models.task import DataQuality, Task, TaskDevice, TaskLog
from app.models.test import TestTask
from app.models.user import Department, Permission, Role, RolePermission, User, UserRole


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # --- Departments ---
        dept_root = Department(name="总部", code="HQ", sort_order=0, leader="管理员")
        dept_rd = Department(name="研发部", code="RD", sort_order=1, leader="王研发", parent_id=1)
        dept_test = Department(name="测试部", code="TEST", sort_order=2, leader="张工程师", parent_id=1)
        session.add_all([dept_root, dept_rd, dept_test])
        await session.flush()

        # --- Permissions ---
        perms = [
            Permission(name="仪表盘", code="dashboard", type="menu", sort_order=0),
            Permission(name="设备管理", code="devices", type="menu", sort_order=1),
            Permission(name="项目管理", code="projects", type="menu", sort_order=2),
            Permission(name="采集任务", code="tasks", type="menu", sort_order=3),
            Permission(name="告警管理", code="alarms", type="menu", sort_order=4),
            Permission(name="数据分析", code="analysis", type="menu", sort_order=5),
            Permission(name="系统管理", code="system", type="menu", sort_order=6),
        ]
        session.add_all(perms)
        await session.flush()

        # --- Roles ---
        role_super = Role(name="超级管理员", code="super", description="系统最高权限", sort_order=0)
        role_admin = Role(name="工程师", code="admin", description="工程管理权限", sort_order=1)
        role_user = Role(name="测试员", code="user", description="基础操作权限", sort_order=2)
        session.add_all([role_super, role_admin, role_user])
        await session.flush()

        for p in perms:
            session.add(RolePermission(role_id=role_super.id, permission_id=p.id))
            session.add(RolePermission(role_id=role_admin.id, permission_id=p.id))
        session.add(RolePermission(role_id=role_user.id, permission_id=perms[0].id))
        session.add(RolePermission(role_id=role_user.id, permission_id=perms[1].id))
        await session.flush()

        # --- Users ---
        users = [
            User(
                username="admin",
                password_hash=get_password_hash("123456"),
                name="超级管理员",
                email="admin@minihes.com",
                phone="13800000001",
                department_id=1,
            ),
            User(
                username="engineer",
                password_hash=get_password_hash("123456"),
                name="张工程师",
                email="engineer@minihes.com",
                phone="13800000002",
                department_id=2,
            ),
            User(
                username="tester",
                password_hash=get_password_hash("123456"),
                name="李测试员",
                email="tester@minihes.com",
                phone="13800000003",
                department_id=3,
            ),
        ]
        session.add_all(users)
        await session.flush()

        session.add_all(
            [
                UserRole(user_id=users[0].id, role_id=role_super.id),
                UserRole(user_id=users[0].id, role_id=role_admin.id),
                UserRole(user_id=users[1].id, role_id=role_admin.id),
                UserRole(user_id=users[2].id, role_id=role_user.id),
            ]
        )
        await session.flush()

        # --- Meter Types ---
        session.add_all(
            [
                MeterType(name="单相电能表", code="single_phase", description="220V 单相电表"),
                MeterType(name="三相四线电能表", code="three_phase_4w", description="3×220/380V 三相四线"),
                MeterType(name="三相三线电能表", code="three_phase_3w", description="3×100V 三相三线"),
            ]
        )
        await session.flush()

        # --- Wire Types ---
        session.add_all(
            [
                WireType(name="单相二线", code="1p2w"),
                WireType(name="三相三线", code="3p3w"),
                WireType(name="三相四线", code="3p4w"),
            ]
        )
        await session.flush()

        # --- Projects ---
        session.add_all(
            [
                Project(
                    name="三相智能电能表型式评价测试",
                    description="某厂商三相表全性能测试",
                    test_lead_id=2,
                    dev_lead_id=2,
                    status="testing",
                ),
                Project(
                    name="单相费控智能表通信协议一致性测试",
                    description="单相表DLMS协议一致性验证",
                    test_lead_id=3,
                    dev_lead_id=2,
                    status="active",
                ),
                Project(
                    name="NB-IoT电表数据采集稳定性测试",
                    description="NB-IoT通信模块长期稳定性",
                    test_lead_id=2,
                    dev_lead_id=2,
                    status="testing",
                ),
                Project(
                    name="红外抄表功能验证",
                    description="红外通信接口功能验证",
                    test_lead_id=3,
                    dev_lead_id=2,
                    status="completed",
                ),
                Project(
                    name="G3-PLC载波通信性能测试",
                    description="电力线载波通信性能测试",
                    test_lead_id=2,
                    dev_lead_id=2,
                    status="active",
                ),
                Project(
                    name="LoRaWAN远传电表通信测试",
                    description="LoRaWAN低功耗广域网抄表测试",
                    test_lead_id=2,
                    dev_lead_id=2,
                    status="active",
                ),
                Project(
                    name="RS485集中抄表系统测试",
                    description="RS485总线集中器+多表位抄表验证",
                    test_lead_id=3,
                    dev_lead_id=2,
                    status="planning",
                ),
                Project(
                    name="DLMS协议安全性评估",
                    description="DLMS/COSEM认证加密安全性测试",
                    test_lead_id=2,
                    dev_lead_id=2,
                    status="testing",
                ),
                Project(
                    name="三相多功能表精度校验",
                    description="三相表计量精度全量程校验",
                    test_lead_id=3,
                    dev_lead_id=2,
                    status="active",
                ),
            ]
        )
        await session.flush()

        # --- Meters ---
        meters_data = [
            Meter(
                serial_number="SM-2024-0001",
                meter_name="三相表#1",
                meter_type_id=2,
                project_id=1,
                line_type="3p4w",
                manufacturer="华立科技",
                model="HL316-3P",
                firmware_version="v2.1.0",
                hardware_version="HW3.0",
                frame_number="FN-001",
                location="A区-01工位",
                current_status="in_use",
            ),
            Meter(
                serial_number="SM-2024-0002",
                meter_name="三相表#2",
                meter_type_id=2,
                project_id=1,
                line_type="3p4w",
                manufacturer="华立科技",
                model="HL316-3P",
                firmware_version="v2.1.0",
                hardware_version="HW3.0",
                frame_number="FN-002",
                location="A区-02工位",
                current_status="in_use",
            ),
            Meter(
                serial_number="SM-2024-0003",
                meter_name="单相表#1",
                meter_type_id=1,
                project_id=2,
                line_type="1p2w",
                manufacturer="威胜集团",
                model="WS-D112",
                firmware_version="v1.3.2",
                hardware_version="HW2.1",
                frame_number="FN-003",
                location="B区-01工位",
                current_status="in_use",
            ),
            Meter(
                serial_number="SM-2024-0004",
                meter_name="NB-IoT表#1",
                meter_type_id=1,
                project_id=3,
                line_type="1p2w",
                manufacturer="海兴电力",
                model="HX-NB01",
                firmware_version="v3.0.1",
                hardware_version="HW1.0",
                frame_number="FN-004",
                location="C区-01工位",
                current_status="online",
                notes="NB-IoT模块",
            ),
            Meter(
                serial_number="SM-2024-0005",
                meter_name="红外表#1",
                meter_type_id=1,
                project_id=4,
                line_type="1p2w",
                manufacturer="许继电气",
                model="XJ-IR200",
                firmware_version="v1.0.5",
                hardware_version="HW1.2",
                frame_number="FN-005",
                location="D区-01工位",
                current_status="returned",
                notes="红外通信",
            ),
            Meter(
                serial_number="SM-2024-0006",
                meter_name="PLC表#1",
                meter_type_id=2,
                project_id=5,
                line_type="3p4w",
                manufacturer="林洋能源",
                model="LY-PLC100",
                firmware_version="v2.5.0",
                hardware_version="HW4.0",
                frame_number="FN-006",
                location="E区-01工位",
                current_status="in_use",
                notes="G3-PLC模块",
            ),
            Meter(
                serial_number="SM-2024-0007",
                meter_name="三相表#3",
                meter_type_id=2,
                project_id=1,
                line_type="3p4w",
                manufacturer="华立科技",
                model="HL316-3P",
                firmware_version="v2.1.0",
                hardware_version="HW3.0",
                frame_number="FN-007",
                location="A区-03工位",
                current_status="offline",
                notes="当前离线",
            ),
            Meter(
                serial_number="SM-2024-0008",
                meter_name="三相表#4",
                meter_type_id=3,
                project_id=1,
                line_type="3p3w",
                manufacturer="威胜集团",
                model="WS-D316",
                firmware_version="v2.0.3",
                hardware_version="HW2.5",
                frame_number="FN-008",
                location="A区-04工位",
                current_status="in_use",
            ),
            Meter(
                serial_number="SM-2024-0009",
                meter_name="单相表#2",
                meter_type_id=1,
                project_id=2,
                line_type="1p2w",
                manufacturer="海兴电力",
                model="HX-D112",
                firmware_version="v1.5.0",
                hardware_version="HW1.8",
                frame_number="FN-009",
                location="B区-02工位",
                current_status="in_use",
            ),
            Meter(
                serial_number="SM-2024-0010",
                meter_name="NB-IoT表#2",
                meter_type_id=1,
                project_id=3,
                line_type="1p2w",
                manufacturer="许继电气",
                model="XJ-NB200",
                firmware_version="v3.1.0",
                hardware_version="HW1.2",
                frame_number="FN-010",
                location="C区-02工位",
                current_status="online",
            ),
            Meter(
                serial_number="SM-2024-0011",
                meter_name="PLC表#2",
                meter_type_id=2,
                project_id=5,
                line_type="3p4w",
                manufacturer="林洋能源",
                model="LY-PLC100",
                firmware_version="v2.5.0",
                hardware_version="HW4.0",
                frame_number="FN-011",
                location="E区-02工位",
                current_status="in_use",
            ),
            Meter(
                serial_number="SM-2024-0012",
                meter_name="维修中表#1",
                meter_type_id=1,
                project_id=1,
                line_type="1p2w",
                manufacturer="华立科技",
                model="HL112",
                firmware_version="v1.2.0",
                hardware_version="HW2.0",
                frame_number="FN-012",
                location="维修室",
                current_status="repairing",
                notes="显示模块故障",
            ),
        ]
        session.add_all(meters_data)
        await session.flush()

        # --- Meter Points (SM meters, simplified) ---
        session.add_all(
            [
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.1.8.0.255",
                    class_id=3,
                    attribute_id=2,
                    point_name="正向有功总电能",
                    module="Energy",
                    point_type="register",
                    unit="kWh",
                ),
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.1.7.0.255",
                    class_id=3,
                    attribute_id=2,
                    point_name="当前需量",
                    module="Instantaneous",
                    point_type="register",
                    unit="W",
                ),
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.32.7.0.255",
                    class_id=3,
                    attribute_id=2,
                    point_name="A相电压",
                    module="Instantaneous",
                    point_type="register",
                    unit="V",
                ),
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.31.7.0.255",
                    class_id=3,
                    attribute_id=2,
                    point_name="A相电流",
                    module="Instantaneous",
                    point_type="register",
                    unit="A",
                ),
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.52.7.0.255",
                    class_id=3,
                    attribute_id=2,
                    point_name="B相电压",
                    module="Instantaneous",
                    point_type="register",
                    unit="V",
                ),
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.51.7.0.255",
                    class_id=3,
                    attribute_id=2,
                    point_name="B相电流",
                    module="Instantaneous",
                    point_type="register",
                    unit="A",
                ),
                MeterPoint(
                    meter_id=1,
                    obis_code="0.0.1.0.0.255",
                    class_id=8,
                    attribute_id=2,
                    point_name="电表时钟",
                    module="Clock",
                    point_type="register",
                    data_type="string",
                    unit="",
                ),
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.14.7.0.255",
                    class_id=3,
                    attribute_id=2,
                    point_name="频率",
                    module="Instantaneous",
                    point_type="register",
                    unit="Hz",
                ),
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.13.7.0.255",
                    class_id=3,
                    attribute_id=2,
                    point_name="功率因数",
                    module="Instantaneous",
                    point_type="register",
                    unit="",
                ),
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.1.8.1.255",
                    class_id=3,
                    attribute_id=2,
                    point_name="正向有功电能(费率1)",
                    module="Energy",
                    point_type="register",
                    unit="kWh",
                ),
            ]
        )
        await session.flush()

        # --- Tasks ---
        session.add_all(
            [
                Task(
                    task_name="三相表每日数据采集",
                    task_type="cron",
                    schedule_config={"cron": "0 8 * * *"},
                    execution_content={"meter_ids": [1, 2, 7, 8], "obis_codes": ["1.0.0.0.0.255"]},
                    filter_config={},
                    priority=1,
                    retry_times=3,
                    timeout=60,
                    is_enabled=True,
                    last_execute_time=datetime.now(timezone.utc),
                    next_execute_time=datetime.now(timezone.utc) + timedelta(days=1),
                ),
                Task(
                    task_name="单相表负荷曲线采集",
                    task_type="interval",
                    schedule_config={"interval_minutes": 30},
                    execution_content={"meter_ids": [3, 9], "obis_codes": ["1.0.1.8.0.255"]},
                    filter_config={},
                    priority=2,
                    retry_times=2,
                    timeout=30,
                    is_enabled=True,
                    last_execute_time=datetime.now(timezone.utc),
                    next_execute_time=datetime.now(timezone.utc) + timedelta(minutes=30),
                ),
                Task(
                    task_name="NB-IoT实时监控",
                    task_type="interval",
                    schedule_config={"interval_minutes": 15},
                    execution_content={"meter_ids": [4, 10], "obis_codes": ["1.0.0.0.0.255"]},
                    filter_config={},
                    priority=1,
                    retry_times=5,
                    timeout=20,
                    is_enabled=True,
                    last_execute_time=datetime.now(timezone.utc),
                    next_execute_time=datetime.now(timezone.utc) + timedelta(minutes=15),
                ),
                Task(
                    task_name="数据一致性分析",
                    task_type="cron",
                    schedule_config={"cron": "0 2 * * *"},
                    execution_content={"analysis_type": "consistency"},
                    filter_config={},
                    priority=3,
                    retry_times=1,
                    timeout=300,
                    is_enabled=True,
                    last_execute_time=datetime.now(timezone.utc),
                    next_execute_time=datetime.now(timezone.utc) + timedelta(days=1),
                ),
                Task(
                    task_name="PLC载波稳定性测试",
                    task_type="cron",
                    schedule_config={"cron": "0 */2 * * *"},
                    execution_content={"meter_ids": [6, 11], "obis_codes": ["1.0.0.0.0.255"]},
                    filter_config={},
                    priority=2,
                    retry_times=3,
                    timeout=45,
                    is_enabled=True,
                    last_execute_time=datetime.now(timezone.utc),
                    next_execute_time=datetime.now(timezone.utc) + timedelta(hours=2),
                ),
                Task(
                    task_name="每周测试报告生成",
                    task_type="cron",
                    schedule_config={"cron": "0 9 * * 1"},
                    execution_content={"report_type": "weekly"},
                    filter_config={"project_ids": [1, 2]},
                    priority=5,
                    retry_times=1,
                    timeout=600,
                    is_enabled=False,
                    last_execute_time=datetime.now(timezone.utc) - timedelta(days=3),
                ),
            ]
        )
        await session.flush()

        # --- Alarm Rules ---
        session.add_all(
            [
                AlarmRule(rule_name="通信超时告警", rule_type="communication", severity="critical", is_enabled=True),
                AlarmRule(
                    rule_name="电压越限告警",
                    rule_type="threshold",
                    point_code="1.0.12.7.0.255",
                    severity="warning",
                    is_enabled=True,
                ),
            ]
        )
        await session.flush()

        # --- Alarms ---
        session.add_all(
            [
                Alarm(
                    meter_id=7, alarm_type="communication", severity="critical", alarm_message="设备持续离线超过30分钟"
                ),
                Alarm(meter_id=12, alarm_type="eeprom", severity="warning", alarm_message="EEPROM校验失败"),
                Alarm(
                    meter_id=1,
                    alarm_type="threshold",
                    severity="warning",
                    alarm_message="相位A电压超过上限阈值",
                    alarm_value=245.8,
                    threshold_value=240.0,
                    is_handled=True,
                ),
                Alarm(
                    meter_id=3,
                    alarm_type="anomaly",
                    severity="info",
                    alarm_message="电流读数突变",
                    alarm_value=15.2,
                    is_handled=True,
                ),
                Alarm(
                    meter_id=2,
                    alarm_type="threshold",
                    severity="critical",
                    alarm_message="总功率超过额定值",
                    alarm_value=12.5,
                    threshold_value=10.0,
                ),
                Alarm(
                    meter_id=4,
                    alarm_type="communication",
                    severity="warning",
                    alarm_message="NB-IoT信号强度低于阈值",
                    alarm_value=-120.0,
                    threshold_value=-110.0,
                ),
                Alarm(
                    meter_id=6,
                    alarm_type="stack",
                    severity="info",
                    alarm_message="PLC载波通信重试次数增加",
                    alarm_value=5.0,
                    threshold_value=3.0,
                    is_handled=True,
                ),
                Alarm(
                    meter_id=8,
                    alarm_type="anomaly",
                    severity="warning",
                    alarm_message="电能计量数据跳变",
                    alarm_value=5.2,
                ),
                Alarm(
                    meter_id=9,
                    alarm_type="threshold",
                    severity="info",
                    alarm_message="当前需量接近上限",
                    alarm_value=8.5,
                    threshold_value=10.0,
                    is_handled=True,
                ),
                Alarm(meter_id=10, alarm_type="communication", severity="critical", alarm_message="数据上报超时"),
            ]
        )
        await session.flush()

        # --- Test Tasks ---
        session.add_all(
            [
                TestTask(
                    test_name="三相表型式评价",
                    test_type="type_approval",
                    project_id=1,
                    status="running",
                    description="三相智能电能表型式评价全性能测试",
                ),
                TestTask(
                    test_name="DLMS协议一致性",
                    test_type="protocol_conformance",
                    project_id=2,
                    status="running",
                    description="DLMS/COSEM协议一致性验证",
                ),
                TestTask(
                    test_name="NB-IoT稳定性",
                    test_type="stability",
                    project_id=3,
                    status="running",
                    description="NB-IoT通信长期稳定性测试",
                ),
                TestTask(
                    test_name="红外抄表功能",
                    test_type="functional",
                    project_id=4,
                    status="completed",
                    description="红外抄表功能验证",
                ),
                TestTask(
                    test_name="PLC性能测试",
                    test_type="performance",
                    project_id=5,
                    status="planned",
                    description="G3-PLC载波通信性能测试",
                ),
            ]
        )
        await session.flush()

        # ========== KFM 电表（匹配 MongoDB 真实数据）==========
        kfm_meters = [
            Meter(
                serial_number="KFM1020110000001",
                meter_name="Puma-01 DCPP #001",
                meter_type_id=2,
                project_id=1,
                line_type="3p4w",
                manufacturer="KFM",
                model="Puma-01",
                firmware_version="v2.1.0",
                hardware_version="HW3.0",
                frame_number="KFM-001",
                location="Puma实验室-01工位",
                current_status="online",
                created_by=1,
            ),
            Meter(
                serial_number="KFM1020110000005",
                meter_name="Puma-01 DCPP #005",
                meter_type_id=2,
                project_id=1,
                line_type="3p4w",
                manufacturer="KFM",
                model="Puma-01",
                firmware_version="v2.1.0",
                hardware_version="HW3.0",
                frame_number="KFM-005",
                location="Puma实验室-05工位",
                current_status="in_stock",
                created_by=1,
            ),
            Meter(
                serial_number="KFM1020110000008",
                meter_name="Puma-01 DCPP #008",
                meter_type_id=2,
                project_id=1,
                line_type="3p4w",
                manufacturer="KFM",
                model="Puma-01",
                firmware_version="v2.1.0",
                hardware_version="HW3.0",
                frame_number="KFM-008",
                location="Puma实验室-08工位",
                current_status="offline",
                created_by=1,
            ),
        ]
        session.add_all(kfm_meters)
        await session.flush()

        # ========== KFM MeterPoints（基于真实 OBIS 抄读清单，83 个测量点） ==========
        obis_template = [
            ("DeviceID", "Device ID", "0.0.96.1.0.255", 1, 2, "string", ""),
            ("LogicalName", "LogicalName", "0.0.42.0.0.255", 1, 2, "string", ""),
            ("Clock", "Time", "0.0.1.0.0.255", 8, 2, "string", ""),
            ("Clock", "Time zone", "0.0.1.0.0.255", 8, 3, "int", ""),
            ("Clock", "Status", "0.0.1.0.0.255", 8, 4, "int", ""),
            ("Clock", "Daylight savings begin", "0.0.1.0.0.255", 8, 5, "string", ""),
            ("Clock", "Daylight savings end", "0.0.1.0.0.255", 8, 6, "string", ""),
            ("Clock", "Daylight savings deviation", "0.0.1.0.0.255", 8, 7, "int", ""),
            ("Clock", "Daylight savings enabled", "0.0.1.0.0.255", 8, 8, "int", ""),
            ("Tariff", "Season profile active", "0.0.13.0.0.255", 20, 3, "string", ""),
            ("Tariff", "Week profile active", "0.0.13.0.0.255", 20, 4, "string", ""),
            ("Tariff", "Day profile active", "0.0.13.0.0.255", 20, 5, "string", ""),
            ("Tariff", "Season profile passive", "0.0.13.0.0.255", 20, 7, "string", ""),
            ("Tariff", "Week profile passive", "0.0.13.0.0.255", 20, 8, "string", ""),
            ("Tariff", "Day profile passive", "0.0.13.0.0.255", 20, 9, "string", ""),
            ("Tariff", "Special Days entries", "0.0.11.0.0.255", 11, 2, "string", ""),
            ("Tariff", "Currently active tariff", "0.0.96.14.0.255", 1, 2, "int", ""),
            ("DisconnectControl", "Output state", "0.0.96.3.10.255", 70, 2, "int", ""),
            ("DisconnectControl", "Control state", "0.0.96.3.10.255", 70, 3, "int", ""),
            ("DisconnectControl", "Relay output state", "0.1.96.3.10.255", 70, 2, "int", ""),
            ("DisconnectControl", "Relay control state", "0.1.96.3.10.255", 70, 3, "int", ""),
            ("DisconnectControl", "Relay2 output state", "0.2.96.3.10.255", 70, 2, "int", ""),
            ("DisconnectControl", "Relay2 control state", "0.2.96.3.10.255", 70, 3, "int", ""),
            ("Energy", "Active energy import", "1.0.1.8.0.255", 3, 2, "numeric", "kWh"),
            ("Energy", "Active energy import scaler_unit", "1.0.1.8.0.255", 3, 3, "string", ""),
            ("Energy", "Active energy export", "1.0.2.8.0.255", 3, 2, "numeric", "kWh"),
            ("Energy", "Active energy export scaler_unit", "1.0.2.8.0.255", 3, 3, "string", ""),
            ("Energy", "Reactive energy import", "1.0.3.8.0.255", 3, 2, "numeric", "kvarh"),
            ("Energy", "Reactive energy export", "1.0.4.8.0.255", 3, 2, "numeric", "kvarh"),
            ("Energy", "Reactive energy QI", "1.0.5.8.0.255", 3, 2, "numeric", "kvarh"),
            ("Energy", "Reactive energy QII", "1.0.6.8.0.255", 3, 2, "numeric", "kvarh"),
            ("Energy", "Reactive energy QIII", "1.0.7.8.0.255", 3, 2, "numeric", "kvarh"),
            ("Energy", "Reactive energy QIV", "1.0.8.8.0.255", 3, 2, "numeric", "kvarh"),
            ("Energy", "Absolute energy |+A|+|-A|", "1.0.15.8.0.255", 3, 2, "numeric", "kWh"),
            ("Energy", "Net energy |+A|-|-A|", "1.0.16.8.0.255", 3, 2, "numeric", "kWh"),
            *[("Energy", f"Active import rate {r}", f"1.0.1.8.{r}.255", 3, 2, "numeric", "kWh") for r in range(1, 7)],
            *[("Energy", f"Active export rate {r}", f"1.0.2.8.{r}.255", 3, 2, "numeric", "kWh") for r in range(1, 7)],
            ("Instantaneous", "Voltage L1", "1.0.32.7.0.255", 3, 2, "numeric", "V"),
            ("Instantaneous", "Voltage L2", "1.0.52.7.0.255", 3, 2, "numeric", "V"),
            ("Instantaneous", "Voltage L3", "1.0.72.7.0.255", 3, 2, "numeric", "V"),
            ("Instantaneous", "Current L1", "1.0.31.7.0.255", 3, 2, "numeric", "A"),
            ("Instantaneous", "Current L2", "1.0.51.7.0.255", 3, 2, "numeric", "A"),
            ("Instantaneous", "Current L3", "1.0.71.7.0.255", 3, 2, "numeric", "A"),
            ("Instantaneous", "Active import power", "1.0.1.7.0.255", 3, 2, "numeric", "W"),
            ("Instantaneous", "Active import power L1", "1.0.21.7.0.255", 3, 2, "numeric", "W"),
            ("Instantaneous", "Active import power L2", "1.0.41.7.0.255", 3, 2, "numeric", "W"),
            ("Instantaneous", "Active import power L3", "1.0.61.7.0.255", 3, 2, "numeric", "W"),
            ("Instantaneous", "Active export power", "1.0.2.7.0.255", 3, 2, "numeric", "W"),
            ("Instantaneous", "Reactive import power", "1.0.3.7.0.255", 3, 2, "numeric", "var"),
            ("Instantaneous", "Reactive export power", "1.0.4.7.0.255", 3, 2, "numeric", "var"),
            ("Instantaneous", "Apparent import power", "1.0.9.7.0.255", 3, 2, "numeric", "VA"),
            ("Instantaneous", "Apparent export power", "1.0.10.7.0.255", 3, 2, "numeric", "VA"),
            ("Instantaneous", "Power Factor", "1.0.13.7.0.255", 3, 2, "numeric", ""),
            ("Instantaneous", "Power Factor L1", "1.0.33.7.0.255", 3, 2, "numeric", ""),
            ("Instantaneous", "Frequency", "1.0.14.7.0.255", 3, 2, "numeric", "Hz"),
            ("Instantaneous", "Phase Angle U(L1)-I(L1)", "1.0.81.7.40.255", 3, 2, "numeric", "deg"),
            ("Instantaneous", "Battery Voltage", "0.0.96.6.3.255", 3, 2, "numeric", "V"),
            ("Status", "Error register", "0.0.97.97.0.255", 1, 2, "string", ""),
            ("Status", "Alarm register 1", "0.0.97.98.0.255", 1, 2, "string", ""),
            ("Status", "Alarm register 2", "0.0.97.98.1.255", 1, 2, "string", ""),
            ("Event", "Standard Event Log buffer", "0.0.99.98.0.255", 7, 2, "string", ""),
            ("Event", "Fraud Event Log buffer", "0.0.99.98.1.255", 7, 2, "string", ""),
            ("Event", "Communication Event Log buffer", "0.0.99.98.5.255", 7, 2, "string", ""),
            ("Event", "Quality Event Log buffer", "0.0.99.98.4.255", 7, 2, "string", ""),
            ("LoadProfile1", "Load profile 1 buffer", "1.0.99.1.0.255", 7, 2, "string", ""),
            ("LoadProfile1", "Load profile 1 period", "1.0.99.1.0.255", 7, 4, "int", "min"),
            ("LoadProfile2", "Load profile 2 buffer", "1.0.99.2.0.255", 7, 2, "string", ""),
            ("LoadProfile2", "Load profile 2 period", "1.0.99.2.0.255", 7, 4, "int", "min"),
            ("DailyBilling", "Daily Billing buffer", "0.0.98.2.0.255", 7, 2, "string", ""),
            ("MonthlyBilling", "Monthly Billing buffer", "0.0.98.1.0.255", 7, 2, "string", ""),
            ("GSM", "CSQ", "0.1.94.31.6.255", 1, 2, "int", ""),
            ("GSM", "RSRP", "0.1.94.31.7.255", 1, 2, "int", "dBm"),
            ("GSM", "SNR", "0.1.94.31.10.255", 1, 2, "numeric", "dB"),
        ]

        kfm_points = []
        for mid in [kfm_meters[0].id, kfm_meters[1].id, kfm_meters[2].id]:
            for module, name, obis, cls_id, attr_id, dtype, unit in obis_template:
                kfm_points.append(
                    MeterPoint(
                        meter_id=mid,
                        obis_code=obis,
                        class_id=cls_id,
                        attribute_id=attr_id,
                        point_name=name,
                        module=module,
                        point_type="register" if cls_id in (1, 3, 8, 20, 47, 70) else "profile",
                        data_type=dtype,
                        unit=unit,
                        is_collectible=True,
                    )
                )
        session.add_all(kfm_points)
        await session.flush()

        # ========== MeterComm / MeterSnapshot / MeterStatusHistory ==========
        session.add_all(
            [
                MeterComm(
                    meter_id=kfm_meters[0].id,
                    protocol="DLMS",
                    connection_type="tcp",
                    host="192.168.234.101",
                    port=4059,
                    is_enabled=True,
                ),
                MeterComm(
                    meter_id=kfm_meters[1].id,
                    protocol="DLMS",
                    connection_type="tcp",
                    host="192.168.234.105",
                    port=4059,
                    is_enabled=True,
                ),
                MeterComm(
                    meter_id=1, protocol="DLMS", connection_type="tcp", host="192.168.234.1", port=4059, is_enabled=True
                ),
                MeterComm(
                    meter_id=4, protocol="DLMS", connection_type="tcp", host="192.168.234.4", port=4059, is_enabled=True
                ),
            ]
        )
        await session.flush()

        session.add_all(
            [
                MeterSnapshot(
                    meter_id=kfm_meters[0].id,
                    online_status=True,
                    signal_strength=-65,
                    firmware_version="v2.1.0",
                    error_code="",
                    stack_usage=2048,
                    eeprom_write_count=1523,
                    last_comm_time=datetime.now(timezone.utc) - timedelta(minutes=5),
                    last_data_time=datetime.now(timezone.utc) - timedelta(minutes=5),
                ),
                MeterSnapshot(meter_id=kfm_meters[1].id, online_status=False, firmware_version="v2.1.0", error_code=""),
                MeterSnapshot(
                    meter_id=1,
                    online_status=True,
                    signal_strength=-72,
                    firmware_version="v2.1.0",
                    error_code="",
                    last_comm_time=datetime.now(timezone.utc) - timedelta(minutes=2),
                    last_data_time=datetime.now(timezone.utc) - timedelta(minutes=2),
                ),
                MeterSnapshot(
                    meter_id=4,
                    online_status=True,
                    signal_strength=-85,
                    firmware_version="v3.0.1",
                    error_code="",
                    last_comm_time=datetime.now(timezone.utc) - timedelta(minutes=1),
                ),
            ]
        )
        await session.flush()

        now = datetime.now(timezone.utc)
        session.add_all(
            [
                MeterStatusHistory(
                    meter_id=kfm_meters[0].id,
                    old_status="in_stock",
                    new_status="online",
                    reason="设备上线",
                    changed_by=1,
                    created_at=now - timedelta(days=10),
                ),
                MeterStatusHistory(
                    meter_id=kfm_meters[2].id,
                    old_status="online",
                    new_status="offline",
                    reason="通信超时",
                    changed_by=2,
                    created_at=now - timedelta(days=2),
                ),
                MeterStatusHistory(
                    meter_id=12,
                    old_status="in_use",
                    new_status="repairing",
                    reason="显示模块故障",
                    changed_by=2,
                    created_at=now - timedelta(days=5),
                ),
            ]
        )
        await session.flush()

        # ========== CollectionSession（PG-MongoDB 桥梁）==========
        base_time = datetime(2025, 11, 1, 9, 33, 0, tzinfo=timezone.utc)
        sessions = [
            CollectionSession(
                meter_id=kfm_meters[0].id,
                project_id=1,
                task_id=1,
                mongo_db="Puma-01_DCPP_DailyCheck",
                mongo_collection="KFM1020110000001",
                mongo_doc_id="6985f99d01de8a5162785ca4",
                source="auto",
                source_file="XMLFunctionLists_Meter_PP.xlsx",
                started_at=base_time,
                finished_at=base_time + timedelta(minutes=3, seconds=12),
                duration_ms=192000,
                status="completed",
                total_read=796,
                total_success=796,
                total_failed=0,
                sheet_count=24,
                connection_type="TCP",
                communication="4G",
                meter_ip="192.168.234.101",
                ping_status=True,
            ),
            CollectionSession(
                meter_id=kfm_meters[0].id,
                project_id=1,
                task_id=1,
                mongo_db="Puma-01_DCPP_DailyCheck",
                mongo_collection="KFM1020110000001",
                mongo_doc_id="2025-11-02 08:00:12.345678",
                source="auto",
                started_at=base_time + timedelta(days=1),
                finished_at=base_time + timedelta(days=1, minutes=3, seconds=5),
                duration_ms=185000,
                status="completed",
                total_read=796,
                total_success=794,
                total_failed=2,
                sheet_count=24,
                connection_type="TCP",
                communication="4G",
                meter_ip="192.168.234.101",
                ping_status=True,
                error_summary="Load Profile partial timeout, Definable Load Profile failed",
            ),
            CollectionSession(
                meter_id=kfm_meters[1].id,
                project_id=1,
                task_id=1,
                mongo_db="Puma-01_DCPP_DailyCheck",
                mongo_collection="KFM1020110000005",
                mongo_doc_id="2025-11-01 09:35:00.123456",
                source="auto",
                started_at=base_time + timedelta(seconds=30),
                finished_at=base_time + timedelta(seconds=35),
                duration_ms=5000,
                status="failed",
                total_read=0,
                total_success=0,
                total_failed=1,
                sheet_count=0,
                connection_type="TCP",
                communication="4G",
                meter_ip="192.168.234.105",
                ping_status=False,
                error_summary="Connection refused: unable to connect to meter",
            ),
        ]
        # 最近 7 天每天一条 session
        for day_offset in range(7):
            t = now - timedelta(days=day_offset, hours=random.randint(7, 10))
            sessions.append(
                CollectionSession(
                    meter_id=kfm_meters[0].id,
                    project_id=1,
                    mongo_db="Puma-01_DCPP_DailyCheck",
                    mongo_collection="KFM1020110000001",
                    mongo_doc_id=f"session_day{day_offset}",
                    source="auto",
                    started_at=t,
                    finished_at=t + timedelta(minutes=random.randint(2, 4)),
                    duration_ms=random.randint(120000, 240000),
                    status="completed",
                    total_read=796,
                    total_success=random.randint(790, 796),
                    total_failed=random.randint(0, 6),
                    sheet_count=24,
                    connection_type="TCP",
                    communication="4G",
                    meter_ip="192.168.234.101",
                    ping_status=True,
                )
            )
        session.add_all(sessions)
        await session.flush()

        # ========== TaskLog + TaskDevice ==========
        for task_id_val in [1, 2, 3, 5]:
            for day_offset in range(3):
                t = now - timedelta(days=day_offset, hours=random.randint(6, 9))
                log = TaskLog(
                    task_id=task_id_val,
                    start_time=t,
                    end_time=t + timedelta(seconds=random.randint(15, 60)),
                    duration_ms=random.randint(15000, 60000),
                    status="completed",
                    total_devices=random.randint(2, 5),
                    success_devices=random.randint(2, 5),
                    failed_devices=random.randint(0, 1),
                )
                session.add(log)
                await session.flush()

                for mid in random.sample([1, 2, 3, 4, kfm_meters[0].id, kfm_meters[1].id], k=min(3, 6)):
                    session.add(
                        TaskDevice(
                            log_id=log.id,
                            task_id=task_id_val,
                            meter_id=mid,
                            status="success",
                            data_count=random.randint(10, 30),
                            start_time=t + timedelta(seconds=random.randint(1, 5)),
                            end_time=t + timedelta(seconds=random.randint(6, 15)),
                            duration_ms=random.randint(3000, 12000),
                        )
                    )
                await session.flush()

        # ========== MeterReadings（KFM 电表 + SM 电表） ==========
        point_energy = kfm_points[1]  # Cumulative A Positive for KFM #001
        point_voltage = kfm_points[8]  # Voltage L1 for KFM #001
        base_kwh = 40163

        for day_offset in range(14):
            t = now - timedelta(days=day_offset, hours=random.randint(7, 10))
            base_kwh += random.randint(5, 20)
            session.add(
                MeterReading(
                    meter_id=kfm_meters[0].id,
                    point_id=point_energy.id,
                    task_id=1,
                    reading_value=float(base_kwh),
                    reading_time=t,
                    quality="good",
                    source="auto",
                )
            )
            session.add(
                MeterReading(
                    meter_id=kfm_meters[0].id,
                    point_id=point_voltage.id,
                    task_id=1,
                    reading_value=round(random.uniform(218, 242), 2),
                    reading_time=t,
                    quality="good",
                    source="auto",
                )
            )
        await session.flush()

        # SM 表读数
        for mid in [1, 2, 3, 4, 6]:
            pid = 1 if mid <= 10 else 10  # meter_point id
            for day_offset in range(7):
                t = now - timedelta(days=day_offset, hours=random.randint(7, 10))
                session.add(
                    MeterReading(
                        meter_id=mid,
                        point_id=pid,
                        task_id=1,
                        reading_value=round(random.uniform(1000, 50000), 2),
                        reading_time=t,
                        quality="good" if random.random() > 0.1 else "suspect",
                        source="auto",
                    )
                )
        await session.flush()

        # ========== ReadingDailySummary ==========
        for day_offset in range(7):
            d = (now - timedelta(days=day_offset)).date()
            for mid in [kfm_meters[0].id, 1, 2, 3, 4]:
                pid = kfm_points[1].id if mid == kfm_meters[0].id else 1
                v = round(random.uniform(100, 500), 2)
                session.add(
                    ReadingDailySummary(
                        meter_id=mid,
                        point_id=pid,
                        stat_date=d,
                        min_value=v - random.uniform(10, 30),
                        max_value=v + random.uniform(10, 30),
                        avg_value=v,
                        first_value=v - 5,
                        last_value=v + 5,
                        reading_count=random.randint(20, 48),
                        delta=round(random.uniform(5, 20), 2),
                    )
                )
        await session.flush()

        # ========== DataQuality ==========
        for day_offset in range(7):
            d = (now - timedelta(days=day_offset)).date()
            for mid in [kfm_meters[0].id, 1, 2, 3, 4]:
                total = random.randint(50, 100)
                success = total - random.randint(0, 5)
                session.add(
                    DataQuality(
                        meter_id=mid,
                        task_id=1,
                        stat_date=d,
                        total_points=total,
                        success_points=success,
                        failed_points=total - success,
                        quality_score=round(random.uniform(90, 100), 2),
                        abnormal_count=random.randint(0, 3),
                        first_collect_time=datetime.now(timezone.utc) - timedelta(days=day_offset, hours=8),
                        last_collect_time=datetime.now(timezone.utc) - timedelta(days=day_offset, hours=7),
                    )
                )
        await session.flush()

        # ========== MeterBorrow + MeterRepair ==========
        session.add_all(
            [
                MeterBorrow(
                    meter_id=kfm_meters[1].id,
                    borrower_id=2,
                    borrow_reason="协议一致性测试",
                    approval_status="approved_lab",
                    dept_approver_id=1,
                    lab_approver_id=1,
                ),
                MeterBorrow(
                    meter_id=12, borrower_id=3, borrow_reason="模块更换后验证", approval_status="pending_department"
                ),
                MeterRepair(
                    meter_id=12, description="显示模块故障，更换LCD", cost=150.00, status="in_progress", repaired_by=2
                ),
                MeterRepair(
                    meter_id=5, description="红外通信口氧化清理", cost=30.00, status="completed", repaired_by=2
                ),
            ]
        )
        await session.flush()

        # ========== AuditLog ==========
        session.add_all(
            [
                AuditLog(
                    user_id=1,
                    username="admin",
                    operation_type="LOGIN",
                    resource_type="system",
                    resource_id=0,
                    ip_address="192.168.234.1",
                    user_agent="Chrome/120",
                ),
                AuditLog(
                    user_id=1,
                    username="admin",
                    operation_type="CREATE",
                    resource_type="meter",
                    resource_id=1,
                    ip_address="192.168.234.1",
                    user_agent="Chrome/120",
                    new_values={"serial_number": "KFM1020110000001", "meter_name": "Puma-01 DCPP #001"},
                ),
                AuditLog(
                    user_id=2,
                    username="engineer",
                    operation_type="CREATE",
                    resource_type="task",
                    resource_id=1,
                    ip_address="192.168.234.2",
                    user_agent="Chrome/120",
                    new_values={"task_name": "三相表每日数据采集"},
                ),
                AuditLog(
                    user_id=2,
                    username="engineer",
                    operation_type="UPDATE",
                    resource_type="meter",
                    resource_id=12,
                    ip_address="192.168.234.2",
                    user_agent="Chrome/120",
                    old_values={"current_status": "in_use"},
                    new_values={"current_status": "repairing"},
                ),
                AuditLog(
                    user_id=3,
                    username="tester",
                    operation_type="CREATE",
                    resource_type="borrow",
                    resource_id=1,
                    ip_address="192.168.234.3",
                    user_agent="Chrome/120",
                ),
                AuditLog(
                    user_id=1,
                    username="admin",
                    operation_type="LOGIN",
                    resource_type="system",
                    resource_id=0,
                    ip_address="192.168.234.1",
                    user_agent="Chrome/120",
                    created_at=now - timedelta(hours=2),
                ),
                AuditLog(
                    user_id=2,
                    username="engineer",
                    operation_type="LOGIN",
                    resource_type="system",
                    resource_id=0,
                    ip_address="192.168.234.2",
                    user_agent="Chrome/120",
                    created_at=now - timedelta(hours=1),
                ),
            ]
        )
        await session.flush()

        # ========== DataArchive ==========
        session.add_all(
            [
                DataArchive(
                    archive_type="postgresql",
                    table_name="col_meter_reading",
                    start_time=now - timedelta(days=90),
                    end_time=now - timedelta(days=60),
                    record_count=15420,
                    archive_status="completed",
                ),
                DataArchive(
                    archive_type="postgresql",
                    table_name="sys_audit_log",
                    start_time=now - timedelta(days=180),
                    end_time=now - timedelta(days=90),
                    record_count=3842,
                    archive_status="completed",
                ),
            ]
        )

        await session.commit()

    import logging

    logging.getLogger(__name__).info("Seed data created successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
