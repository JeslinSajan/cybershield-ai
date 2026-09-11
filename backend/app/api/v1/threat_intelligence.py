"""
Threat Intelligence router — Phase 8 RBAC enforcement.

Permission matrix (user-roles.md):
- View threat indicators: Administrator, Security Analyst, Viewer
- Write (add indicators):  Administrator, Security Analyst

Business logic will be implemented in Phase 14.
"""

from fastapi import APIRouter, Depends
from app.core.deps import get_any_authenticated_user, require_role

router = APIRouter()

_any_user = Depends(get_any_authenticated_user)
_analyst_or_admin = Depends(require_role("Administrator", "Security Analyst"))


@router.get("/", summary="List threat indicators", dependencies=[_any_user])
async def list_indicators():
    return {"message": "Not implemented yet — Phase 14"}


@router.get("/{indicator_id}", summary="Get threat indicator", dependencies=[_any_user])
async def get_indicator(indicator_id: str):
    return {"message": "Not implemented yet — Phase 14"}


@router.post("/", summary="Add threat indicator", dependencies=[_analyst_or_admin])
async def create_indicator():
    return {"message": "Not implemented yet — Phase 14"}
