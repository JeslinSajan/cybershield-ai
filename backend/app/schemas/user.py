"""Pydantic schemas for user management endpoints — Phase 8."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class UserResponse(BaseModel):
    """User object returned by all user management endpoints.
    password_hash is explicitly excluded — never returned in any response.
    """

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


class UserCreateRequest(BaseModel):
    """Request body for POST /users (Administrator-only)."""

    organization_id: uuid.UUID = Field(..., description="Organization this user belongs to")
    email: EmailStr = Field(..., description="User's email address (must be unique)")
    username: Optional[str] = Field(None, max_length=80)
    password: str = Field(..., min_length=8, description="Plaintext password — hashed before storage, never logged")
    role_id: uuid.UUID = Field(..., description="UUID of the role to assign")

    model_config = {
        "json_schema_extra": {
            "example": {
                "organization_id": "uuid",
                "email": "analyst@example.com",
                "username": "analyst01",
                "password": "StrongPass!123",
                "role_id": "uuid",
            }
        }
    }


class UserUpdateRequest(BaseModel):
    """Request body for PATCH /users/{user_id} (Administrator-only).
    All fields are optional — only provided fields are updated.
    """

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, max_length=80)
    role_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class UserDeactivateResponse(BaseModel):
    """Response body for POST /users/{user_id}/deactivate."""

    id: uuid.UUID
    is_active: bool
    updated_at: datetime

    model_config = {"from_attributes": True}
