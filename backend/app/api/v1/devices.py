"""
Devices router — Phase 8 RBAC enforcement.

Permission matrix (user-roles.md):
- View devices:  Administrator, Security Analyst, Viewer
- Write devices: Administrator, Security Analyst (discovery results from agents)

Business logic will be implemented in Phase 11.
"""

from fastapi import APIRouter, Depends
from app.core.deps import get_any_authenticated_user, require_role

router = APIRouter()

_any_user = Depends(get_any_authenticated_user)
_analyst_or_admin = Depends(require_role("Administrator", "Security Analyst"))


@router.get("/", summary="List devices", dependencies=[_any_user])
async def list_devices():
    return {"message": "Not implemented yet — Phase 11"}


@router.get("/{device_id}", summary="Get device", dependencies=[_any_user])
async def get_device(device_id: str):
    return {"message": "Not implemented yet — Phase 11"}


@router.post("/", summary="Create/update device", dependencies=[_analyst_or_admin])
async def create_device():
    return {"message": "Not implemented yet — Phase 11"}
