"""add project description, source, language, and timestamp fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("source_type", sa.String(), nullable=True))
    op.add_column(
        "projects",
        sa.Column("target_languages", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("projects", sa.Column("source_location", sa.String(), nullable=True))
    op.add_column(
        "projects",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_unique_constraint("uq_projects_name", "projects", ["name"])


def downgrade() -> None:
    op.drop_constraint("uq_projects_name", "projects", type_="unique")
    op.drop_column("projects", "updated_at")
    op.drop_column("projects", "source_location")
    op.drop_column("projects", "target_languages")
    op.drop_column("projects", "source_type")
    op.drop_column("projects", "description")
