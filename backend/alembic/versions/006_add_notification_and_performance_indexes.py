"""add notification and performance indexes

Revision ID: 006
Revises: 005
Create Date: 2026-10-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"


def upgrade():
    # Notification performance indexes
    op.create_index(
        'idx_notifications_org_user_unread',
        'notifications',
        ['organization_id', 'user_id', 'is_read'],
        if_not_exists=True,
    )
    op.create_index(
        'idx_notifications_created_at',
        'notifications',
        ['created_at'],
        if_not_exists=True,
    )
    # Device and agent query performance indexes
    op.create_index(
        'idx_devices_org_status',
        'devices',
        ['organization_id', 'status'],
        if_not_exists=True,
    )
    op.create_index(
        'idx_agents_org_status',
        'agents',
        ['organization_id', 'status'],
        if_not_exists=True,
    )


def downgrade():
    op.drop_index('idx_notifications_org_user_unread', table_name='notifications', if_exists=True)
    op.drop_index('idx_notifications_created_at', table_name='notifications', if_exists=True)
    op.drop_index('idx_devices_org_status', table_name='devices', if_exists=True)
    op.drop_index('idx_agents_org_status', table_name='agents', if_exists=True)
