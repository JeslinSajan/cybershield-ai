"""add upload_id to scan_results for idempotent uploads

Revision ID: 005
Revises: 004
Create Date: 2026-10-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005"
down_revision = "004"

def upgrade():
    op.add_column('scan_results', sa.Column('upload_id', sa.String(36), nullable=True))
    op.create_unique_constraint('uq_scan_results_upload_id', 'scan_results', ['upload_id'])
    op.create_index('idx_scan_results_upload_id', 'scan_results', ['upload_id'])

def downgrade():
    op.drop_index('idx_scan_results_upload_id', table_name='scan_results')
    op.drop_constraint('uq_scan_results_upload_id', 'scan_results')
    op.drop_column('scan_results', 'upload_id')
