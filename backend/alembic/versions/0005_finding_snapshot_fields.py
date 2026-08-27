"""add finding snapshot fields and minimal kisa_catalog snapshot sources

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # E1-06 finalizes the full catalog field set; these two are added now only
    # because Finding needs a source to snapshot from (ADR-005, ADR-007).
    op.add_column("kisa_catalog", sa.Column("criterion_id", sa.String(), nullable=True))
    op.add_column("kisa_catalog", sa.Column("recommendation", sa.Text(), nullable=True))

    op.add_column("findings", sa.Column("criterion_id", sa.String(), nullable=True))
    op.add_column("findings", sa.Column("evidence", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("recommendation", sa.Text(), nullable=True))
    op.add_column(
        "findings",
        sa.Column("raw_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("findings", "raw_result")
    op.drop_column("findings", "recommendation")
    op.drop_column("findings", "evidence")
    op.drop_column("findings", "criterion_id")

    op.drop_column("kisa_catalog", "recommendation")
    op.drop_column("kisa_catalog", "criterion_id")
