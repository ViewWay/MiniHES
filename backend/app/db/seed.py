import asyncio
from datetime import datetime, timedelta, timezone

from app.core.database import AsyncSessionLocal as async_session  # noqa: N813
from app.core.database import Base, engine
from app.core.security import get_password_hash
from app.models.alarm import Alarm, AlarmRule
from app.models.meter import (
    Meter,
    MeterType,
    WireType,
)
from app.models.meter_point import MeterPoint
from app.models.project import Project
from app.models.task import Task
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

        # --- Meter Points ---
        session.add_all(
            [
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.0.0.0.255",
                    point_name="正向有功总电能",
                    point_type="register",
                    unit="kWh",
                ),
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.1.8.0.255",
                    point_name="当前需量",
                    point_type="register",
                    unit="kW",
                ),
                MeterPoint(
                    meter_id=1, obis_code="1.0.12.7.0.255", point_name="A相电压", point_type="register", unit="V"
                ),
                MeterPoint(
                    meter_id=1, obis_code="1.0.21.7.0.255", point_name="A相电流", point_type="register", unit="A"
                ),
                MeterPoint(
                    meter_id=1, obis_code="1.0.32.7.0.255", point_name="B相电压", point_type="register", unit="V"
                ),
                MeterPoint(
                    meter_id=1, obis_code="1.0.41.7.0.255", point_name="B相电流", point_type="register", unit="A"
                ),
                MeterPoint(
                    meter_id=1, obis_code="0.0.1.0.0.255", point_name="电表状态", point_type="register", unit=""
                ),
                MeterPoint(meter_id=1, obis_code="1.0.14.7.0.255", point_name="频率", point_type="register", unit="Hz"),
                MeterPoint(
                    meter_id=1, obis_code="1.0.13.7.0.255", point_name="功率因数", point_type="register", unit=""
                ),
                MeterPoint(
                    meter_id=1,
                    obis_code="1.0.1.8.1.255",
                    point_name="正向有功电能(费率1)",
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

        await session.commit()

    import logging

    logging.getLogger(__name__).info("Seed data created successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
