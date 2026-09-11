"""
Agents router — Phase 8 RBAC enforcement.

Permission matrix (user-roles.md):
- View agents:             Administrator, Security Analyst, Viewer
- Register / Revoke agents: Administrator only

Business logic for agent management will be implemented in Phase 9.
Agent authentication uses a SEPARATE credential mechanism (not user JWT).
TODO Phase 9: Add Depends(get_current_agent) to agent-facing endpoints.
"""

from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.deps import get_any_authenticated_user, require_role
from app.models.user import User

router = APIRouter()

_any_user = Depends(get_any_authenticated_user)
_admin_only = Depends(require_role("Administrator"))


@router.get("/", summary="List agents", dependencies=[_any_user])
async def list_agents():
    """List agents — Phase 9 implementation pending."""
    return {"message": "Not implemented yet — Phase 9"}


@router.get("/{agent_id}", summary="Get agent", dependencies=[_any_user])
async def get_agent(agent_id: str):
    """Get a single agent — Phase 9 implementation pending."""
    return {"message": "Not implemented yet — Phase 9"}


@router.post("/", summary="Register agent (Admin only)", dependencies=[_admin_only])
async def register_agent():
    """Register agent — Phase 9 implementation pending. Administrator only."""
    return {"message": "Not implemented yet — Phase 9"}


@router.delete("/{agent_id}", summary="Revoke agent (Admin only)", dependencies=[_admin_only])
async def revoke_agent(agent_id: str):
    """Revoke agent — Phase 9 implementation pending. Administrator only."""
    return {"message": "Not implemented yet — Phase 9"}
