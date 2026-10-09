"""
Logs router — Phase 14.2.

Permission matrix (user-roles.md):
- View logs: Administrator, Security Analyst, Viewer (get_any_authenticated_user)
"""

import uuid
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_any_authenticated_user
from app.models.log import Log
from app.models.user import User

router = APIRouter()


@router.get("/", summary="List logs")
async def list_logs(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
    event_type: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    username: Optional[str] = Query(default=None),
    source_ip: Optional[str] = Query(default=None),
    device_id: Optional[uuid.UUID] = Query(default=None),
    agent_id: Optional[uuid.UUID] = Query(default=None),
    from_date: Optional[datetime] = Query(default=None),
    start_time: Optional[datetime] = Query(default=None),
    to_date: Optional[datetime] = Query(default=None),
    end_time: Optional[datetime] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List logs for the caller's organization with optional filters."""
    effective_from = from_date or start_time
    effective_to = to_date or end_time

    query = db.query(Log).filter(Log.organization_id == current_user.organization_id)

    if event_type:
        query = query.filter(Log.event_type == event_type)
    if source:
        query = query.filter(Log.source == source)
    if severity:
        query = query.filter(Log.severity == severity.lower())
    if username:
        query = query.filter(Log.username == username)
    if source_ip:
        query = query.filter(Log.source_ip == source_ip)
    if device_id:
        query = query.filter(Log.device_id == device_id)
    if agent_id:
        query = query.filter(Log.agent_id == agent_id)
    if effective_from:
        query = query.filter(Log.timestamp >= effective_from)
    if effective_to:
        query = query.filter(Log.timestamp <= effective_to)

    logs = query.order_by(Log.timestamp.desc()).offset(offset).limit(limit).all()

    return [
        {
            "id": str(log.id),
            "organization_id": str(log.organization_id),
            "agent_id": str(log.agent_id),
            "device_id": str(log.device_id) if log.device_id else None,
            "source": log.source,
            "event_type": log.event_type,
            "severity": log.severity,
            "message": log.message,
            "source_ip": str(log.source_ip) if log.source_ip else None,
            "username": log.username,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "updated_at": log.updated_at.isoformat() if log.updated_at else None,
        }
        for log in logs
    ]


@router.get("/{log_id}", summary="Get log entry")
async def get_log(
    log_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve detail for a single log entry in the caller's organization."""
    log = db.query(Log).filter(
        Log.id == log_id,
        Log.organization_id == current_user.organization_id,
    ).first()

    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Log entry not found.", "details": []}},
        )

    return {
        "id": str(log.id),
        "organization_id": str(log.organization_id),
        "agent_id": str(log.agent_id),
        "device_id": str(log.device_id) if log.device_id else None,
        "source": log.source,
        "event_type": log.event_type,
        "severity": log.severity,
        "message": log.message,
        "source_ip": str(log.source_ip) if log.source_ip else None,
        "username": log.username,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "updated_at": log.updated_at.isoformat() if log.updated_at else None,
    }
