"""
Threat Detection Service for CyberShield AI (Phase 15).

Implements 3 detection rules:
- Rule 1: Brute Force — 5+ login_failure events from the same source_ip within 10 minutes.
- Rule 2: Port Scan — scan result indicates 10+ open ports on a device.
- Rule 3: Suspicious Login — login_success from an IP with 3+ login_failure events in the last hour.

Provides alert deduplication (1-hour window for Open/Acknowledged alerts),
system AuditLog generation, and notification dispatch for High/Critical alerts.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.log import Log
from app.models.scan import ScanResult
from app.models.system import AuditLog, Notification
from app.models.user import User

logger = logging.getLogger("app.services.detection")


def create_alert(
    db: Session,
    organization_id: uuid.UUID,
    alert_type: str,
    severity: str,
    description: str,
    risk_score: float,
    agent_id: Optional[uuid.UUID] = None,
    device_id: Optional[uuid.UUID] = None,
    source_ip: Optional[str] = None,
) -> Optional[Alert]:
    """
    Create a new Alert record if not duplicate, create system AuditLog,
    and dispatch Notifications to active users for High/Critical severity.
    """
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    # 1. Deduplication check: 1-hour window on Open / Acknowledged alerts
    dedup_query = db.query(Alert).filter(
        Alert.organization_id == organization_id,
        Alert.alert_type == alert_type,
        Alert.status.in_(["Open", "Acknowledged"]),
        Alert.triggered_at >= one_hour_ago,
    )
    if agent_id:
        dedup_query = dedup_query.filter(Alert.agent_id == agent_id)
    if device_id:
        dedup_query = dedup_query.filter(Alert.device_id == device_id)
    if source_ip:
        dedup_query = dedup_query.filter(Alert.description.contains(source_ip))

    existing = dedup_query.first()
    if existing:
        logger.info(
            f"Deduplication: active {alert_type} alert already exists for org {organization_id} (ID: {existing.id})"
        )
        return None

    # 2. Create Alert
    alert = Alert(
        organization_id=organization_id,
        agent_id=agent_id,
        device_id=device_id,
        alert_type=alert_type,
        severity=severity,
        status="Open",
        description=description,
        risk_score=risk_score,
        triggered_at=now,
    )
    db.add(alert)
    db.flush()

    # 3. Create AuditLog entry
    audit = AuditLog(
        organization_id=organization_id,
        actor_type="system",
        actor_id=None,
        action="alert_created",
        target_type="alerts",
        target_id=alert.id,
        details={
            "alert_type": alert_type,
            "severity": severity,
            "risk_score": float(risk_score),
            "description": description,
        },
    )
    db.add(audit)

    # 4. Dispatch Notifications for High / Critical severity alerts
    if severity.lower() in ("high", "critical"):
        active_users = (
            db.query(User)
            .filter(
                User.organization_id == organization_id,
                User.is_active == True,
                User.deleted_at.is_(None),
            )
            .all()
        )
        for user in active_users:
            notification = Notification(
                organization_id=organization_id,
                user_id=user.id,
                alert_id=alert.id,
                notification_type="alert",
                channel="dashboard",
                title=f"{severity} Alert: {alert_type.replace('_', ' ').title()}",
                body=description,
                is_read=False,
            )
            db.add(notification)

    db.flush()
    logger.info(f"Created {severity} alert '{alert_type}' (ID: {alert.id}) for org {organization_id}")
    return alert


def check_brute_force(
    db: Session,
    org_id: uuid.UUID,
    agent_id: Optional[uuid.UUID],
    source_ip: str,
    device_id: Optional[uuid.UUID] = None,
) -> Optional[Alert]:
    """
    Rule 1: Brute Force.
    5+ login_failure logs from the same source_ip within 10 minutes -> High alert (risk 40).
    """
    ten_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=10)

    count = (
        db.query(Log)
        .filter(
            Log.organization_id == org_id,
            Log.source_ip == source_ip,
            Log.event_type == "login_failure",
            Log.timestamp >= ten_minutes_ago,
        )
        .count()
    )

    if count >= 5:
        return create_alert(
            db=db,
            organization_id=org_id,
            alert_type="brute_force",
            severity="High",
            description=f"Brute force detected from {source_ip} ({count} failed logins within 10 minutes)",
            risk_score=40.0,
            agent_id=agent_id,
            device_id=device_id,
            source_ip=source_ip,
        )
    return None


def check_port_scan(
    db: Session,
    org_id: uuid.UUID,
    agent_id: Optional[uuid.UUID],
    scan_result: ScanResult,
) -> Optional[Alert]:
    """
    Rule 2: Port Scan.
    Scan result shows 10+ open ports on one device -> Medium alert (risk 20).
    """
    payload = scan_result.raw_payload or {}
    services = payload.get("services") or []
    target_ip = payload.get("target_ip")

    open_ports = [s for s in services if s.get("state") == "open" or s.get("port") is not None]
    if len(open_ports) >= 10:
        target_name = target_ip or (str(scan_result.device_id) if scan_result.device_id else "host")
        return create_alert(
            db=db,
            organization_id=org_id,
            alert_type="port_scan",
            severity="Medium",
            description=f"Port scan detected on device {target_name}: {len(open_ports)} open ports discovered",
            risk_score=20.0,
            agent_id=agent_id,
            device_id=scan_result.device_id,
            source_ip=target_ip,
        )
    return None


def check_suspicious_login(
    db: Session,
    org_id: uuid.UUID,
    agent_id: Optional[uuid.UUID],
    source_ip: str,
    username: Optional[str] = None,
    device_id: Optional[uuid.UUID] = None,
) -> Optional[Alert]:
    """
    Rule 3: Suspicious Login.
    login_success from an IP with 3+ login_failure events in the last hour -> High alert (risk 40).
    """
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

    failure_count = (
        db.query(Log)
        .filter(
            Log.organization_id == org_id,
            Log.source_ip == source_ip,
            Log.event_type == "login_failure",
            Log.timestamp >= one_hour_ago,
        )
        .count()
    )

    if failure_count >= 3:
        user_name = username or "unknown"
        return create_alert(
            db=db,
            organization_id=org_id,
            alert_type="suspicious_login",
            severity="High",
            description=(
                f"Suspicious login for user '{user_name}' from {source_ip} "
                f"following {failure_count} recent failed login attempts"
            ),
            risk_score=40.0,
            agent_id=agent_id,
            device_id=device_id,
            source_ip=source_ip,
        )
    return None


def process_log_detections(
    db: Session,
    org_id: uuid.UUID,
    agent_id: Optional[uuid.UUID],
    logs: List[Log],
) -> List[Alert]:
    """Evaluate log events synchronously and return any triggered alerts."""
    created_alerts = []
    # Avoid re-evaluating the same IP repeatedly in a single batch
    checked_brute_force_ips = set()
    checked_suspicious_ips = set()

    for entry in logs:
        ip = str(entry.source_ip) if entry.source_ip else None
        if not ip:
            continue

        if entry.event_type == "login_failure" and ip not in checked_brute_force_ips:
            checked_brute_force_ips.add(ip)
            alert = check_brute_force(
                db=db,
                org_id=org_id,
                agent_id=agent_id,
                source_ip=ip,
                device_id=entry.device_id,
            )
            if alert:
                created_alerts.append(alert)

        elif entry.event_type == "login_success" and ip not in checked_suspicious_ips:
            checked_suspicious_ips.add(ip)
            alert = check_suspicious_login(
                db=db,
                org_id=org_id,
                agent_id=agent_id,
                source_ip=ip,
                username=entry.username,
                device_id=entry.device_id,
            )
            if alert:
                created_alerts.append(alert)

    return created_alerts


def process_scan_detections(
    db: Session,
    org_id: uuid.UUID,
    agent_id: Optional[uuid.UUID],
    scan_result: ScanResult,
) -> List[Alert]:
    """Evaluate scan results synchronously and return any triggered alerts."""
    created_alerts = []
    alert = check_port_scan(
        db=db,
        org_id=org_id,
        agent_id=agent_id,
        scan_result=scan_result,
    )
    if alert:
        created_alerts.append(alert)
    return created_alerts
