"""Schemas module - Pydantic models for request/response validation."""

from app.schemas.base import (
    ErrorDetail,
    HealthResponse,
    HealthDatabaseResponse,
    RootResponse,
    PaginationParams,
    ListResponse,
    CreatedResponse
)
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse, UserInToken
from app.schemas.user import (
    UserResponse,
    UserCreateRequest,
    UserUpdateRequest,
    UserDeactivateResponse,
)

__all__ = [
    # Base
    "ErrorDetail",
    "HealthResponse",
    "HealthDatabaseResponse",
    "RootResponse",
    "PaginationParams",
    "ListResponse",
    "CreatedResponse",
    # Auth
    "LoginRequest",
    "LoginResponse",
    "MeResponse",
    "UserInToken",
    # Users
    "UserResponse",
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserDeactivateResponse",
]
