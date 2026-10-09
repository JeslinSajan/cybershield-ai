"""
Risk Scoring Engine for CyberShield AI (Phase 17).

Formula specification (v1):
- vulnerability_score:
    Critical vuln: +30 (subtotal capped at 30)
    High vuln:     +15 (subtotal capped at 30)
    Medium vuln:   +5  (subtotal capped at 15)
    Low vuln:      +2  (subtotal capped at 5)
    Maximum vulnerability subtotal: 80.0
- alert_score:
    Open brute_force alert:       +20
    Open suspicious_login alert:  +15
    Open port_scan alert:         +10
- exposure_score:
    10+ open ports in latest scan result for device: +10
- Total score capped at 100.0 (minimum 0.0).
- Bands:
    0 - 24:   Low
    25 - 49:  Medium
    50 - 74:  High
    75 - 100: Critical

CRITICAL: RiskScore.factor_breakdown is Column(Text).
It MUST be serialized as a JSON string with json.dumps(dict) before persisting.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.models.alert import Alert, RiskScore
from app.models.device import Device
from app.models.scan import ScanResult, Vulnerability

logger = logging.getLogger("app.services.risk")

FORMULA_VERSION = "v1"

# Scoring weights & caps
VULN_WEIGHTS = {
    "critical": (30.0, 30.0),  # (points_per_item, max_cap)
    "high": (15.0, 30.0),
    "medium": (5.0, 15.0),
    "low": (2.0, 5.0),
}

ALERT_WEIGHTS = {
    "brute_force": 20.0,
    "suspicious_login": 15.0,
    "port_scan": 10.0,
}

EXPOSURE_THRESHOLD = 10
EXPOSURE_POINTS = 10.0


def determine_risk_band(score: float) -> str:
    """Classify numerical risk score into standardized risk band."""
    if score >= 75.0:
        return "Critical"
    elif score >= 50.0:
        return "High"
    elif score >= 25.0:
        return "Medium"
    else:
        return "Low"


def calculate_device_risk(
    db: Session,
    device_id: uuid.UUID,
    org_id: uuid.UUID,
) -> Optional[RiskScore]:
    """
    Calculate and persist dynamic risk score for a target device.
    
    1. Tallies open vulnerabilities with severity caps.
    2. Tallies active (Open) alerts by detection rule.
    3. Evaluates port exposure from the most recent scan result.
    4. Serializes factor breakdown to JSON string.
    5. Saves new RiskScore record and backfills alerts.risk_score for open alerts.
    """
    device = (
        db.query(Device)
        .filter(
            Device.id == device_id,
            Device.organization_id == org_id,
            Device.deleted_at.is_(None),
        )
        .first()
    )

    if not device:
        logger.warning(f"Device {device_id} not found in org {org_id} for risk calculation")
        return None

    # 1. Vulnerability Scoring
    open_vulns = (
        db.query(Vulnerability)
        .filter(
            Vulnerability.device_id == device_id,
            Vulnerability.organization_id == org_id,
            Vulnerability.status == "open",
        )
        .all()
    )

    crit_count = sum(1 for v in open_vulns if (v.severity or "").lower() == "critical")
    high_count = sum(1 for v in open_vulns if (v.severity or "").lower() == "high")
    med_count = sum(1 for v in open_vulns if (v.severity or "").lower() == "medium")
    low_count = sum(1 for v in open_vulns if (v.severity or "").lower() == "low")

    crit_score = min(VULN_WEIGHTS["critical"][1], crit_count * VULN_WEIGHTS["critical"][0])
    high_score = min(VULN_WEIGHTS["high"][1], high_count * VULN_WEIGHTS["high"][0])
    med_score = min(VULN_WEIGHTS["medium"][1], med_count * VULN_WEIGHTS["medium"][0])
    low_score = min(VULN_WEIGHTS["low"][1], low_count * VULN_WEIGHTS["low"][0])

    total_vuln_score = crit_score + high_score + med_score + low_score

    # 2. Alert Scoring
    open_alerts = (
        db.query(Alert)
        .filter(
            Alert.device_id == device_id,
            Alert.organization_id == org_id,
            Alert.status.in_(["Open", "open"]),
        )
        .all()
    )

    bf_count = sum(1 for a in open_alerts if a.alert_type == "brute_force")
    sl_count = sum(1 for a in open_alerts if a.alert_type == "suspicious_login")
    ps_count = sum(1 for a in open_alerts if a.alert_type == "port_scan")

    bf_score = bf_count * ALERT_WEIGHTS["brute_force"]
    sl_score = sl_count * ALERT_WEIGHTS["suspicious_login"]
    ps_score = ps_count * ALERT_WEIGHTS["port_scan"]

    total_alert_score = bf_score + sl_score + ps_score

    # 3. Exposure Scoring
    latest_scan = (
        db.query(ScanResult)
        .filter(
            ScanResult.device_id == device_id,
            ScanResult.organization_id == org_id,
            ScanResult.result_type == "services",
        )
        .order_by(ScanResult.created_at.desc())
        .first()
    )

    open_ports_count = 0
    if latest_scan and latest_scan.raw_payload:
        services = latest_scan.raw_payload.get("services") or []
        open_ports = [s for s in services if s.get("state") == "open" or s.get("port") is not None]
        open_ports_count = len(open_ports)

    exposure_score = EXPOSURE_POINTS if open_ports_count >= EXPOSURE_THRESHOLD else 0.0

    # 4. Total and Band
    raw_total = total_vuln_score + total_alert_score + exposure_score
    total_score = round(min(100.0, max(0.0, float(raw_total))), 2)
    risk_band = determine_risk_band(total_score)

    # 5. Factor Breakdown (JSON String)
    breakdown_dict = {
        "vulnerabilities": {
            "critical_count": crit_count,
            "critical_score": crit_score,
            "high_count": high_count,
            "high_score": high_score,
            "medium_count": med_count,
            "medium_score": med_score,
            "low_count": low_count,
            "low_score": low_score,
            "subtotal": total_vuln_score,
        },
        "alerts": {
            "brute_force_count": bf_count,
            "brute_force_score": bf_score,
            "suspicious_login_count": sl_count,
            "suspicious_login_score": sl_score,
            "port_scan_count": ps_count,
            "port_scan_score": ps_score,
            "subtotal": total_alert_score,
        },
        "exposure": {
            "open_ports_count": open_ports_count,
            "exposure_score": exposure_score,
        },
        "raw_total": raw_total,
        "total_score": total_score,
        "risk_band": risk_band,
        "formula_version": FORMULA_VERSION,
    }
    factor_breakdown_str = json.dumps(breakdown_dict)

    now = datetime.now(timezone.utc)

    # 6. Upsert RiskScore row for device
    risk_score_row = (
        db.query(RiskScore)
        .filter(
            RiskScore.organization_id == org_id,
            RiskScore.entity_type == "device",
            RiskScore.entity_id == device_id,
        )
        .order_by(RiskScore.updated_at.desc())
        .first()
    )

    if risk_score_row:
        risk_score_row.score = total_score
        risk_score_row.risk_band = risk_band
        risk_score_row.factor_breakdown = factor_breakdown_str
        risk_score_row.formula_version = FORMULA_VERSION
        risk_score_row.updated_at = now
    else:
        risk_score_row = RiskScore(
            organization_id=org_id,
            entity_type="device",
            entity_id=device_id,
            score=total_score,
            risk_band=risk_band,
            factor_breakdown=factor_breakdown_str,
            formula_version=FORMULA_VERSION,
            created_at=now,
            updated_at=now,
        )
        db.add(risk_score_row)

    # 7. Backfill open alerts with missing or zero risk score for this device
    db.query(Alert).filter(
        Alert.organization_id == org_id,
        Alert.device_id == device_id,
        Alert.status.in_(["Open", "open"]),
        (Alert.risk_score == None) | (Alert.risk_score == 0),
    ).update({Alert.risk_score: total_score}, synchronize_session=False)

    db.commit()
    db.refresh(risk_score_row)

    logger.info(
        f"Calculated risk score for device {device_id}: {total_score} ({risk_band}) "
        f"[vuln={total_vuln_score}, alert={total_alert_score}, exp={exposure_score}]"
    )

    return risk_score_row


def get_latest_device_risk(
    db: Session,
    device_id: uuid.UUID,
    org_id: uuid.UUID,
) -> Optional[RiskScore]:
    """
    Retrieve the most recent RiskScore for a device, or calculate on-demand if none exists.
    """
    existing = (
        db.query(RiskScore)
        .filter(
            RiskScore.entity_type == "device",
            RiskScore.entity_id == device_id,
            RiskScore.organization_id == org_id,
        )
        .order_by(RiskScore.updated_at.desc())
        .first()
    )
    if existing:
        return existing

    # Calculate on-demand if device exists
    return calculate_device_risk(db, device_id, org_id)


def get_all_devices_risk(
    db: Session,
    org_id: uuid.UUID,
) -> List[Dict]:
    """
    Retrieve latest risk score summary for all devices in the organization,
    sorted by score descending.
    """
    devices = (
        db.query(Device)
        .filter(
            Device.organization_id == org_id,
            Device.deleted_at.is_(None),
        )
        .all()
    )

    results = []
    for d in devices:
        risk = get_latest_device_risk(db, d.id, org_id)
        if risk:
            # Parse breakdown if available
            try:
                breakdown = json.loads(risk.factor_breakdown) if risk.factor_breakdown else {}
            except Exception:
                breakdown = {}

            results.append({
                "id": str(risk.id),
                "device_id": str(d.id),
                "device_ip": str(d.ip_address) if d.ip_address else None,
                "device_hostname": d.hostname,
                "device_type": d.device_type,
                "organization_id": str(org_id),
                "score": float(risk.score),
                "risk_band": risk.risk_band,
                "factor_breakdown": breakdown,
                "formula_version": risk.formula_version,
                "created_at": risk.created_at.isoformat() if risk.created_at else None,
                "updated_at": risk.updated_at.isoformat() if risk.updated_at else None,
            })
        else:
            results.append({
                "id": None,
                "device_id": str(d.id),
                "device_ip": str(d.ip_address) if d.ip_address else None,
                "device_hostname": d.hostname,
                "device_type": d.device_type,
                "organization_id": str(org_id),
                "score": 0.0,
                "risk_band": "Low",
                "factor_breakdown": {},
                "formula_version": FORMULA_VERSION,
                "created_at": None,
                "updated_at": None,
            })

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
