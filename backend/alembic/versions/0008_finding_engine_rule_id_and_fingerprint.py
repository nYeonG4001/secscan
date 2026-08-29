"""add engine_rule_id, end_line, finding_fingerprint to findings

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("findings", sa.Column("engine_rule_id", sa.String(), nullable=False))
    op.add_column("findings", sa.Column("end_line", sa.Integer(), nullable=True))
    op.add_column("findings", sa.Column("finding_fingerprint", sa.String(), nullable=False))
    op.create_check_constraint(
        "ck_findings_end_line_gte_line",
        "findings",
        "end_line IS NULL OR end_line >= line",
    )
    op.create_check_constraint(
        "ck_findings_severity",
        "findings",
        "severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN')",
    )
    op.create_check_constraint(
        "ck_findings_confidence",
        "findings",
        "confidence IN ('HIGH', 'MEDIUM', 'LOW', 'UNKNOWN')",
    )
    op.create_unique_constraint(
        "uq_findings_analysis_fingerprint",
        "findings",
        ["analysis_id", "finding_fingerprint"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_findings_analysis_fingerprint", "findings", type_="unique")
    op.drop_constraint("ck_findings_confidence", "findings", type_="check")
    op.drop_constraint("ck_findings_severity", "findings", type_="check")
    op.drop_constraint("ck_findings_end_line_gte_line", "findings", type_="check")
    op.drop_column("findings", "finding_fingerprint")
    op.drop_column("findings", "end_line")
    op.drop_column("findings", "engine_rule_id")
