"""allow standalone composed email drafts

Revision ID: 9d4e5f6a7b8c
Revises: 8c2d3f4e5b6a
Create Date: 2026-07-13 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d4e5f6a7b8c"
down_revision: Union[str, None] = "8c2d3f4e5b6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("drafts", "email_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("drafts", sa.Column("recipient", sa.String(length=512), nullable=True))
    op.add_column("drafts", sa.Column("subject", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("drafts", "subject")
    op.drop_column("drafts", "recipient")
    op.alter_column("drafts", "email_id", existing_type=sa.Integer(), nullable=False)
