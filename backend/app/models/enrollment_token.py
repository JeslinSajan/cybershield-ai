"""
AgentEnrollmentToken — DB-persisted enrollment token model.

Phase 9 addition. Replaces the in-memory enrollment_store.py approach.

Why DB-backed (not in-memory):
  Render free tier restarts on every deploy and cold-start wake-up (~15 min idle).
  An in-memory store loses all pending tokens on every restart, making it impossible
  to enroll an agent after any backend restart. The DB is the only durable store
  available in this architecture (Neon Postgres).

Token security:
  The raw token is never stored. Only the SHA-256 hash is persisted, matching
  the same pattern as AgentCredential. Enrollment tokens are short-lived
  (default 60 min) and single-use (used_at is set on consumption).
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class AgentEnrollmentToken(Base):
    """
    One-time agent enrollment tokens.

    Lifecycle:
      1. Admin calls POST /agents/enrollment-token → row created, raw token returned once.
      2. Agent calls POST /agents/register → row looked up by token_hash, used_at set.
      3. Expired or used rows are cleaned up lazily (checked at lookup time).
    """
    __tablename__ = "agent_enrollment_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # organization scope — which org this token enrolls into
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # who generated this token
    created_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    # SHA-256 hash of the raw token (raw token is NEVER stored)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    # optional human label for audit/UI purposes
    agent_name_hint = Column(String(120), nullable=True)
    # when this token expires (set by admin at creation time)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    # set when the token is consumed by POST /agents/register
    # NULL = not yet used; NOT NULL = already used (one-time use enforced)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
