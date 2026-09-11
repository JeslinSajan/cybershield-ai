"""
Dashboard router — Phase 8 RBAC enforcement.

Permission matrix (user-roles.md):
- View Dashboard: Administrator, Security Analyst, Viewer (all roles)

Business logic will be implemented in Phase 17.
"""

from fastapi import APIRouter, Depends
from app.core.deps import get_any_authenticated_user

router = APIRouter()

_any_user = Depends(get_any_authenticated_user)


@router.get("/", summary="Get dashboard summary", dependencies=[_any_user])
async def get_dashboard():
    return {"message": "Not implemented yet — Phase 17"}
