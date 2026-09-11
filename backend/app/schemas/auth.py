"""Pydantic schemas for authentication endpoints — Phase 8."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class LoginRequest(BaseModel):
    """Request body for POST /auth/login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's plaintext password (never stored or logged)")

    model_config = {"json_schema_extra": {"example": {"email": "admin@example.com", "password": "StrongPass!123"}}}


class UserInToken(BaseModel):
    """User fields returned inside a login response. Never includes password_hash."""

    id: uuid.UUID
    organization_id: uuid.UUID
    role_id: uuid.UUID
    email: str
    username: Optional[str]
    is_active: bool
    last_login_at: Optional[datetime]

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """Response body for POST /auth/login."""

    user: UserInToken
    token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer")


class MeResponse(BaseModel):
    """Response body for GET /auth/me. Never includes password_hash."""

    id: uuid.UUID
    organization_id: uuid.UUID
    role_id: uuid.UUID
    email: str
    username: Optional[str]
    is_active: bool
    failed_login_count: int
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
