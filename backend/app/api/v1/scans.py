"""
Scans router — Phase 8 RBAC enforcement.

Permission matrix (user-roles.md):
- View scans: Administrator, Security Analyst, Viewer
- Run scans:  Administrator, Security Analyst (Viewer is explicitly excluded — FR-3.2)

Business logic will be implemented in Phase 12.
"""

from fastapi import APIRouter, Depends
from app.core.deps import get_any_authenticated_user, require_role

router = APIRouter()

_any_user = Depends(get_any_authenticated_user)
_analyst_or_admin = Depends(require_role("Administrator", "Security Analyst"))


@router.get("/", summary="List scans", dependencies=[_any_user])
async def list_scans():
    return {"message": "Not implemented yet — Phase 12"}


@router.get("/{scan_id}", summary="Get scan", dependencies=[_any_user])
async def get_scan(scan_id: str):
    return {"message": "Not implemented yet — Phase 12"}


@router.post("/", summary="Start a scan (Analyst/Admin only)", dependencies=[_analyst_or_admin])
async def start_scan():
    """Viewer cannot run scans — FR-3.2."""
    return {"message": "Not implemented yet — Phase 12"}
