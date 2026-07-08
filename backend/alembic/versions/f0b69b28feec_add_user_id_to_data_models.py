"""add_user_id_to_data_models

Revision ID: f0b69b28feec
Revises: 6629166b3b5e
Create Date: 2026-07-08 14:41:48.849134
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f0b69b28feec'
down_revision: Union[str, None] = '6629166b3b5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('classification_feedback', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_classification_feedback_user_id'), 'classification_feedback', ['user_id'], unique=False)
    op.create_foreign_key('fk_classification_feedback_user_id', 'classification_feedback', 'users', ['user_id'], ['id'])

    op.add_column('drafts', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_drafts_user_id'), 'drafts', ['user_id'], unique=False)
    op.create_foreign_key('fk_drafts_user_id', 'drafts', 'users', ['user_id'], ['id'])

    op.add_column('emails', sa.Column('user_id', sa.Integer(), nullable=True))
    op.drop_index(op.f('ix_emails_message_id'), table_name='emails')
    op.create_index(op.f('ix_emails_message_id'), 'emails', ['message_id'], unique=False)
    op.create_index(op.f('ix_emails_user_id'), 'emails', ['user_id'], unique=False)
    op.create_foreign_key('fk_emails_user_id', 'emails', 'users', ['user_id'], ['id'])

    op.add_column('reminders', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_reminders_user_id'), 'reminders', ['user_id'], unique=False)
    op.create_foreign_key('fk_reminders_user_id', 'reminders', 'users', ['user_id'], ['id'])

    op.drop_constraint(op.f('uq_settings_user_key'), 'settings', type_='unique')


def downgrade() -> None:
    op.create_unique_constraint(op.f('uq_settings_user_key'), 'settings', ['user_id', 'key'], postgresql_nulls_not_distinct=False)

    op.drop_constraint('fk_reminders_user_id', 'reminders', type_='foreignkey')
    op.drop_index(op.f('ix_reminders_user_id'), table_name='reminders')
    op.drop_column('reminders', 'user_id')

    op.drop_constraint('fk_emails_user_id', 'emails', type_='foreignkey')
    op.drop_index(op.f('ix_emails_user_id'), table_name='emails')
    op.drop_index(op.f('ix_emails_message_id'), table_name='emails')
    op.create_index(op.f('ix_emails_message_id'), 'emails', ['message_id'], unique=True)
    op.drop_column('emails', 'user_id')

    op.drop_constraint('fk_drafts_user_id', 'drafts', type_='foreignkey')
    op.drop_index(op.f('ix_drafts_user_id'), table_name='drafts')
    op.drop_column('drafts', 'user_id')

    op.drop_constraint('fk_classification_feedback_user_id', 'classification_feedback', type_='foreignkey')
    op.drop_index(op.f('ix_classification_feedback_user_id'), table_name='classification_feedback')
    op.drop_column('classification_feedback', 'user_id')
