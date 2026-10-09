"""
Devices router — Device inventory and management (Phase 11).

Permission matrix (user-roles.md):
- View devices: Administrator, Security Analyst, Viewer
- Write devices: Administrator, Security Analyst
"""

import json
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import nullslast
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_any_authenticated_user, get_current_analyst_or_admin
from app.models.device import Device
from app.models.scan import CVE, Vulnerability
from app.models.user import User
from app.services.risk_service import get_latest_device_risk

router = APIRouter()


@router.get("/", summary="List devices")
async def list_devices(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List discovered devices in the caller's organization."""
    query = db.query(Device).filter(
        Device.organization_id == current_user.organization_id,
        Device.deleted_at.is_(None),
    )
    if status_filter:
        query = query.filter(Device.status == status_filter)

    devices = (
        query.order_by(nullslast(Device.last_seen_at.desc()), Device.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(d.id),
            "organization_id": str(d.organization_id),
            "agent_id": str(d.agent_id) if d.agent_id else None,
            "ip_address": str(d.ip_address),
            "mac_address": d.mac_address,
            "hostname": d.hostname,
            "vendor": d.vendor,
            "device_type": d.device_type,
            "status": d.status,
            "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        }
        for d in devices
    ]


@router.get("/{device_id}", summary="Get device detail")
async def get_device(
    device_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve detail for a single device in the caller's organization."""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.organization_id == current_user.organization_id,
        Device.deleted_at.is_(None),
    ).first()

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Device not found.", "details": []}},
        )

    return {
        "id": str(device.id),
        "organization_id": str(device.organization_id),
        "agent_id": str(device.agent_id) if device.agent_id else None,
        "ip_address": str(device.ip_address),
        "mac_address": device.mac_address,
        "hostname": device.hostname,
        "vendor": device.vendor,
        "device_type": device.device_type,
        "status": device.status,
        "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
        "created_at": device.created_at.isoformat() if device.created_at else None,
        "updated_at": device.updated_at.isoformat() if device.updated_at else None,
    }


@router.get("/{device_id}/risk", summary="Get device risk score")
async def get_device_risk(
    device_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve the latest dynamic risk score and factor breakdown for a device."""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.organization_id == current_user.organization_id,
        Device.deleted_at.is_(None),
    ).first()

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Device not found.", "details": []}},
        )

    risk = get_latest_device_risk(db, device.id, current_user.organization_id)
    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Risk score not available for this device.", "details": []}},
        )

    try:
        breakdown = json.loads(risk.factor_breakdown) if risk.factor_breakdown else {}
    except Exception:
        breakdown = {}

    return {
        "id": str(risk.id),
        "organization_id": str(risk.organization_id),
        "entity_type": risk.entity_type,
        "entity_id": str(risk.entity_id),
        "device_id": str(risk.entity_id),
        "score": float(risk.score),
        "risk_band": risk.risk_band,
        "factor_breakdown": breakdown,
        "formula_version": risk.formula_version,
        "created_at": risk.created_at.isoformat() if risk.created_at else None,
        "updated_at": risk.updated_at.isoformat() if risk.updated_at else None,
    }


@router.get("/{device_id}/vulnerabilities", summary="Get device vulnerabilities")
async def get_device_vulnerabilities(
    device_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve all vulnerabilities discovered for a specific device."""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.organization_id == current_user.organization_id,
        Device.deleted_at.is_(None),
    ).first()

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Device not found.", "details": []}},
        )

    records = (
        db.query(Vulnerability, CVE.cve_id.label("cve_code"))
        .outerjoin(CVE, Vulnerability.cve_id == CVE.id)
        .filter(
            Vulnerability.device_id == device.id,
            Vulnerability.organization_id == current_user.organization_id,
        )
        .order_by(Vulnerability.created_at.desc())
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
            "summary": v.description,
            "recommendation": v.recommendation,
            "status": v.status,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "updated_at": v.updated_at.isoformat() if v.updated_at else None,
        }
        for v, cve_code in records
    ]


@router.post("/", summary="Create/update device")
async def create_device(
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
):
    """Placeholder for manual device registration."""
    return {"message": "Manual device creation is managed via discovery scans."}
