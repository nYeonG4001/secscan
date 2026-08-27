"""add analysis engine, language snapshot, error, and summary fields

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("engine", sa.String(), nullable=True))
    op.add_column(
        "analyses",
        sa.Column("analyzed_languages", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "analyses", sa.Column("source_snapshot_location", sa.String(), nullable=True)
    )
    op.add_column("analyses", sa.Column("error_code", sa.String(), nullable=True))
    op.add_column(
        "analyses",
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_check_constraint(
        "ck_analyses_status",
        "analyses",
        "status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')",
    )
    # DAR-005 decision: at most one PENDING/RUNNING analysis per project.
    op.create_index(
        "uq_analyses_project_active",
        "analyses",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'RUNNING')"),
    )


def downgrade() -> None:
    op.drop_index("uq_analyses_project_active", table_name="analyses")
    op.drop_constraint("ck_analyses_status", "analyses", type_="check")
    op.drop_column("analyses", "summary")
    op.drop_column("analyses", "error_code")
    op.drop_column("analyses", "source_snapshot_location")
    op.drop_column("analyses", "analyzed_languages")
    op.drop_column("analyses", "engine")
