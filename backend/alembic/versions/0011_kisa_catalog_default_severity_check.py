"""add default_severity CHECK constraint to kisa_catalog

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-28
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_kisa_catalog_default_severity",
        "kisa_catalog",
        "default_severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_kisa_catalog_default_severity", "kisa_catalog", type_="check")
