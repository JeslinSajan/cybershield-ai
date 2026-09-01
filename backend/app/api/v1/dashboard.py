from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
async def get_dashboard_summary():
    """Get dashboard summary - Phase 17"""
    return {"message": "Not implemented yet - Phase 17"}


@router.get("/trends")
async def get_dashboard_trends():
    """Get dashboard trends - Phase 17"""
    return {"message": "Not implemented yet - Phase 17"}
