from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_scans():
    """List scans - Phase 10"""
    return {"message": "Not implemented yet - Phase 10"}


@router.post("/")
async def create_scan():
    """Create scan - Phase 10"""
    return {"message": "Not implemented yet - Phase 10"}
