"""
Security utilities for CyberShield AI — Phase 8.

Covers:
- bcrypt password hashing (FR-1.2)
- JWT creation and validation (FR-1.3)

IMPORTANT: This module never logs plaintext passwords, JWT secrets,
or any credential material. Log statements in this file are limited
to operation names and error types only.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("security")

# bcrypt context — always use bcrypt, never store or log plaintext
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt.

    The plaintext password is never logged or stored.
    Returns the bcrypt hash string for storage in users.password_hash.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Returns True if the password matches, False otherwise.
    Neither the plaintext nor the hash is logged.
    """
    return _pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT creation and validation
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str,
    role_name: str,
    organization_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject: The user's UUID (stored as 'sub' claim).
        role_name: The user's role name (stored as 'role' claim).
        organization_id: The user's org UUID (stored as 'org' claim).
        expires_delta: Token lifetime. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.

    Note on refresh tokens: This MVP issues access tokens only.
    If refresh tokens are added in a future phase, add a separate
    create_refresh_token() function here and a /auth/refresh endpoint
    in auth.py. The access token expiry (30 min) is intentionally short
    to limit the exposure window if a token is stolen.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    payload = {
        "sub": subject,           # user UUID
        "role": role_name,        # role name for fast RBAC without a DB hit
        "org": organization_id,   # organization scope
        "iat": now,               # issued at
        "exp": expire,            # expiry
        "type": "access",         # token type guard (not refresh)
    }

    encoded = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.debug("Access token created for subject (id redacted)")
    return encoded


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Args:
        token: The raw JWT string from the Authorization header.

    Returns:
        The decoded payload dict if valid.

    Raises:
        JWTError: If the token is invalid, expired, or tampered.
    """
    settings = get_settings()
    # Let JWTError propagate — callers (deps.py) translate it to HTTPException
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

    # Reject refresh tokens presented as access tokens
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")

    return payload
