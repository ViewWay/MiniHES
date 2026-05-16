import pytest
from sqlalchemy import inspect

# Import all models so Base.metadata knows about them
import app.models.user  # noqa: F401
import app.models.project  # noqa: F401
import app.models.meter  # noqa: F401
import app.models.meter_point  # noqa: F401
import app.models.alarm  # noqa: F401
import app.models.task  # noqa: F401
import app.models.test  # noqa: F401
import app.models.system  # noqa: F401


@pytest.mark.asyncio
async def test_all_models_have_tables(db_engine):
    async with db_engine.connect() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
    expected = [
        "sys_user", "sys_role", "sys_user_role", "sys_role_permission",
        "sys_permission", "sys_department",
        "dev_project", "dev_meter", "dev_meter_type", "dev_wire_type",
        "col_task", "col_task_log", "col_task_device",
        "sys_alarm_record", "sys_alarm_rule",
        "lab_test_task", "lab_defect", "lab_test_report",
        "sys_audit_log", "sys_data_archive",
    ]
    for t in expected:
        assert t in tables, f"Missing table: {t}"
