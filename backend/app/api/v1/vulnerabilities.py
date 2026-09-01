from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_vulnerabilities():
    """List vulnerabilities - Phase 10"""
    return {"message": "Not implemented yet - Phase 10"}


@router.get("/{vulnerability_id}")
async def get_vulnerability(vulnerability_id: str):
    """Get vulnerability details - Phase 10"""
    return {"message": "Not implemented yet - Phase 10"}
