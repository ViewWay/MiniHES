"""add refresh token table

Revision ID: c4e2a1f9b3d7
Revises: a8f3c2d1e4b5
Create Date: 2026-07-12 00:00:00.000000

Refresh token 持久化表，替代内存 dict 存储。
"""
from alembic import op
import sqlalchemy as sa

revision = "c4e2a1f9b3d7"
down_revision = "a8f3c2d1e4b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sys_refresh_token",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(500), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("revoked", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sys_refresh_token_user_id", "sys_refresh_token", ["user_id"])
    op.create_index("ix_sys_refresh_token_token_hash", "sys_refresh_token", ["token_hash"])
    op.create_index("ix_sys_refresh_token_expires_at", "sys_refresh_token", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_sys_refresh_token_expires_at", table_name="sys_refresh_token")
    op.drop_index("ix_sys_refresh_token_token_hash", table_name="sys_refresh_token")
    op.drop_index("ix_sys_refresh_token_user_id", table_name="sys_refresh_token")
    op.drop_table("sys_refresh_token")
