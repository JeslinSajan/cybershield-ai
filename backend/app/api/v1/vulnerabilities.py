"""
Vulnerabilities router — Phase 13.4.

Permission matrix (user-roles.md):
- View vulnerabilities: Administrator, Security Analyst, Viewer (get_any_authenticated_user)
- Write (create/update): Administrator, Security Analyst (get_current_analyst_or_admin)
"""

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_any_authenticated_user, get_current_analyst_or_admin
from app.models.scan import CVE, Vulnerability
from app.models.user import User

router = APIRouter()


@router.get("/", summary="List vulnerabilities")
async def list_vulnerabilities(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
    severity: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    device_id: Optional[uuid.UUID] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List vulnerabilities in the caller's organization with optional filters."""
    query = (
        db.query(Vulnerability, CVE.cve_id.label("cve_code"))
        .outerjoin(CVE, Vulnerability.cve_id == CVE.id)
        .filter(Vulnerability.organization_id == current_user.organization_id)
    )

    if severity:
        query = query.filter(Vulnerability.severity == severity)
    if status_filter:
        query = query.filter(Vulnerability.status == status_filter)
    if device_id:
        query = query.filter(Vulnerability.device_id == device_id)

    records = (
        query.order_by(Vulnerability.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(v.id),
            "organization_id": str(v.organization_id),
            "device_id": str(v.device_id),
            "scan_id": str(v.scan_id) if v.scan_id else None,
            "cve_id": str(v.cve_id) if v.cve_id else None,
            "cve_code": cve_code,
            "severity": v.severity,
            "score": float(v.score) if v.score is not None else None,
            "description": v.description,
            "recommendation": v.recommendation,
            "status": v.status,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "updated_at": v.updated_at.isoformat() if v.updated_at else None,
        }
        for v, cve_code in records
    ]


@router.get("/{vuln_id}", summary="Get vulnerability")
async def get_vulnerability(
    vuln_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve detail for a single vulnerability in the caller's organization."""
    record = (
        db.query(Vulnerability, CVE)
        .outerjoin(CVE, Vulnerability.cve_id == CVE.id)
        .filter(
            Vulnerability.id == vuln_id,
            Vulnerability.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Vulnerability not found.", "details": []}},
        )

    v, cve = record

    return {
        "id": str(v.id),
        "organization_id": str(v.organization_id),
        "device_id": str(v.device_id),
        "scan_id": str(v.scan_id) if v.scan_id else None,
        "cve_id": str(v.cve_id) if v.cve_id else None,
        "cve_code": cve.cve_id if cve else None,
        "severity": v.severity,
        "score": float(v.score) if v.score is not None else None,
        "description": v.description,
        "recommendation": v.recommendation,
        "status": v.status,
        "cve_details": {
            "cve_id": cve.cve_id,
            "severity": cve.severity,
            "cvss_score": float(cve.cvss_score) if cve.cvss_score is not None else None,
            "affected_service": cve.affected_service,
            "affected_version": cve.affected_version,
            "summary": cve.summary,
            "recommendation": cve.recommendation,
            "source": cve.source,
        } if cve else None,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "updated_at": v.updated_at.isoformat() if v.updated_at else None,
    }


@router.post("/", summary="Create vulnerability record")
async def create_vulnerability(
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
):
    """Placeholder for manual vulnerability registration."""
    return {"message": "Manual vulnerability creation is managed via vulnerability scans."}
