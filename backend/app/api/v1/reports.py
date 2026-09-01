from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_reports():
    """List reports - Phase 14"""
    return {"message": "Not implemented yet - Phase 14"}


@router.post("/")
async def create_report():
    """Create report - Phase 14"""
    return {"message": "Not implemented yet - Phase 14"}
