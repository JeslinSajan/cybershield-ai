"""
Alerts router — Phase 8 RBAC enforcement.

Permission matrix (user-roles.md):
- View alerts:              Administrator, Security Analyst, Viewer
- Investigate/Update alerts: Administrator, Security Analyst (Viewer excluded — FR-3.2)

Business logic will be implemented in Phase 14.
"""

from fastapi import APIRouter, Depends
from app.core.deps import get_any_authenticated_user, require_role

router = APIRouter()

_any_user = Depends(get_any_authenticated_user)
_analyst_or_admin = Depends(require_role("Administrator", "Security Analyst"))


@router.get("/", summary="List alerts", dependencies=[_any_user])
async def list_alerts():
    return {"message": "Not implemented yet — Phase 14"}


@router.get("/{alert_id}", summary="Get alert", dependencies=[_any_user])
async def get_alert(alert_id: str):
    return {"message": "Not implemented yet — Phase 14"}


@router.patch("/{alert_id}", summary="Update alert status (Analyst/Admin only)", dependencies=[_analyst_or_admin])
async def update_alert(alert_id: str):
    """Viewer cannot update alert status — FR-3.2."""
    return {"message": "Not implemented yet — Phase 14"}
