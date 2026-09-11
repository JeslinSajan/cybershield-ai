"""
Vulnerabilities router — Phase 8 RBAC enforcement.

Permission matrix (user-roles.md):
- View vulnerabilities: Administrator, Security Analyst, Viewer
- Write (create/update): Administrator, Security Analyst

Business logic will be implemented in Phase 12.
"""

from fastapi import APIRouter, Depends
from app.core.deps import get_any_authenticated_user, require_role

router = APIRouter()

_any_user = Depends(get_any_authenticated_user)
_analyst_or_admin = Depends(require_role("Administrator", "Security Analyst"))


@router.get("/", summary="List vulnerabilities", dependencies=[_any_user])
async def list_vulnerabilities():
    return {"message": "Not implemented yet — Phase 12"}


@router.get("/{vuln_id}", summary="Get vulnerability", dependencies=[_any_user])
async def get_vulnerability(vuln_id: str):
    return {"message": "Not implemented yet — Phase 12"}


@router.post("/", summary="Create vulnerability record", dependencies=[_analyst_or_admin])
async def create_vulnerability():
    return {"message": "Not implemented yet — Phase 12"}
