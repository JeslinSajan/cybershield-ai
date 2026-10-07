"""make device_id nullable

Revision ID: 004
Revises: 003
Create Date: 2026-10-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"

def upgrade():
    op.alter_column('scan_results', 'device_id', existing_type=postgresql.UUID(), nullable=True)

def downgrade():
    op.alter_column('scan_results', 'device_id', existing_type=postgresql.UUID(), nullable=False)
