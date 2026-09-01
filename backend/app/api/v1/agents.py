from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_agents():
    """List agents - Phase 9"""
    return {"message": "Not implemented yet - Phase 9"}


@router.post("/")
async def create_agent():
    """Create agent - Phase 9"""
    return {"message": "Not implemented yet - Phase 9"}
