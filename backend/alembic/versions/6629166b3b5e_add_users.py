"""add_users

Revision ID: 6629166b3b5e
Revises: 951aabbdf27e
Create Date: 2026-07-08 13:30:04.794124
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '6629166b3b5e'
down_revision: Union[str, None] = '951aabbdf27e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(256), nullable=False),
        sa.Column('hashed_password', sa.String(256), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.add_column('settings', sa.Column('user_id', sa.Integer(), nullable=True))
    op.drop_constraint('settings_key_key', 'settings', type_='unique')
    op.create_unique_constraint('uq_settings_user_key', 'settings', ['user_id', 'key'])
    op.create_foreign_key('fk_settings_user_id', 'settings', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_settings_user_id', 'settings', type_='foreignkey')
    op.drop_constraint('uq_settings_user_key', 'settings', type_='unique')
    op.create_unique_constraint('settings_key_key', 'settings', ['key'])
    op.drop_column('settings', 'user_id')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
