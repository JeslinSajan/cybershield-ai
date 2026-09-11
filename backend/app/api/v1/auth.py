"""
Authentication endpoints — Phase 8.

Implements FR-1.1 through FR-1.5:
- POST /auth/login  — verify credentials, issue JWT
- POST /auth/logout — client-side token invalidation
- GET  /auth/me     — current user identity

Registration is NOT self-service. New users are created by an Administrator
via POST /users. The old /register stub has been removed.

Lockout policy (FR-1.5):
  - 5 consecutive failures within a 10-minute window → 423 Locked
  - Window expiry: if last_failed_at is older than 10 minutes, the lock
    is released and the next attempt is treated as fresh (count resets to 1
    if it also fails, or 0 if it succeeds).
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.logging import get_logger
from app.core.security import create_access_token, verify_password
from app.models.organization import Role
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse, UserInToken

logger = get_logger("auth")

router = APIRouter()

# FR-1.5 constants
_MAX_FAILURES = 5
_LOCKOUT_WINDOW = timedelta(minutes=10)


def _is_within_lockout_window(last_failed_at: datetime | None) -> bool:
    """Return True if last_failed_at is within the lockout window."""
    if last_failed_at is None:
        return False
    now = datetime.now(timezone.utc)
    # Normalise to UTC if naive (shouldn't happen with timezone=True columns)
    if last_failed_at.tzinfo is None:
        last_failed_at = last_failed_at.replace(tzinfo=timezone.utc)
    return (now - last_failed_at) < _LOCKOUT_WINDOW


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    description=(
        "Authenticates a user and issues a JWT access token (FR-1.1, FR-1.3). "
        "Accounts are locked after 5 consecutive failures within 10 minutes (FR-1.5). "
        "Passwords are never logged or returned (FR-1.2)."
    ),
)
async def login(
    request: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    # ------------------------------------------------------------------
    # 1. Look up the user by email
    # ------------------------------------------------------------------
    user: User | None = (
        db.query(User)
        .filter(User.email == request.email, User.deleted_at.is_(None))
        .first()
    )

    # Use a generic error for both "not found" and "wrong password" to prevent
    # user enumeration via timing differences.
    invalid_credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "The provided credentials are invalid.",
                "details": [],
            }
        },
    )

    if user is None:
        # Still call verify_password with a valid dummy hash to equalise timing
        # (prevents user enumeration via response time differences).
        # This is a real bcrypt hash of "dummy" — it's not a secret.
        _DUMMY_HASH = "$2b$12$3bM.1ySmbgfLQ4bMFKauE.0GY0NHs6VV9wNJg1/zUYN3d4OZi/QDW"
        verify_password(request.password, _DUMMY_HASH)
        raise invalid_credentials_exc

    # ------------------------------------------------------------------
    # 2. Check account activation
    # ------------------------------------------------------------------
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "ACCOUNT_DEACTIVATED",
                    "message": "This account has been deactivated.",
                    "details": [],
                }
            },
        )

    # ------------------------------------------------------------------
    # 3. Lockout check (FR-1.5) with window expiry
    #
    # If failed_login_count >= 5 AND last_failed_at is within the window
    # → locked. If the window has passed, proceed as a fresh attempt.
    # ------------------------------------------------------------------
    window_active = _is_within_lockout_window(user.last_failed_at)

    if user.failed_login_count >= _MAX_FAILURES and window_active:
        logger.warning(f"Login blocked: account locked (failed_login_count={user.failed_login_count})")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "error": {
                    "code": "ACCOUNT_LOCKED",
                    "message": (
                        f"Account is locked after {_MAX_FAILURES} failed attempts. "
                        "Try again in 10 minutes."
                    ),
                    "details": [],
                }
            },
        )

    # ------------------------------------------------------------------
    # 4. Verify password
    # ------------------------------------------------------------------
    password_ok = verify_password(request.password, user.password_hash)

    if not password_ok:
        # FR-1.5: track failures
        # If the previous window expired, start a fresh window (count = 1)
        # rather than incrementing from the old locked state.
        if user.failed_login_count >= _MAX_FAILURES and not window_active:
            user.failed_login_count = 1
        else:
            user.failed_login_count += 1

        user.last_failed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Failed login attempt (count now {user.failed_login_count})")
        raise invalid_credentials_exc

    # ------------------------------------------------------------------
    # 5. Successful login — reset failure counters, update last_login_at
    # ------------------------------------------------------------------
    user.failed_login_count = 0
    user.last_failed_at = None
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    # ------------------------------------------------------------------
    # 6. Load role name for JWT payload (fast RBAC)
    # ------------------------------------------------------------------
    role: Role | None = db.query(Role).filter(Role.id == user.role_id).first()
    role_name = role.name if role else "Unknown"

    # ------------------------------------------------------------------
    # 7. Issue JWT
    # ------------------------------------------------------------------
    token = create_access_token(
        subject=str(user.id),
        role_name=role_name,
        organization_id=str(user.organization_id),
    )

    logger.info("Successful login")
    return LoginResponse(user=UserInToken.model_validate(user), token=token)


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout (invalidate client token)",
    description=(
        "Logout endpoint (FR-1.4). The client must discard the JWT. "
        "Server-side token denylist is not implemented in the MVP — "
        "adding one would require a Redis or DB-backed revocation store "
        "and can be added in a future phase without changing this endpoint signature."
    ),
)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    logger.info("User logged out")
    return None


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user identity",
    description="Returns the authenticated user's profile. password_hash is never returned.",
)
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> MeResponse:
    return MeResponse.model_validate(current_user)
