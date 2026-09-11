"""
FastAPI dependency injection for authentication and RBAC — Phase 8.

Exports:
- get_current_user: validates JWT and loads user from DB
- require_role(*roles): factory → dependency that enforces role membership
- get_current_admin: shorthand for require_role("Administrator")
- get_current_analyst_or_admin: shorthand for require_role("Administrator", "Security Analyst")

Agent authentication is NOT implemented here. Agent-facing routes will use
a separate agent credential dependency to be added in Phase 9-10. Those
routes should be annotated with:
    # TODO Phase 9: replace Depends(placeholder) with Depends(get_current_agent)
"""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.models.user import User
from app.models.organization import Role

logger = get_logger("deps")


class _BearerScheme(HTTPBearer):
    """HTTPBearer subclass that raises 401 (not 403) when the token is missing.

    FastAPI's default HTTPBearer(auto_error=True) raises 403 Forbidden on a
    missing Authorization header, but RFC 6750 and the API contract require 401
    Unauthorized for missing credentials.
    """

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        try:
            return await super().__call__(request)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "NOT_AUTHENTICATED",
                        "message": "Authentication credentials were not provided or are invalid.",
                        "details": [],
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )


_bearer = _BearerScheme(auto_error=True)


# ---------------------------------------------------------------------------
# Core user loader
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Validate JWT and return the authenticated User ORM object.

    Raises:
        401 Unauthorized: missing/invalid/expired token, user not found,
                          user deactivated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "NOT_AUTHENTICATED",
                "message": "Could not validate credentials.",
                "details": [],
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Load user from DB
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        logger.warning("JWT valid but user not found in DB (deleted?)")
        raise credentials_exception

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

    return user


# ---------------------------------------------------------------------------
# RBAC role enforcement factory
# ---------------------------------------------------------------------------

def require_role(*allowed_roles: str):
    """Dependency factory for role-based access control (FR-3.1).

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role("Administrator"))])

        @router.get("/analysts", dependencies=[Depends(require_role("Administrator", "Security Analyst"))])

    Default policy is DENY — if the user's role is not in allowed_roles, raises 403.
    Role name is loaded from the DB to guarantee accuracy (not just the JWT claim).
    """

    async def _check_role(
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        role = db.query(Role).filter(Role.id == current_user.role_id).first()
        role_name = role.name if role else None

        if role_name not in allowed_roles:
            logger.info(f"RBAC denied: role '{role_name}' not in {allowed_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You are not allowed to perform this action.",
                        "details": [],
                    }
                },
            )

        return current_user

    return _check_role


# ---------------------------------------------------------------------------
# Convenience shorthands (used across routers)
# ---------------------------------------------------------------------------

def get_current_admin(
    current_user: Annotated[User, Depends(require_role("Administrator"))],
) -> User:
    """Require the caller to be an Administrator."""
    return current_user


def get_current_analyst_or_admin(
    current_user: Annotated[User, Depends(require_role("Administrator", "Security Analyst"))],
) -> User:
    """Require the caller to be an Administrator or Security Analyst."""
    return current_user


def get_any_authenticated_user(
    current_user: Annotated[User, Depends(require_role("Administrator", "Security Analyst", "Viewer"))],
) -> User:
    """Require any authenticated human user (all three roles)."""
    return current_user
