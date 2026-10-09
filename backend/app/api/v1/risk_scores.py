"""
Risk Scores Router — Phase 17 Risk Scoring.

Endpoints:
  GET /risk-scores/ — All authenticated users (JWT) — Device risk scores sorted by score descending
"""

import json
from typing import Annotated, List, Optional
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_any_authenticated_user
from app.models.user import User
from app.services.risk_service import get_all_devices_risk

router = APIRouter()


@router.get("/", summary="List device risk scores")
async def list_risk_scores(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
    risk_band: Optional[str] = Query(default=None, description="Filter by risk band (Low, Medium, High, Critical)"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    Retrieve current risk scores for all devices in the caller's organization,
    sorted by score descending.
    """
    all_scores = get_all_devices_risk(db, current_user.organization_id)

    if risk_band:
        all_scores = [s for s in all_scores if s.get("risk_band", "").lower() == risk_band.lower()]

    paginated = all_scores[offset : offset + limit]
    return paginated
