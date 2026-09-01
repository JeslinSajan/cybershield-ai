from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_devices():
    """List devices - Phase 9"""
    return {"message": "Not implemented yet - Phase 9"}


@router.get("/{device_id}")
async def get_device(device_id: str):
    """Get device details - Phase 9"""
    return {"message": "Not implemented yet - Phase 9"}
