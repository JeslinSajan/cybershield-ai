"""
Agents router — Phase 9 full implementation.

Endpoints:
  POST /agents/enrollment-token  — Admin only (JWT) — FR-4.1
  POST /agents/register          — No auth, uses enrollment token — FR-4.2
  POST /agents/heartbeat         — Agent credential — FR-4.3
  GET  /agents/                  — Admin + Analyst (JWT) — FR-4.7
  GET  /agents/{agent_id}        — Admin + Analyst (JWT) — FR-4.7
  POST /agents/{agent_id}/revoke — Admin only (JWT) — FR-4.5
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import (
    get_current_admin,
    get_current_analyst_or_admin,
    require_agent_credential,
)
from app.core.enrollment_store import add_token, consume_token
from app.models.agent import Agent, AgentCredential, AgentHeartbeat
from app.models.organization import Organization
from app.models.scan import Scan, ScanResult
from app.models.system import AuditLog
from app.models.user import User

router = APIRouter()

# Offline detection threshold: mark agents offline if no heartbeat for 120 seconds
OFFLINE_THRESHOLD_SECONDS = 120


def _mark_stale_agents_offline(db: Session, exclude_agent_id: Optional[uuid.UUID] = None) -> int:
    """Mark agents as OFFLINE if they haven't sent a heartbeat recently.
    
    Returns the number of agents marked offline.
    """
    threshold = datetime.now(timezone.utc) - timedelta(seconds=OFFLINE_THRESHOLD_SECONDS)
    
    # Find agents that are ONLINE but have stale heartbeats
    query = db.query(Agent).filter(
        Agent.status == "ONLINE",
        Agent.is_active == True,
        (Agent.last_heartbeat_at < threshold) | (Agent.last_heartbeat_at.is_(None))
    )
    if exclude_agent_id:
        query = query.filter(Agent.id != exclude_agent_id)
        
    stale_agents = query.all()
    
    count = 0
    for stale_agent in stale_agents:
        stale_agent.status = "OFFLINE"
        count += 1
    
    if count > 0:
        db.commit()
    
    return count


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class EnrollmentTokenRequest(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=120)
    expires_in_minutes: int = Field(default=60, ge=1, le=1440)


class RegisterRequest(BaseModel):
    enrollment_token: str
    name: str = Field(..., min_length=1, max_length=120)
    hostname: str = Field(..., min_length=1, max_length=120)
    version: str = Field(default="1.0.0", max_length=50)


class HeartbeatRequest(BaseModel):
    agent_id: uuid.UUID
    timestamp: datetime
    status: str = Field(default="ONLINE")
    version: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    details: Optional[dict] = None


class RevokeRequest(BaseModel):
    pass


class TaskStatusUpdate(BaseModel):
    status: str
    started_at: Optional[datetime] = None
    details: Optional[dict] = None


class ResultUpload(BaseModel):
    scan_id: uuid.UUID
    device_id: Optional[uuid.UUID] = None
    upload_id: Optional[str] = Field(None, max_length=36)
    result_type: str
    raw_payload: dict


# ---------------------------------------------------------------------------
# Helper: write audit log
# ---------------------------------------------------------------------------

def _write_audit(db: Session, org_id, actor_type: str, actor_id,
                 action: str, target_type: str, target_id, details: dict = None):
    log = AuditLog(
        organization_id=org_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
    )
    db.add(log)


# ---------------------------------------------------------------------------
# POST /agents/enrollment-token  (Admin JWT)
# ---------------------------------------------------------------------------

@router.post("/enrollment-token", status_code=201, summary="Generate enrollment token")
async def generate_enrollment_token(
    body: EnrollmentTokenRequest,
    current_user: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Generate a one-time enrollment token for a new agent. Admin only. FR-4.1."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=body.expires_in_minutes)

    # Persist in DB — survives Render restarts and cold-start wake-ups
    add_token(
        db=db,
        token_hash=token_hash,
        expires_at=expires_at,
        organization_id=str(current_user.organization_id),
        created_by_user_id=str(current_user.id),
        agent_name_hint=body.agent_name,
    )
    db.commit()
    # Never log raw_token
    return {"token": raw_token, "expires_at": expires_at.isoformat()}


# ---------------------------------------------------------------------------
# POST /agents/register  (no auth — uses enrollment token)
# ---------------------------------------------------------------------------

@router.post("/register", status_code=201, summary="Register a new agent")
async def register_agent(
    body: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Register a new agent using a one-time enrollment token. FR-4.2."""
    token_hash = hashlib.sha256(body.enrollment_token.encode()).hexdigest()
    token_data = consume_token(db=db, token_hash=token_hash)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "AGENT_NOT_AUTHORIZED",
                              "message": "Enrollment token is invalid or expired.",
                              "details": []}},
        )

    org_id = uuid.UUID(token_data["organization_id"])

    # Create agent row
    agent = Agent(
        organization_id=org_id,
        name=body.name,
        hostname=body.hostname,
        version=body.version,
        status="PENDING",
        is_active=True,
    )
    db.add(agent)
    db.flush()  # get agent.id without committing

    # Generate credential
    raw_credential = secrets.token_urlsafe(48)
    cred_hash = hashlib.sha256(raw_credential.encode()).hexdigest()
    credential = AgentCredential(
        agent_id=agent.id,
        credential_hash=cred_hash,
        type="token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        is_active=True,
    )
    db.add(credential)

    # Audit log
    _write_audit(db, org_id, "system", None, "agent_enrolled", "agents", agent.id,
                 {"name": agent.name, "hostname": agent.hostname})

    db.commit()
    db.refresh(agent)
    db.refresh(credential)

    # Never log raw_credential
    return {
        "id": str(agent.id),
        "organization_id": str(agent.organization_id),
        "name": agent.name,
        "hostname": agent.hostname,
        "status": agent.status,
        "version": agent.version,
        "credential": {
            "token": raw_credential,  # returned once — never stored in plaintext
            "expires_at": credential.expires_at.isoformat(),
        },
    }


# ---------------------------------------------------------------------------
# POST /agents/heartbeat  (Agent credential)
# ---------------------------------------------------------------------------

@router.post("/heartbeat", status_code=200, summary="Agent heartbeat")
async def agent_heartbeat(
    body: HeartbeatRequest,
    agent: Annotated[Agent, Depends(require_agent_credential)],
    db: Annotated[Session, Depends(get_db)],
):
    """Receive heartbeat from a running agent. FR-4.3."""
    # Validate agent_id in body matches credential's agent
    if body.agent_id != agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN",
                              "message": "agent_id does not match credential.",
                              "details": []}},
        )

    # Idempotency: skip if same (agent_id, timestamp) already exists
    existing = db.query(AgentHeartbeat).filter(
        AgentHeartbeat.agent_id == agent.id,
        AgentHeartbeat.timestamp == body.timestamp,
    ).first()
    if existing:
        return {"agent_id": str(agent.id), "status": agent.status,
                "last_heartbeat_at": agent.last_heartbeat_at.isoformat() if agent.last_heartbeat_at else None}

    # Save heartbeat
    heartbeat = AgentHeartbeat(
        agent_id=agent.id,
        organization_id=agent.organization_id,
        timestamp=body.timestamp,
        status=body.status,
        version=body.version,
        cpu_percent=body.cpu_percent,
        memory_percent=body.memory_percent,
        details=body.details,
    )
    db.add(heartbeat)

    # Update agent status
    agent.last_heartbeat_at = body.timestamp
    agent.status = "ONLINE"
    if body.version:
        agent.version = body.version

    # Periodically mark stale agents offline (runs on each heartbeat)
    _mark_stale_agents_offline(db, exclude_agent_id=agent.id)

    db.commit()

    return {
        "agent_id": str(agent.id),
        "status": agent.status,
        "last_heartbeat_at": agent.last_heartbeat_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# GET /agents/  (Admin + Analyst JWT)
# ---------------------------------------------------------------------------

@router.get("/", status_code=200, summary="List agents")
async def list_agents(
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List agents for the authenticated user's organization. Admin + Analyst. FR-4.7."""
    query = db.query(Agent).filter(
        Agent.organization_id == current_user.organization_id,
        Agent.deleted_at == None,
    )
    if status_filter:
        query = query.filter(Agent.status == status_filter)

    agents = query.order_by(Agent.created_at.desc()).offset(offset).limit(limit).all()

    return [
        {
            "id": str(a.id),
            "name": a.name,
            "hostname": a.hostname,
            "status": a.status,
            "version": a.version,
            "is_active": a.is_active,
            "last_heartbeat_at": a.last_heartbeat_at.isoformat() if a.last_heartbeat_at else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in agents
    ]


# ---------------------------------------------------------------------------
# GET /agents/tasks  (Agent credential)
# ---------------------------------------------------------------------------

@router.get("/tasks", status_code=200, summary="Get pending tasks")
async def get_tasks(
    agent: Annotated[Agent, Depends(require_agent_credential)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get pending tasks for the agent. FR-5.1."""
    tasks = db.query(Scan).filter(
        Scan.agent_id == agent.id,
        Scan.status == "PENDING",
        Scan.organization_id == agent.organization_id,
    ).all()
    
    return [
        {
            "id": str(t.id),
            "organization_id": str(t.organization_id),
            "agent_id": str(t.agent_id),
            "scan_type": t.scan_type,
            "status": t.status,
            "target_scope": t.target_scope,
            "created_at": t.created_at.isoformat(),
        }
        for t in tasks
    ]


# ---------------------------------------------------------------------------
# POST /agents/tasks/{task_id}/status  (Agent credential)
# ---------------------------------------------------------------------------

@router.post("/tasks/{task_id}/status", status_code=200, summary="Update task status")
async def update_task_status(
    task_id: uuid.UUID,
    body: TaskStatusUpdate,
    agent: Annotated[Agent, Depends(require_agent_credential)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update task status. FR-5.2."""
    scan = db.query(Scan).filter(Scan.id == task_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Task not found.", "details": []}})
    if scan.agent_id != agent.id:
        raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": "Task does not belong to agent.", "details": []}})
        
    scan.status = body.status
    if body.status == "RUNNING":
        scan.started_at = body.started_at or datetime.now(timezone.utc)
    elif body.status in ("COMPLETED", "FAILED"):
        scan.completed_at = datetime.now(timezone.utc)
        
    db.commit()
    db.refresh(scan)
    
    return {
        "id": str(scan.id),
        "status": scan.status,
        "updated_at": scan.updated_at.isoformat()
    }


# ---------------------------------------------------------------------------
# POST /agents/results  (Agent credential)
# ---------------------------------------------------------------------------

@router.post("/results", status_code=201, summary="Upload scan result")
async def upload_result(
    body: ResultUpload,
    agent: Annotated[Agent, Depends(require_agent_credential)],
    db: Annotated[Session, Depends(get_db)],
):
    """Upload result for a task. FR-5.3."""
    scan = db.query(Scan).filter(Scan.id == body.scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Task not found.", "details": []}})
    if scan.agent_id != agent.id:
        raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": "Task does not belong to agent.", "details": []}})
    
    # Idempotency check: if upload_id provided, check if already exists
    # This must happen BEFORE task state validation to allow retries of completed uploads
    if body.upload_id:
        existing = db.query(ScanResult).filter(ScanResult.upload_id == body.upload_id).first()
        if existing:
            # Return existing result without re-inserting
            return {
                "id": str(existing.id),
                "scan_id": str(existing.scan_id),
                "device_id": str(existing.device_id) if existing.device_id else None,
                "result_type": existing.result_type,
                "created_at": existing.created_at.isoformat(),
                "upload_id": existing.upload_id
            }
    
    # Validate task state - only accept results for RUNNING or PENDING tasks
    if scan.status not in ("PENDING", "RUNNING"):
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "INVALID_TASK_STATE", "message": f"Task is {scan.status}, cannot accept results.", "details": []}}
        )
    
    result = ScanResult(
        organization_id=agent.organization_id,
        scan_id=body.scan_id,
        device_id=body.device_id,
        upload_id=body.upload_id,
        result_type=body.result_type,
        raw_payload=body.raw_payload
    )
    db.add(result)
    
    # Update task state to COMPLETED after successful result upload
    scan.status = "COMPLETED"
    scan.completed_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(result)
    
    return {
        "id": str(result.id),
        "scan_id": str(result.scan_id),
        "device_id": str(result.device_id) if result.device_id else None,
        "result_type": result.result_type,
        "created_at": result.created_at.isoformat(),
        "upload_id": result.upload_id
    }


# ---------------------------------------------------------------------------
# Dynamic agent-ID routes
#
# Keep these after static Agent routes. FastAPI matches routes in declaration
# order, so declaring /{agent_id} above /tasks would interpret "tasks" as an
# agent ID instead of dispatching to the Agent task-list endpoint.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# GET /agents/{agent_id}  (Admin + Analyst JWT)
# ---------------------------------------------------------------------------

@router.get("/{agent_id}", status_code=200, summary="Get agent detail")
async def get_agent(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get a single agent with recent heartbeats. Admin + Analyst. FR-4.7."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id,
        Agent.deleted_at == None,
    ).first()

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND",
                              "message": "Agent not found.",
                              "details": []}},
        )

    recent_heartbeats = db.query(AgentHeartbeat).filter(
        AgentHeartbeat.agent_id == agent.id,
    ).order_by(AgentHeartbeat.timestamp.desc()).limit(10).all()

    return {
        "id": str(agent.id),
        "name": agent.name,
        "hostname": agent.hostname,
        "status": agent.status,
        "version": agent.version,
        "is_active": agent.is_active,
        "last_heartbeat_at": agent.last_heartbeat_at.isoformat() if agent.last_heartbeat_at else None,
        "created_at": agent.created_at.isoformat(),
        "updated_at": agent.updated_at.isoformat(),
        "recent_heartbeats": [
            {
                "id": str(h.id),
                "timestamp": h.timestamp.isoformat(),
                "status": h.status,
                "cpu_percent": float(h.cpu_percent) if h.cpu_percent is not None else None,
                "memory_percent": float(h.memory_percent) if h.memory_percent is not None else None,
                "details": h.details,
            }
            for h in recent_heartbeats
        ],
    }


# ---------------------------------------------------------------------------
# POST /agents/{agent_id}/revoke  (Admin JWT)
# ---------------------------------------------------------------------------

@router.post("/{agent_id}/revoke", status_code=200, summary="Revoke an agent")
async def revoke_agent(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Revoke an agent and deactivate all its credentials. Admin only. FR-4.5."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id,
        Agent.deleted_at == None,
    ).first()

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Agent not found.", "details": []}},
        )

    now = datetime.now(timezone.utc)

    # Revoke all credentials
    creds = db.query(AgentCredential).filter(AgentCredential.agent_id == agent.id).all()
    for cred in creds:
        cred.is_active = False
        cred.revoked_at = now

    # Deactivate agent
    agent.is_active = False
    agent.status = "OFFLINE"

    _write_audit(db, agent.organization_id, "user", current_user.id,
                 "agent_revoked", "agents", agent.id, {})

    db.commit()

    return {"id": str(agent.id), "is_active": False, "revoked_at": now.isoformat()}


# ---------------------------------------------------------------------------
# POST /agents/{agent_id}/rotate-credential  (Admin JWT)
# ---------------------------------------------------------------------------

@router.post("/{agent_id}/rotate-credential", status_code=200, summary="Rotate agent credential")
async def rotate_credential(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Rotate agent credentials. Admin only."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id,
        Agent.deleted_at == None
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Agent not found.", "details": []}})
        
    now = datetime.now(timezone.utc)
    
    # Revoke all credentials
    creds = db.query(AgentCredential).filter(AgentCredential.agent_id == agent.id, AgentCredential.is_active == True).all()
    for cred in creds:
        cred.is_active = False
        cred.revoked_at = now
        
    # Generate new credential
    raw_credential = secrets.token_urlsafe(48)
    cred_hash = hashlib.sha256(raw_credential.encode()).hexdigest()
    new_cred = AgentCredential(
        agent_id=agent.id,
        credential_hash=cred_hash,
        type="token",
        expires_at=now + timedelta(days=365),
        is_active=True,
    )
    db.add(new_cred)
    
    _write_audit(db, agent.organization_id, "user", current_user.id,
                 "agent_credential_rotated", "agents", agent.id, {})
                 
    db.commit()
    db.refresh(new_cred)
    
    return {
        "agent_id": str(agent.id),
        "credential_id": str(new_cred.id),
        "expires_at": new_cred.expires_at.isoformat(),
        "is_active": True
    }


# ---------------------------------------------------------------------------
# GET /agents/{agent_id}/network-stats  (Analyst+Admin JWT)
# ---------------------------------------------------------------------------

@router.get("/{agent_id}/network-stats", status_code=200, summary="Get agent network stats")
async def get_network_stats(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get agent network stats. Analyst+Admin."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id,
        Agent.deleted_at == None
    ).first()
    if not agent:
        raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": "Agent not found or access denied.", "details": []}})
        
    heartbeats = db.query(AgentHeartbeat).filter(AgentHeartbeat.agent_id == agent.id).order_by(AgentHeartbeat.timestamp.desc()).limit(10).all()
    
    return [
        {
            "id": str(h.id),
            "timestamp": h.timestamp.isoformat(),
            "cpu_percent": float(h.cpu_percent) if h.cpu_percent is not None else None,
            "memory_percent": float(h.memory_percent) if h.memory_percent is not None else None,
            "details": h.details
        }
        for h in heartbeats
    ]
