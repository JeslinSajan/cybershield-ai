"""Scan routes for network and device scanning tasks."""

import uuid
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_any_authenticated_user, get_current_analyst_or_admin
from app.models.agent import Agent
from app.models.scan import Scan
from app.models.system import AuditLog
from app.models.user import User

router = APIRouter()


class CreateTaskRequest(BaseModel):
    """Scan creation request schema."""

    agent_id: uuid.UUID
    scan_type: Literal["health_check", "discovery", "vulnerability"]
    target_scope: str = Field(..., min_length=1, max_length=1000)


@router.get("/", summary="List scans")
async def list_scans(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List scans for the caller's organization."""
    query = db.query(Scan).filter(Scan.organization_id == current_user.organization_id)
    if status_filter:
        query = query.filter(Scan.status == status_filter)

    scans = query.order_by(Scan.created_at.desc()).offset(offset).limit(limit).all()

    return [
        {
            "id": str(s.id),
            "organization_id": str(s.organization_id),
            "agent_id": str(s.agent_id) if s.agent_id else None,
            "created_by_user_id": str(s.created_by_user_id),
            "scan_type": s.scan_type,
            "status": s.status,
            "target_scope": s.target_scope,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in scans
    ]


@router.get("/{scan_id}", summary="Get scan")
async def get_scan(
    scan_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve details for a single scan."""
    scan = db.query(Scan).filter(
        Scan.id == scan_id,
        Scan.organization_id == current_user.organization_id,
    ).first()

    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Scan not found.", "details": []}},
        )

    return {
        "id": str(scan.id),
        "organization_id": str(scan.organization_id),
        "agent_id": str(scan.agent_id) if scan.agent_id else None,
        "created_by_user_id": str(scan.created_by_user_id),
        "scan_type": scan.scan_type,
        "status": scan.status,
        "target_scope": scan.target_scope,
        "started_at": scan.started_at.isoformat() if scan.started_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "updated_at": scan.updated_at.isoformat() if scan.updated_at else None,
    }


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create a scan task")
async def start_scan(
    body: CreateTaskRequest,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a pending scan task for an Agent in the caller's organization.
    
    IMPORTANT: This endpoint initiates a network scan. Only scan networks
    and systems you own or are explicitly authorized to assess.
    """
    agent = db.query(Agent).filter(
        Agent.id == body.agent_id,
        Agent.organization_id == current_user.organization_id,
        Agent.deleted_at.is_(None),
    ).first()
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Agent not found.", "details": []}},
        )
    if not agent.is_active or agent.status != "ONLINE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "AGENT_NOT_AVAILABLE",
                    "message": "Agent must be active and ONLINE to receive a task.",
                    "details": [],
                }
            },
        )

    task = Scan(
        organization_id=current_user.organization_id,
        agent_id=agent.id,
        created_by_user_id=current_user.id,
        scan_type=body.scan_type,
        status="PENDING",
        target_scope=body.target_scope,
    )
    db.add(task)
    db.flush()

    audit = AuditLog(
        organization_id=current_user.organization_id,
        actor_type="user",
        actor_id=current_user.id,
        action="scan_created",
        target_type="scans",
        target_id=task.id,
        details={
            "scan_type": task.scan_type,
            "target_scope": task.target_scope,
            "agent_id": str(agent.id),
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(task)

    return {
        "id": str(task.id),
        "organization_id": str(task.organization_id),
        "agent_id": str(task.agent_id),
        "created_by_user_id": str(task.created_by_user_id),
        "scan_type": task.scan_type,
        "status": task.status,
        "target_scope": task.target_scope,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
