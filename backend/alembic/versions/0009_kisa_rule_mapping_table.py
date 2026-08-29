"""add KISA_RULE_MAPPING table

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kisa_rule_mapping",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engine", sa.String(), nullable=False),
        sa.Column("engine_rule_id", sa.String(), nullable=False),
        sa.Column(
            "kisa_code",
            sa.String(),
            sa.ForeignKey("kisa_catalog.kisa_code"),
            nullable=False,
        ),
        sa.UniqueConstraint("engine", "engine_rule_id", name="uq_kisa_rule_mapping_engine_rule"),
    )


def downgrade() -> None:
    op.drop_table("kisa_rule_mapping")
