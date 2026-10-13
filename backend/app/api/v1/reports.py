"""
Reports router — Phase 20 full implementation.

Permission matrix (user-roles.md):
- View reports list / detail: Administrator, Security Analyst, Viewer (get_any_authenticated_user)
- Generate report:            Administrator, Security Analyst (get_current_analyst_or_admin)
- Download report:            Administrator, Security Analyst (get_current_analyst_or_admin) - Viewer gets 403 FORBIDDEN

Endpoints:
- POST /reports/                    - Generate executive / compliance report (Analyst/Admin)
- GET  /reports/                    - List reports for organization (All roles)
- GET  /reports/{report_id}         - Retrieve report metadata (All roles)
- GET  /reports/{report_id}/download - Stream PDF or CSV document (Analyst/Admin)
"""

import os
import uuid
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_any_authenticated_user, get_current_analyst_or_admin
from app.models.report import Report
from app.models.system import AuditLog
from app.models.user import User
from app.services.report_service import report_service, REPORT_DIR

router = APIRouter()

VALID_REPORT_TYPES = {"security_overview", "vulnerability", "alert"}


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class GenerateReportRequest(BaseModel):
    type: str = Field(..., description="Report type: 'security_overview', 'vulnerability', or 'alert'")
    from_date: datetime = Field(..., description="ISO 8601 start timestamp of reporting window")
    to_date: datetime = Field(..., description="ISO 8601 end timestamp of reporting window")


class ReportResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_by_user_id: uuid.UUID
    report_type: str
    period_start: datetime
    period_end: datetime
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED, summary="Generate compliance or incident report")
async def generate_report(
    body: GenerateReportRequest,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Generate a new security report (PDF & CSV ready).
    Permitted roles: Administrator, Security Analyst.
    """
    clean_type = body.type.lower().strip()
    if clean_type not in VALID_REPORT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Invalid report type '{body.type}'. Must be one of: {', '.join(sorted(VALID_REPORT_TYPES))}.",
                    "details": [],
                }
            },
        )

    if body.from_date > body.to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "from_date must be earlier than or equal to to_date.",
                    "details": [],
                }
            },
        )

    # Instantiate Report DB record
    report = Report(
        organization_id=current_user.organization_id,
        created_by_user_id=current_user.id,
        report_type=clean_type,
        period_start=body.from_date,
        period_end=body.to_date,
        status="READY",
        mime_type="application/pdf",
    )
    db.add(report)
    db.flush()

    report.file_name = f"cybershield_report_{report.id}.pdf"

    # Generate initial PDF document
    try:
        report_service.generate_pdf(db=db, report=report)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": f"Failed generating PDF report: {str(e)}",
                    "details": [],
                }
            },
        )

    # Write AuditLog
    audit_log = AuditLog(
        organization_id=current_user.organization_id,
        actor_type="user",
        actor_id=current_user.id,
        action="report_generated",
        target_type="reports",
        target_id=report.id,
        details={
            "report_type": report.report_type,
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "file_name": report.file_name,
        },
    )
    db.add(audit_log)

    db.commit()
    db.refresh(report)

    return report


@router.get("/", response_model=List[ReportResponse], summary="List organization reports")
async def list_reports(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
    report_type: Optional[str] = Query(default=None, alias="type"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    List historical security reports for the authenticated user's organization.
    Permitted roles: Administrator, Security Analyst, Viewer.
    """
    query = db.query(Report).filter(Report.organization_id == current_user.organization_id)

    if report_type:
        query = query.filter(Report.report_type == report_type.lower().strip())

    reports = (
        query.order_by(Report.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return reports


@router.get("/{report_id}", response_model=ReportResponse, summary="Get report details")
async def get_report(
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Retrieve report metadata by ID.
    Permitted roles: Administrator, Security Analyst, Viewer.
    """
    report = (
        db.query(Report)
        .filter(
            Report.id == report_id,
            Report.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Report '{report_id}' was not found.",
                    "details": [],
                }
            },
        )
    return report


@router.get("/{report_id}/download", summary="Download report document (PDF / CSV)")
async def download_report(
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
    format: str = Query(default="pdf", pattern="^(pdf|csv)$"),
):
    """
    Download a security report in PDF or CSV format.
    Permitted roles: Administrator, Security Analyst. (Viewer receives 403 Forbidden).
    """
    report = (
        db.query(Report)
        .filter(
            Report.id == report_id,
            Report.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Report '{report_id}' was not found.",
                    "details": [],
                }
            },
        )

    clean_format = format.lower().strip()

    if clean_format == "csv":
        file_path = report_service.generate_csv(db=db, report=report)
        download_filename = f"cybershield_{report.report_type}_{report.id}.csv"
        return FileResponse(
            path=file_path,
            media_type="text/csv",
            filename=download_filename,
            headers={"Content-Disposition": f'attachment; filename="{download_filename}"'},
        )
    else:
        # Default PDF
        pdf_path = os.path.join(REPORT_DIR, f"cybershield_report_{report.id}.pdf")
        if not os.path.exists(pdf_path):
            pdf_path = report_service.generate_pdf(db=db, report=report)

        download_filename = f"cybershield_{report.report_type}_{report.id}.pdf"
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=download_filename,
            headers={"Content-Disposition": f'attachment; filename="{download_filename}"'},
        )
