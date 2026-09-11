"""
Reports router — Phase 8 RBAC enforcement.

Permission matrix (user-roles.md):
- View reports:     Administrator, Security Analyst, Viewer
- Generate reports: Administrator, Security Analyst

Business logic will be implemented in Phase 15.
"""

from fastapi import APIRouter, Depends
from app.core.deps import get_any_authenticated_user, require_role

router = APIRouter()

_any_user = Depends(get_any_authenticated_user)
_analyst_or_admin = Depends(require_role("Administrator", "Security Analyst"))


@router.get("/", summary="List reports", dependencies=[_any_user])
async def list_reports():
    return {"message": "Not implemented yet — Phase 15"}


@router.get("/{report_id}", summary="Get report", dependencies=[_any_user])
async def get_report(report_id: str):
    return {"message": "Not implemented yet — Phase 15"}


@router.post("/", summary="Generate report (Analyst/Admin only)", dependencies=[_analyst_or_admin])
async def generate_report():
    return {"message": "Not implemented yet — Phase 15"}
