"""
Threat Intelligence router — Phase 18 full implementation.

Permission matrix (user-roles.md):
- View threat indicators: Administrator, Security Analyst, Viewer (get_any_authenticated_user)
- Create threat indicators: Administrator, Security Analyst (get_current_analyst_or_admin)
- Delete threat indicators: Administrator ONLY (get_current_admin)
"""

import uuid
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import (
    get_any_authenticated_user,
    get_current_admin,
    get_current_analyst_or_admin,
)
from app.models.log import ThreatIndicator
from app.models.system import AuditLog
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class ThreatIndicatorCreate(BaseModel):
    indicator_type: str = Field(..., description="Type of indicator: ip, domain, or hash")
    value: str = Field(..., min_length=1, max_length=255, description="Indicator value")
    description: Optional[str] = Field(None, description="Contextual threat description")
    source: str = Field(default="local", max_length=50, description="Source feed or provider")

    @field_validator("indicator_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        clean = v.lower().strip()
        if clean not in ("ip", "domain", "hash"):
            raise ValueError("indicator_type must be one of: 'ip', 'domain', 'hash'")
        return clean

    @field_validator("value")
    @classmethod
    def clean_val(cls, v: str) -> str:
        return v.strip()


class ThreatIndicatorResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    indicator_type: str
    value: str
    description: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helper: write audit log
# ---------------------------------------------------------------------------

def _write_audit(
    db: Session,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    action: str,
    target_id: uuid.UUID,
    details: Optional[dict] = None,
):
    audit = AuditLog(
        organization_id=org_id,
        actor_type="user",
        actor_id=user_id,
        action=action,
        target_type="threat_indicators",
        target_id=target_id,
        details=details or {},
    )
    db.add(audit)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[ThreatIndicatorResponse], summary="List threat indicators")
async def list_indicators(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
    indicator_type: Optional[str] = Query(default=None, description="Filter by indicator type ('ip', 'domain', 'hash')"),
    source: Optional[str] = Query(default=None, description="Filter by source"),
    search: Optional[str] = Query(default=None, description="Search indicator value or description"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List threat indicators for the user's organization with optional filters."""
    query = db.query(ThreatIndicator).filter(
        ThreatIndicator.organization_id == current_user.organization_id
    )

    if indicator_type:
        query = query.filter(ThreatIndicator.indicator_type == indicator_type.lower().strip())
    if source:
        query = query.filter(ThreatIndicator.source == source.strip())
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (ThreatIndicator.value.ilike(search_pattern)) |
            (ThreatIndicator.description.ilike(search_pattern))
        )

    indicators = query.order_by(ThreatIndicator.created_at.desc()).offset(offset).limit(limit).all()
    return indicators


@router.get("/{indicator_id}", response_model=ThreatIndicatorResponse, summary="Get threat indicator")
async def get_indicator(
    indicator_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve details of a single threat indicator by ID."""
    indicator = db.query(ThreatIndicator).filter(
        ThreatIndicator.id == indicator_id,
        ThreatIndicator.organization_id == current_user.organization_id,
    ).first()

    if not indicator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Threat indicator with ID '{indicator_id}' was not found.",
                    "details": [],
                }
            },
        )
    return indicator


@router.post("/", response_model=ThreatIndicatorResponse, status_code=status.HTTP_201_CREATED, summary="Add threat indicator")
async def create_indicator(
    body: ThreatIndicatorCreate,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Add a new threat intelligence indicator (IP, domain, or hash). Admin or Analyst."""
    # Check duplicate on (organization_id, indicator_type, value)
    existing = db.query(ThreatIndicator).filter(
        ThreatIndicator.organization_id == current_user.organization_id,
        ThreatIndicator.indicator_type == body.indicator_type,
        ThreatIndicator.value == body.value,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "CONFLICT",
                    "message": f"Threat indicator of type '{body.indicator_type}' with value '{body.value}' already exists.",
                    "details": [],
                }
            },
        )

    indicator = ThreatIndicator(
        organization_id=current_user.organization_id,
        indicator_type=body.indicator_type,
        value=body.value,
        description=body.description,
        source=body.source,
    )
    db.add(indicator)
    db.flush()

    _write_audit(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        action="threat_indicator_created",
        target_id=indicator.id,
        details={
            "indicator_type": indicator.indicator_type,
            "value": indicator.value,
            "source": indicator.source,
        },
    )

    db.commit()
    db.refresh(indicator)
    return indicator


@router.delete("/{indicator_id}", status_code=status.HTTP_200_OK, summary="Delete threat indicator")
async def delete_indicator(
    indicator_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a threat indicator. Administrator only."""
    indicator = db.query(ThreatIndicator).filter(
        ThreatIndicator.id == indicator_id,
        ThreatIndicator.organization_id == current_user.organization_id,
    ).first()

    if not indicator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Threat indicator with ID '{indicator_id}' was not found.",
                    "details": [],
                }
            },
        )

    _write_audit(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        action="threat_indicator_deleted",
        target_id=indicator.id,
        details={
            "indicator_type": indicator.indicator_type,
            "value": indicator.value,
        },
    )

    db.delete(indicator)
    db.commit()

    return {
        "message": "Threat indicator deleted successfully",
        "id": str(indicator_id),
    }
