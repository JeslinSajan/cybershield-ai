"""
DB-backed enrollment token store — Phase 9.

Replaces the previous in-memory dict approach. Tokens are persisted in
Postgres so they survive Render restarts, cold-start wake-ups, and deploys.

Interface is unchanged from the old in-memory version:
  add_token(db, token_hash, expires_at, organization_id, created_by_user_id, agent_name_hint)
  consume_token(db, token_hash) -> Optional[dict]

Callers (agents.py) pass the SQLAlchemy session explicitly.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.enrollment_token import AgentEnrollmentToken


def add_token(
    db: Session,
    token_hash: str,
    expires_at: datetime,
    organization_id: str,
    created_by_user_id: str,
    agent_name_hint: str = None,
) -> None:
    """Persist a new enrollment token (hashed). Raw token is NEVER stored."""
    import uuid
    token = AgentEnrollmentToken(
        organization_id=uuid.UUID(str(organization_id)),
        created_by_user_id=uuid.UUID(str(created_by_user_id)),
        token_hash=token_hash,
        agent_name_hint=agent_name_hint,
        expires_at=expires_at,
        used_at=None,
    )
    db.add(token)
    db.flush()  # ensure row is written; caller commits


def consume_token(db: Session, token_hash: str) -> Optional[dict]:
    """
    Look up a token by hash, validate it, mark it used, and return metadata.

    Returns None if:
      - token not found
      - token already used (used_at is not None)
      - token expired (expires_at < now)

    On success: sets used_at = now and returns {"organization_id": str}.
    Caller is responsible for committing.
    """
    now = datetime.now(timezone.utc)

    row = db.query(AgentEnrollmentToken).filter(
        AgentEnrollmentToken.token_hash == token_hash,
        AgentEnrollmentToken.used_at.is_(None),   # not yet consumed
        AgentEnrollmentToken.expires_at > now,     # not expired
    ).first()

    if row is None:
        return None

    # Mark as used — single-use enforcement
    row.used_at = now

    return {
        "organization_id": str(row.organization_id),
        "created_by_user_id": str(row.created_by_user_id),
    }
