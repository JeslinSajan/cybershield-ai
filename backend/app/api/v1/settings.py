"""
Settings and Audit Logs router — Phase 21 implementation.

Permission matrix:
- System Settings (GET, PUT): Administrator only (get_current_admin). Analyst and Viewer receive 403.
- Audit Logs (GET):           Administrator only (get_current_admin). Analyst and Viewer receive 403.
"""

import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.system import AuditLog, SystemSetting
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class SystemSettingResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    key: str
    value: Any
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PutSettingRequest(BaseModel):
    value: Any = Field(..., description="JSON-serializable value for the setting")


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    actor_type: str
    actor_id: Optional[uuid.UUID] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[uuid.UUID] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# System Settings Endpoints (Admin Only)
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[SystemSettingResponse], summary="Get system settings (Admin only)")
async def get_system_settings(
    current_user: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve all configuration keys for the administrator's organization."""
    settings = (
        db.query(SystemSetting)
        .filter(SystemSetting.organization_id == current_user.organization_id)
        .order_by(SystemSetting.key.asc())
        .all()
    )
    return settings


@router.put("/{key}", response_model=SystemSettingResponse, summary="Set system setting (Admin only)")
@router.patch("/{key}", response_model=SystemSettingResponse, summary="Update system setting (Admin only)")
async def set_system_setting(
    key: str,
    body: PutSettingRequest,
    current_user: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create or update a system setting key for the organization."""
    clean_key = key.strip()
    setting = (
        db.query(SystemSetting)
        .filter(
            SystemSetting.organization_id == current_user.organization_id,
            SystemSetting.key == clean_key,
        )
        .first()
    )

    if setting:
        setting.value = body.value
    else:
        setting = SystemSetting(
            organization_id=current_user.organization_id,
            key=clean_key,
            value=body.value,
            created_by_user_id=current_user.id,
        )
        db.add(setting)

    db.flush()

    audit = AuditLog(
        organization_id=current_user.organization_id,
        actor_type="user",
        actor_id=current_user.id,
        action="setting_updated",
        target_type="system_settings",
        target_id=setting.id,
        details={"key": clean_key},
    )
    db.add(audit)

    db.commit()
    db.refresh(setting)
    return setting


# ---------------------------------------------------------------------------
# Audit Logs Endpoints (Admin Only)
# ---------------------------------------------------------------------------

audit_router = APIRouter()


@router.get("/audit-logs", response_model=List[AuditLogResponse], summary="List audit logs (Admin only)")
@audit_router.get("/", response_model=List[AuditLogResponse], summary="List audit logs (Admin only)")
async def list_audit_logs(
    current_user: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    action: Optional[str] = Query(default=None),
    actor_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Retrieve audit log history for administrative compliance."""
    query = db.query(AuditLog).filter(AuditLog.organization_id == current_user.organization_id)

    if action:
        query = query.filter(AuditLog.action == action)
    if actor_type:
        query = query.filter(AuditLog.actor_type == actor_type)

    logs = (
        query.order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return logs
