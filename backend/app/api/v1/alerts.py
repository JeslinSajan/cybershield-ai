"""
Alerts router — Phase 16 Alert Management implementation.

Endpoints:
  GET   /alerts/summary            — All roles (JWT) — Summary counts by status and severity
  GET   /alerts/                   — All roles (JWT) — List alerts with filters
  GET   /alerts/{alert_id}         — All roles (JWT) — Get alert detail + event history
  GET   /alerts/{alert_id}/history — All roles (JWT) — Get alert event history timeline
  PATCH /alerts/{alert_id}         — Analyst + Admin (JWT) — Status transition (Viewer gets 403)
"""

from datetime import datetime, timezone
from typing import Annotated, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_any_authenticated_user, get_current_analyst_or_admin
from app.models.alert import Alert, AlertEvent
from app.models.system import AuditLog
from app.models.user import User

router = APIRouter()

# ---------------------------------------------------------------------------
# Canonical status mapping and allowed transitions
# ---------------------------------------------------------------------------

STATUS_CANONICAL_MAP = {
    "open": "Open",
    "acknowledged": "Acknowledged",
    "investigating": "Investigating",
    "resolved": "Resolved",
    "false_positive": "False Positive",
    "false positive": "False Positive",
}

# Valid status transitions per Phase 16 specification:
# Open → Acknowledged / Investigating / False Positive
# Acknowledged → Investigating / Resolved / False Positive
# Investigating → Resolved / False Positive
ALLOWED_TRANSITIONS = {
    "open": {"acknowledged", "investigating", "false_positive"},
    "acknowledged": {"investigating", "resolved", "false_positive"},
    "investigating": {"resolved", "false_positive"},
}


class UpdateAlertStatusRequest(BaseModel):
    status: str = Field(..., min_length=1, max_length=50, description="Target status name")
    reason: Optional[str] = Field(default=None, max_length=1000, description="Reason for status change")


# ---------------------------------------------------------------------------
# GET /alerts/summary
# Registered BEFORE /{alert_id} to prevent path conflict
# ---------------------------------------------------------------------------

@router.get("/summary", summary="Get alert counts summary")
async def get_alerts_summary(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Return counts of alerts by status and severity for the caller's organization."""
    alerts = (
        db.query(Alert.status, Alert.severity)
        .filter(Alert.organization_id == current_user.organization_id)
        .all()
    )

    summary = {
        "open": 0,
        "acknowledged": 0,
        "investigating": 0,
        "resolved": 0,
        "false_positive": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for alert_status, alert_severity in alerts:
        # Status matching
        st = alert_status.lower().replace(" ", "_") if alert_status else ""
        if st in summary:
            summary[st] += 1

        # Severity matching
        sev = alert_severity.lower() if alert_severity else ""
        if sev in summary:
            summary[sev] += 1

    return summary


# ---------------------------------------------------------------------------
# GET /alerts/
# ---------------------------------------------------------------------------

@router.get("/", summary="List alerts")
async def list_alerts(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Optional[str] = Query(default=None, alias="status"),
    severity: Optional[str] = Query(default=None),
    alert_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List alerts in the caller's organization with optional filters."""
    query = db.query(Alert).filter(Alert.organization_id == current_user.organization_id)

    if status_filter:
        norm = status_filter.lower().replace(" ", "_")
        if norm == "false_positive":
            query = query.filter(func.lower(Alert.status).in_(["false positive", "false_positive"]))
        else:
            query = query.filter(func.lower(Alert.status) == status_filter.lower())

    if severity:
        query = query.filter(func.lower(Alert.severity) == severity.lower())

    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)

    alerts = query.order_by(Alert.triggered_at.desc()).offset(offset).limit(limit).all()

    return [
        {
            "id": str(a.id),
            "organization_id": str(a.organization_id),
            "agent_id": str(a.agent_id) if a.agent_id else None,
            "device_id": str(a.device_id) if a.device_id else None,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "status": a.status,
            "description": a.description,
            "risk_score": float(a.risk_score) if a.risk_score is not None else 0.0,
            "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }
        for a in alerts
    ]


# ---------------------------------------------------------------------------
# GET /alerts/{alert_id}
# ---------------------------------------------------------------------------

@router.get("/{alert_id}", summary="Get alert detail")
async def get_alert(
    alert_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve details and status transition history for a single alert."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.organization_id == current_user.organization_id,
    ).first()

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Alert not found.", "details": []}},
        )

    events = (
        db.query(AlertEvent)
        .filter(AlertEvent.alert_id == alert.id)
        .order_by(AlertEvent.changed_at.desc())
        .all()
    )

    return {
        "id": str(alert.id),
        "organization_id": str(alert.organization_id),
        "agent_id": str(alert.agent_id) if alert.agent_id else None,
        "device_id": str(alert.device_id) if alert.device_id else None,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "status": alert.status,
        "description": alert.description,
        "risk_score": float(alert.risk_score) if alert.risk_score is not None else 0.0,
        "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
        "history": [
            {
                "id": str(e.id),
                "organization_id": str(e.organization_id),
                "alert_id": str(e.alert_id),
                "actor_user_id": str(e.actor_user_id) if e.actor_user_id else None,
                "from_status": e.from_status,
                "to_status": e.to_status,
                "reason": e.reason,
                "changed_at": e.changed_at.isoformat() if e.changed_at else None,
            }
            for e in events
        ],
    }


# ---------------------------------------------------------------------------
# GET /alerts/{alert_id}/history
# ---------------------------------------------------------------------------

@router.get("/{alert_id}/history", summary="Get alert status history")
async def get_alert_history(
    alert_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve event transition history timeline for a single alert."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.organization_id == current_user.organization_id,
    ).first()

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Alert not found.", "details": []}},
        )

    events = (
        db.query(AlertEvent)
        .filter(AlertEvent.alert_id == alert.id)
        .order_by(AlertEvent.changed_at.desc())
        .all()
    )

    return [
        {
            "id": str(e.id),
            "organization_id": str(e.organization_id),
            "alert_id": str(e.alert_id),
            "actor_user_id": str(e.actor_user_id) if e.actor_user_id else None,
            "from_status": e.from_status,
            "to_status": e.to_status,
            "reason": e.reason,
            "changed_at": e.changed_at.isoformat() if e.changed_at else None,
        }
        for e in events
    ]


# ---------------------------------------------------------------------------
# PATCH /alerts/{alert_id}
# ---------------------------------------------------------------------------

@router.patch("/{alert_id}", summary="Update alert status")
async def update_alert_status(
    alert_id: uuid.UUID,
    body: UpdateAlertStatusRequest,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Transition an alert's lifecycle status. Analyst and Admin only (FR-3.2)."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.organization_id == current_user.organization_id,
    ).first()

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Alert not found.", "details": []}},
        )

    norm_current = alert.status.lower().replace(" ", "_") if alert.status else ""
    norm_target = body.status.lower().replace(" ", "_") if body.status else ""

    if norm_target not in STATUS_CANONICAL_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Unknown target status '{body.status}'.",
                    "details": [],
                }
            },
        )

    allowed_targets = ALLOWED_TRANSITIONS.get(norm_current, set())
    if norm_target not in allowed_targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Invalid status transition from '{alert.status}' to '{body.status}'.",
                    "details": [],
                }
            },
        )

    from_status = alert.status
    to_status = STATUS_CANONICAL_MAP[norm_target]

    alert.status = to_status
    alert.updated_at = datetime.now(timezone.utc)

    event = AlertEvent(
        organization_id=current_user.organization_id,
        alert_id=alert.id,
        actor_user_id=current_user.id,
        from_status=from_status,
        to_status=to_status,
        reason=body.reason,
        changed_at=datetime.now(timezone.utc),
    )
    db.add(event)

    audit = AuditLog(
        organization_id=current_user.organization_id,
        actor_type="user",
        actor_id=current_user.id,
        action="alert_status_changed",
        target_type="alerts",
        target_id=alert.id,
        details={
            "from_status": from_status,
            "to_status": to_status,
            "reason": body.reason,
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(alert)
    db.refresh(event)

    return {
        "id": str(alert.id),
        "status": alert.status,
        "from_status": from_status,
        "reason": body.reason,
        "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
    }
