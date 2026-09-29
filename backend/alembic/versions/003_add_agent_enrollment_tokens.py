"""
Phase 9 — Add agent_enrollment_tokens table.

Replaces the in-memory enrollment token store with a persisted DB table
so tokens survive Render restarts, cold-start wake-ups, and deploys.

Table: agent_enrollment_tokens
  - Tokens are single-use (used_at is set on consumption)
  - Tokens are time-limited (expires_at checked at lookup)
  - Only the SHA-256 hash of the raw token is stored (never plaintext)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Alembic revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_enrollment_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("agent_name_hint", sa.String(120), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_enrollment_tokens_org",
        "agent_enrollment_tokens",
        ["organization_id"],
    )
    op.create_index(
        "idx_enrollment_tokens_hash",
        "agent_enrollment_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "idx_enrollment_tokens_expires",
        "agent_enrollment_tokens",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_enrollment_tokens_expires", table_name="agent_enrollment_tokens")
    op.drop_index("idx_enrollment_tokens_hash", table_name="agent_enrollment_tokens")
    op.drop_index("idx_enrollment_tokens_org", table_name="agent_enrollment_tokens")
    op.drop_table("agent_enrollment_tokens")
