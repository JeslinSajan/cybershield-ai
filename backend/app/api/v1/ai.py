"""
AI Security Assistant router — Phase 8 RBAC enforcement.

Permission matrix (user-roles.md):
- Use AI assistant: Administrator, Security Analyst
- Viewer: explicitly excluded

Business logic will be implemented in Phase 16.
"""

from fastapi import APIRouter, Depends
from app.core.deps import require_role

router = APIRouter()

_analyst_or_admin = Depends(require_role("Administrator", "Security Analyst"))


@router.get("/conversations", summary="List AI conversations", dependencies=[_analyst_or_admin])
async def list_conversations():
    return {"message": "Not implemented yet — Phase 16"}


@router.post("/conversations", summary="Start AI conversation", dependencies=[_analyst_or_admin])
async def create_conversation():
    return {"message": "Not implemented yet — Phase 16"}


@router.post("/conversations/{conversation_id}/messages", summary="Send AI message", dependencies=[_analyst_or_admin])
async def send_message(conversation_id: str):
    return {"message": "Not implemented yet — Phase 16"}
