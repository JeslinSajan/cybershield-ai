from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_users():
    """List users - Phase 8"""
    return {"message": "Not implemented yet - Phase 8"}


@router.post("/")
async def create_user():
    """Create user - Phase 8"""
    return {"message": "Not implemented yet - Phase 8"}
