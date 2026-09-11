"""
Settings router — Phase 8 RBAC enforcement.

Permission matrix (user-roles.md):
- Manage System Settings: Administrator only (FR-3.3)
- View Audit Logs:        Administrator only

Business logic will be implemented in a future phase.
"""

from fastapi import APIRouter, Depends
from app.core.deps import require_role

router = APIRouter()

_admin_only = Depends(require_role("Administrator"))


@router.get("/", summary="Get system settings (Admin only)", dependencies=[_admin_only])
async def get_settings():
    return {"message": "Not implemented yet — future phase"}


@router.patch("/", summary="Update system settings (Admin only)", dependencies=[_admin_only])
async def update_settings():
    """Security Analyst and Viewer cannot manage settings — FR-3.3."""
    return {"message": "Not implemented yet — future phase"}


@router.get("/audit-logs", summary="View audit logs (Admin only)", dependencies=[_admin_only])
async def get_audit_logs():
    return {"message": "Not implemented yet — future phase"}
