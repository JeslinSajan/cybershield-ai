"""
Logs router — Phase 8 RBAC enforcement.

Permission matrix (user-roles.md):
- View logs: Administrator, Security Analyst, Viewer (read-only, may be restricted per settings)

Business logic will be implemented in Phase 13.
"""

from fastapi import APIRouter, Depends
from app.core.deps import get_any_authenticated_user

router = APIRouter()

_any_user = Depends(get_any_authenticated_user)


@router.get("/", summary="List logs", dependencies=[_any_user])
async def list_logs():
    return {"message": "Not implemented yet — Phase 13"}


@router.get("/{log_id}", summary="Get log entry", dependencies=[_any_user])
async def get_log(log_id: str):
    return {"message": "Not implemented yet — Phase 13"}
