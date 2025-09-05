"""Add Clerk integration fields to User model

Revision ID: 4fea26b68426
Revises: 1a31ce608336
Create Date: 2025-08-22 12:55:53.858366

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision = '4fea26b68426'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('webhook_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('webhook_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('event_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'SUCCESS', 'FAILED', 'IGNORED', 'INVALID', name='webhookstatus'), nullable=False),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=False),
    sa.Column('max_retries', sa.Integer(), nullable=False),
    sa.Column('next_retry_at', sa.DateTime(), nullable=True),
    sa.Column('error_message', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('error_details', sa.JSON(), nullable=True),
    sa.Column('raw_data', sa.JSON(), nullable=True),
    sa.Column('processed_data', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('source_ip', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('user_agent', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_events_event_type'), 'webhook_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_webhook_events_status'), 'webhook_events', ['status'], unique=False)
    op.create_index(op.f('ix_webhook_events_webhook_id'), 'webhook_events', ['webhook_id'], unique=True)
    op.add_column('user', sa.Column('clerk_user_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('user', sa.Column('auth_provider', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    op.add_column('user', sa.Column('is_synced', sa.Boolean(), nullable=False))
    op.add_column('user', sa.Column('email_verified', sa.Boolean(), nullable=False))
    op.add_column('user', sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.add_column('user', sa.Column('last_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.add_column('user', sa.Column('profile_image_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('user', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('user', sa.Column('last_login', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('account_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_user_clerk_user_id'), 'user', ['clerk_user_id'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_user_clerk_user_id'), table_name='user')
    op.drop_column('user', 'account_id')
    op.drop_column('user', 'last_login')
    op.drop_column('user', 'created_at')
    op.drop_column('user', 'profile_image_url')
    op.drop_column('user', 'last_name')
    op.drop_column('user', 'first_name')
    op.drop_column('user', 'email_verified')
    op.drop_column('user', 'is_synced')
    op.drop_column('user', 'auth_provider')
    op.drop_column('user', 'clerk_user_id')
    op.drop_index(op.f('ix_webhook_events_webhook_id'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_status'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_event_type'), table_name='webhook_events')
    op.drop_table('webhook_events')
