from fastapi import APIRouter

router = APIRouter()


@router.post("/explain")
async def explain():
    """AI explanation - Phase 15"""
    return {"message": "Not implemented yet - Phase 15"}


@router.get("/conversations")
async def list_conversations():
    """List AI conversations - Phase 15"""
    return {"message": "Not implemented yet - Phase 15"}
