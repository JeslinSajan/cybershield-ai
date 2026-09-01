from fastapi import APIRouter

router = APIRouter()


@router.get("/indicators")
async def list_indicators():
    """List threat indicators - Phase 13"""
    return {"message": "Not implemented yet - Phase 13"}


@router.post("/indicators")
async def create_indicator():
    """Create threat indicator - Phase 13"""
    return {"message": "Not implemented yet - Phase 13"}
