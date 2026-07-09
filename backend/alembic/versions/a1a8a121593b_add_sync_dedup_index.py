"""add_sync_dedup_index

Revision ID: a1a8a121593b
Revises: c320c152a427
Create Date: 2026-07-09 10:30:02.932353
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1a8a121593b'
down_revision: Union[str, None] = 'c320c152a427'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_emails_provider_dedup',
        'emails',
        ['user_id', 'provider', 'provider_message_id'],
        unique=True,
        postgresql_where=sa.text("provider IS NOT NULL AND provider_message_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index('ix_emails_provider_dedup', table_name='emails')
