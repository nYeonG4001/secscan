"""add E4 analysis source snapshot input and execution log

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("source_location", sa.String(), nullable=True))
    op.add_column("analyses", sa.Column("execution_log", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "execution_log")
    op.drop_column("analyses", "source_location")
