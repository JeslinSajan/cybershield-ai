"""
Alembic migration 002 — Add last_failed_at to users table.

Rationale: FR-1.5 requires locking after 5 consecutive failed login
attempts within a 10-minute window. The users table already has
failed_login_count but lacks a timestamp to enforce the time window.
Without this column, lockout would be permanent (never expire), which
violates the spec. This migration adds the nullable timestamp column.
"""

from alembic import op
import sqlalchemy as sa


# Alembic revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "last_failed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp of the most recent failed login attempt. "
                    "Used with failed_login_count to enforce the 10-minute lockout window (FR-1.5)."
        )
    )


def downgrade() -> None:
    op.drop_column("users", "last_failed_at")
