"""
Dashboard router — Consolidated Platform Telemetry and Summary.

Provides a unified bootstrap endpoint for the dashboard view, consolidating
agents, devices, vulnerabilities, scans, and security logs in a single query
to eliminate network latency and connection queueing.
"""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_any_authenticated_user
from app.models.agent import Agent
from app.models.device import Device
from app.models.log import Log
from app.models.scan import Scan, Vulnerability
from app.models.user import User

router = APIRouter()


@router.get("/", summary="Get consolidated dashboard summary")
async def get_dashboard_summary(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Return consolidated platform statistics, active agents, discovered devices,

    recent scans, vulnerabilities, and recent security logs for the caller's organization.
    """
    org_id = current_user.organization_id

    # 1. Monitored Agents
    agents = (
        db.query(Agent)
        .filter(Agent.organization_id == org_id, Agent.deleted_at.is_(None))
        .order_by(Agent.created_at.desc())
        .limit(20)
        .all()
    )
    agents_online = sum(1 for a in agents if a.status == "ONLINE")
    agents_total = len(agents)

    # 2. Discovered Devices
    devices = (
        db.query(Device)
        .filter(Device.organization_id == org_id, Device.deleted_at.is_(None))
        .order_by(Device.last_seen_at.desc())
        .limit(50)
        .all()
    )
    devices_online = sum(1 for d in devices if d.status == "online")
    devices_total = len(devices)

    # 3. Vulnerabilities Matrix
    vulns = (
        db.query(Vulnerability)
        .filter(Vulnerability.organization_id == org_id)
        .order_by(Vulnerability.created_at.desc())
        .limit(100)
        .all()
    )
    crit_count = sum(1 for v in vulns if v.severity and v.severity.lower() == "critical")
    high_count = sum(1 for v in vulns if v.severity and v.severity.lower() == "high")
    med_count = sum(1 for v in vulns if v.severity and v.severity.lower() == "medium")
    low_count = sum(1 for v in vulns if v.severity and v.severity.lower() == "low")

    # 4. Scans Pipeline
    scans = (
        db.query(Scan)
        .filter(Scan.organization_id == org_id)
        .order_by(Scan.created_at.desc())
        .limit(20)
        .all()
    )
    scans_in_progress = sum(1 for s in scans if s.status in ("PENDING", "RUNNING"))
    scans_total = len(scans)

    # 5. Recent Security Logs
    logs = (
        db.query(Log)
        .filter(Log.organization_id == org_id)
        .order_by(Log.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "summary": {
            "agents_online": agents_online,
            "agents_total": agents_total,
            "devices_online": devices_online,
            "devices_total": devices_total,
            "critical_vulns": crit_count,
            "high_vulns": high_count,
            "medium_vulns": med_count,
            "low_vulns": low_count,
            "scans_in_progress": scans_in_progress,
            "scans_total": scans_total,
        },
        "agents": [
            {
                "id": str(a.id),
                "name": a.name,
                "hostname": a.hostname,
                "status": a.status,
                "version": a.version,
                "is_active": a.is_active,
                "last_heartbeat_at": a.last_heartbeat_at.isoformat() if a.last_heartbeat_at else None,
                "created_at": a.created_at.isoformat(),
            }
            for a in agents
        ],
        "devices": [
            {
                "id": str(d.id),
                "ip_address": d.ip_address,
                "mac_address": d.mac_address,
                "hostname": d.hostname,
                "vendor": d.vendor,
                "status": d.status,
                "device_type": d.device_type,
                "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
            }
            for d in devices
        ],
        "vulnerabilities": [
            {
                "id": str(v.id),
                "severity": v.severity,
                "score": float(v.score) if v.score else None,
                "description": v.description,
                "recommendation": v.recommendation,
                "status": v.status,
                "device_id": str(v.device_id),
                "cve_id": str(v.cve_id) if v.cve_id else None,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in vulns
        ],
        "scans": [
            {
                "id": str(s.id),
                "scan_type": s.scan_type,
                "status": s.status,
                "target_scope": s.target_scope,
                "agent_id": str(s.agent_id) if s.agent_id else None,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in scans
        ],
        "recent_logs": [
            {
                "id": str(l.id),
                "source": l.source,
                "event_type": l.event_type,
                "severity": l.severity,
                "username": l.username,
                "source_ip": str(l.source_ip) if l.source_ip else None,
                "message": l.message,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in logs
        ],
    }
