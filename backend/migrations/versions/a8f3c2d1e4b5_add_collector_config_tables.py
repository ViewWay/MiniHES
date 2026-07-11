"""add collector config tables (obis_template, data_point_template, task_obis_override)

Revision ID: a8f3c2d1e4b5
Revises: 14399098fe8c
Create Date: 2026-07-09 22:00:00.000000

新增采集配置建模（设计文档 docs/design/collector-config-model.md）：
  - obis_template: 数据点模板表
  - data_point_template: 模板明细（统一表 + JSONB 协议参数）
  - task_obis_override: 任务数据点覆盖表
  - col_task: 新增 device_type/task_category/obis_template_id
  - dev_meter_comm: 新增 pos/meter_mac/keys/comm_layer 等连接参数
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a8f3c2d1e4b5"
down_revision: Union[str, Sequence[str], None] = "14399098fe8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ============================================================
    # 1. obis_template — 数据点模板表
    # ============================================================
    op.create_table(
        "obis_template",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("device_type", sa.String(length=30), nullable=False),
        sa.Column("task_category", sa.String(length=30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "version", name="uq_obis_template_name_version"),
        comment="数据点模板表",
    )

    # ============================================================
    # 2. data_point_template — 模板明细（统一表 + JSONB）
    # ============================================================
    op.create_table(
        "data_point_template",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "template_id",
            sa.Integer(),
            sa.ForeignKey("obis_template.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("device_type", sa.String(length=30), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=True),
        sa.Column("point_name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.String(length=60), nullable=False),
        sa.Column("data_type", sa.String(length=20), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("scaler", sa.Integer(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column(
            "protocol_params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "template_id",
            "address",
            "sort_order",
            name="uq_dpt_template_addr_order",
        ),
        comment="数据点模板明细表",
    )
    op.create_index("ix_dpt_template", "data_point_template", ["template_id"])
    op.create_index("ix_dpt_device_type", "data_point_template", ["device_type"])

    # ============================================================
    # 3. task_obis_override — 任务数据点覆盖表
    # ============================================================
    op.create_table(
        "task_obis_override",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("col_task.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "template_item_id",
            sa.Integer(),
            sa.ForeignKey("data_point_template.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_selected", sa.Boolean(), nullable=True),
        sa.Column(
            "custom_params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "task_id", "template_item_id", name="uq_task_override_item"
        ),
        comment="任务数据点覆盖表",
    )
    op.create_index("ix_task_override_task", "task_obis_override", ["task_id"])

    # ============================================================
    # 4. col_task — 新增字段（向后兼容，全部有默认值）
    # ============================================================
    op.add_column(
        "col_task",
        sa.Column(
            "device_type",
            sa.String(length=30),
            nullable=False,
            server_default="electric_meter",
        ),
    )
    op.add_column(
        "col_task",
        sa.Column(
            "task_category",
            sa.String(length=30),
            nullable=False,
            server_default="metering",
        ),
    )
    op.add_column(
        "col_task",
        sa.Column(
            "obis_template_id",
            sa.Integer(),
            sa.ForeignKey("obis_template.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ============================================================
    # 5. dev_meter_comm — 新增连接参数字段
    # ============================================================
    op.add_column(
        "dev_meter_comm",
        sa.Column(
            "device_type",
            sa.String(length=30),
            nullable=False,
            server_default="electric_meter",
        ),
    )
    op.add_column("dev_meter_comm", sa.Column("pos", sa.Integer(), nullable=True))
    op.add_column(
        "dev_meter_comm", sa.Column("meter_mac", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "dev_meter_comm", sa.Column("src_wport", sa.Integer(), nullable=True)
    )
    op.add_column(
        "dev_meter_comm", sa.Column("dst_wport", sa.Integer(), nullable=True)
    )
    op.add_column(
        "dev_meter_comm", sa.Column("lls_key", sa.String(length=200), nullable=True)
    )
    op.add_column(
        "dev_meter_comm", sa.Column("hls_key", sa.String(length=200), nullable=True)
    )
    op.add_column(
        "dev_meter_comm",
        sa.Column(
            "comm_layer",
            sa.String(length=10),
            nullable=False,
            server_default="HDLC",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # dev_meter_comm
    op.drop_column("dev_meter_comm", "comm_layer")
    op.drop_column("dev_meter_comm", "hls_key")
    op.drop_column("dev_meter_comm", "lls_key")
    op.drop_column("dev_meter_comm", "dst_wport")
    op.drop_column("dev_meter_comm", "src_wport")
    op.drop_column("dev_meter_comm", "meter_mac")
    op.drop_column("dev_meter_comm", "pos")
    op.drop_column("dev_meter_comm", "device_type")

    # col_task
    op.drop_constraint(
        "col_task_obis_template_id_fkey", "col_task", type_="foreignkey"
    )
    op.drop_column("col_task", "obis_template_id")
    op.drop_column("col_task", "task_category")
    op.drop_column("col_task", "device_type")

    # task_obis_override
    op.drop_index("ix_task_override_task", table_name="task_obis_override")
    op.drop_table("task_obis_override")

    # data_point_template
    op.drop_index("ix_dpt_device_type", table_name="data_point_template")
    op.drop_index("ix_dpt_template", table_name="data_point_template")
    op.drop_table("data_point_template")

    # obis_template
    op.drop_table("obis_template")
