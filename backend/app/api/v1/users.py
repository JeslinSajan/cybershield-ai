"""
User management endpoints — Phase 8.

Administrator-only CRUD per FR-2.1, FR-2.2, FR-2.3 and user-api.md.

All endpoints require:
- Valid JWT (get_current_user)
- Administrator role (require_role("Administrator"))

FR-2.3 protection (cannot demote/deactivate last Administrator) is enforced
in PATCH and deactivate endpoints.

Security: password_hash is NEVER returned in any response.
"""

from datetime import datetime, timezone
from typing import Annotated, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models.organization import Role
from app.models.user import User
from app.schemas.user import (
    UserCreateRequest,
    UserDeactivateResponse,
    UserResponse,
    UserUpdateRequest,
)

logger = get_logger("users")
router = APIRouter()

# Reusable admin dependency
_admin_dep = Depends(require_role("Administrator"))


def _get_role_by_id(db: Session, role_id: uuid.UUID) -> Role:
    """Look up a role by ID, raise 404 if not found."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Role not found.", "details": []}},
        )
    return role


def _count_active_admins(db: Session) -> int:
    """Count active, non-deleted Administrator users."""
    admin_role = db.query(Role).filter(Role.name == "Administrator").first()
    if not admin_role:
        return 0
    return (
        db.query(User)
        .filter(
            User.role_id == admin_role.id,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
        .count()
    )


def _last_admin_protection(db: Session, user: User, new_role_id: uuid.UUID | None = None, deactivating: bool = False) -> None:
    """Raise 409 if the operation would leave the system with zero Administrators (FR-2.3)."""
    admin_role = db.query(Role).filter(Role.name == "Administrator").first()
    if not admin_role:
        return

    # Only enforce if this user IS currently an Administrator
    if user.role_id != admin_role.id:
        return

    # Check if this would remove the last admin
    is_demoting = new_role_id is not None and new_role_id != admin_role.id
    if not (is_demoting or deactivating):
        return

    active_admins = _count_active_admins(db)
    if active_admins <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "LAST_ADMINISTRATOR",
                    "message": (
                        "Cannot demote or deactivate the last Administrator. "
                        "Assign another Administrator first."
                    ),
                    "details": [],
                }
            },
        )


# ---------------------------------------------------------------------------
# GET /users — list all users in the organization
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List all users",
    description="Returns all non-deleted users. Administrator only (FR-2.1).",
    dependencies=[_admin_dep],
)
async def list_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("Administrator"))],
) -> List[UserResponse]:
    users = (
        db.query(User)
        .filter(
            User.organization_id == current_user.organization_id,
            User.deleted_at.is_(None),
        )
        .order_by(User.created_at)
        .all()
    )
    return [UserResponse.model_validate(u) for u in users]


# ---------------------------------------------------------------------------
# POST /users — create a new user
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description=(
        "Administrator-only user creation (FR-2.1, FR-2.2). "
        "Password is hashed with bcrypt — never stored or returned in plaintext (FR-1.2)."
    ),
    dependencies=[_admin_dep],
)
async def create_user(
    body: UserCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("Administrator"))],
) -> UserResponse:
    # Validate role exists
    _get_role_by_id(db, body.role_id)

    # Check for duplicate email
    existing = db.query(User).filter(User.email == body.email, User.deleted_at.is_(None)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "CONFLICT", "message": "Email already in use.", "details": []}},
        )

    new_user = User(
        organization_id=body.organization_id,
        role_id=body.role_id,
        email=body.email,
        username=body.username,
        password_hash=hash_password(body.password),  # plaintext never stored
        is_active=True,
        failed_login_count=0,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"Admin {current_user.id} created new user")
    return UserResponse.model_validate(new_user)


# ---------------------------------------------------------------------------
# GET /users/{user_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific user",
    description="Returns a single user by ID. Administrator only (FR-2.1).",
    dependencies=[_admin_dep],
)
async def get_user(
    user_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("Administrator"))],
) -> UserResponse:
    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
            User.deleted_at.is_(None),
        )
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "User not found.", "details": []}},
        )
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}
# ---------------------------------------------------------------------------

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user",
    description=(
        "Partial update of email, username, role, or is_active. "
        "Cannot demote or deactivate the last Administrator (FR-2.3)."
    ),
    dependencies=[_admin_dep],
)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("Administrator"))],
) -> UserResponse:
    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
            User.deleted_at.is_(None),
        )
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "User not found.", "details": []}},
        )

    # FR-2.3: last-Administrator protection
    new_is_active = body.is_active if body.is_active is not None else user.is_active
    _last_admin_protection(
        db,
        user,
        new_role_id=body.role_id,
        deactivating=(new_is_active is False and user.is_active is True),
    )

    # Apply updates
    if body.email is not None:
        conflict = db.query(User).filter(User.email == body.email, User.id != user_id, User.deleted_at.is_(None)).first()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": {"code": "CONFLICT", "message": "Email already in use.", "details": []}},
            )
        user.email = body.email

    if body.username is not None:
        user.username = body.username
    if body.role_id is not None:
        _get_role_by_id(db, body.role_id)
        user.role_id = body.role_id
    if body.is_active is not None:
        user.is_active = body.is_active

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    logger.info(f"Admin {current_user.id} updated user {user_id}")
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# POST /users/{user_id}/deactivate
# ---------------------------------------------------------------------------

@router.post(
    "/{user_id}/deactivate",
    response_model=UserDeactivateResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate a user",
    description=(
        "Soft-deactivates a user (is_active=False). "
        "Cannot deactivate the last Administrator (FR-2.3)."
    ),
    dependencies=[_admin_dep],
)
async def deactivate_user(
    user_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("Administrator"))],
) -> UserDeactivateResponse:
    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
            User.deleted_at.is_(None),
        )
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "User not found.", "details": []}},
        )

    # FR-2.3
    _last_admin_protection(db, user, deactivating=True)

    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    logger.info(f"Admin {current_user.id} deactivated user {user_id}")
    return UserDeactivateResponse.model_validate(user)
