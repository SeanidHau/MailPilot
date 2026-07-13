"""add email soft delete flag

Revision ID: 8c2d3f4e5b6a
Revises: 7b1e1f0a2c4d
Create Date: 2026-07-13 13:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c2d3f4e5b6a"
down_revision: Union[str, None] = "7b1e1f0a2c4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "emails",
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_emails_is_deleted", "emails", ["is_deleted"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_emails_is_deleted", table_name="emails")
    op.drop_column("emails", "is_deleted")
