"""add kisa_catalog item_number, reference_info, active, and 3-tier status

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("kisa_catalog", sa.Column("item_number", sa.Integer(), nullable=True))
    op.add_column("kisa_catalog", sa.Column("reference_info", sa.Text(), nullable=True))
    op.add_column(
        "kisa_catalog",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    # ADR-011: implementation_status moves from a 구현/미구현 binary to a
    # 지원/부분 지원/미지원 three-tier scale. Remap any existing rows before
    # the check constraint goes on so an old value can't violate it.
    op.execute("UPDATE kisa_catalog SET implementation_status = '지원' WHERE implementation_status = '구현'")
    op.execute(
        "UPDATE kisa_catalog SET implementation_status = '미지원' WHERE implementation_status = '미구현'"
    )
    op.alter_column("kisa_catalog", "implementation_status", server_default="미지원")
    op.create_check_constraint(
        "ck_kisa_catalog_implementation_status",
        "kisa_catalog",
        "implementation_status IN ('지원', '부분 지원', '미지원')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_kisa_catalog_implementation_status", "kisa_catalog", type_="check")
    op.alter_column("kisa_catalog", "implementation_status", server_default="미구현")
    op.execute(
        "UPDATE kisa_catalog SET implementation_status = '미구현' "
        "WHERE implementation_status IN ('부분 지원', '미지원')"
    )
    op.execute("UPDATE kisa_catalog SET implementation_status = '구현' WHERE implementation_status = '지원'")

    op.drop_column("kisa_catalog", "active")
    op.drop_column("kisa_catalog", "reference_info")
    op.drop_column("kisa_catalog", "item_number")
