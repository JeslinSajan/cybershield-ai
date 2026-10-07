"""Scan routes, including the minimal Phase 10 Agent task creation path."""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_any_authenticated_user, get_current_analyst_or_admin
from app.models.agent import Agent
from app.models.scan import Scan
from app.models.user import User

router = APIRouter()

_any_user = Depends(get_any_authenticated_user)


class CreateTaskRequest(BaseModel):
    """The deliberately small Phase 10 Agent task contract."""

    agent_id: uuid.UUID
    scan_type: Literal["health_check"]
    target_scope: str = Field(..., min_length=1, max_length=1000)


@router.get("/", summary="List scans", dependencies=[_any_user])
async def list_scans():
    return {"message": "Not implemented yet - Phase 12"}


@router.get("/{scan_id}", summary="Get scan", dependencies=[_any_user])
async def get_scan(scan_id: str):
    return {"message": "Not implemented yet - Phase 12"}


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create an Agent health-check task")
async def start_scan(
    body: CreateTaskRequest,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a pending health-check task for an Agent in the caller's organization."""
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
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }
