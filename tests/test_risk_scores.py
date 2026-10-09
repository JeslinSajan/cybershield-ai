"""
Tests for Phase 17 — Risk Scoring Engine and Endpoints.

Covers:
- Dynamic device risk calculation formula with weights, caps, and bands.
- JSON serialization of factor_breakdown in database column.
- Open alerts risk_score backfill.
- GET /devices/{device_id}/risk endpoint (RBAC, 404, multi-tenant).
- GET /risk-scores/ endpoint (sorting, filtering, multi-tenant).
- Trigger recalculations on alert creation and status resolution.
"""

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.alert import Alert, RiskScore
from app.models.device import Device
from app.models.organization import Organization, Role
from app.models.scan import Scan, ScanResult, Vulnerability
from app.models.user import User
from app.core.security import create_access_token, hash_password
from app.services.risk_service import calculate_device_risk, determine_risk_band

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def setup_risk_data(create_tables, db_session):
    """Set up primary and secondary organizations, roles, users, and devices."""
    org1 = Organization(name="RiskTestOrg1", slug=f"risk-org-1-{uuid.uuid4().hex[:6]}")
    org2 = Organization(name="RiskTestOrg2", slug=f"risk-org-2-{uuid.uuid4().hex[:6]}")
    db_session.add_all([org1, org2])
    db_session.flush()

    roles = {}
    for name, desc in [
        ("Administrator", "Full system access"),
        ("Security Analyst", "Monitoring, scanning, and triage"),
        ("Viewer", "Read-only visibility"),
    ]:
        existing = db_session.query(Role).filter(Role.name == name).first()
        if existing:
            roles[name] = existing
        else:
            r = Role(name=name, description=desc)
            db_session.add(r)
            db_session.flush()
            roles[name] = r

    admin_role = roles["Administrator"]
    analyst_role = roles["Security Analyst"]
    viewer_role = roles["Viewer"]

    admin_user = User(
        organization_id=org1.id,
        role_id=admin_role.id,
        email="risk_admin@test.com",
        password_hash=hash_password("Pass123!"),
        username="Risk Admin",
        is_active=True,
    )
    analyst_user = User(
        organization_id=org1.id,
        role_id=analyst_role.id,
        email="risk_analyst@test.com",
        password_hash=hash_password("Pass123!"),
        username="Risk Analyst",
        is_active=True,
    )
    viewer_user = User(
        organization_id=org1.id,
        role_id=viewer_role.id,
        email="risk_viewer@test.com",
        password_hash=hash_password("Pass123!"),
        username="Risk Viewer",
        is_active=True,
    )
    other_user = User(
        organization_id=org2.id,
        role_id=admin_role.id,
        email="risk_other@test.com",
        password_hash=hash_password("Pass123!"),
        username="Risk Other Admin",
        is_active=True,
    )
    db_session.add_all([admin_user, analyst_user, viewer_user, other_user])

    dev1 = Device(
        organization_id=org1.id,
        ip_address="192.168.1.10",
        hostname="server-alpha",
        status="online",
    )
    dev2 = Device(
        organization_id=org1.id,
        ip_address="192.168.1.20",
        hostname="server-beta",
        status="online",
    )
    dev_other = Device(
        organization_id=org2.id,
        ip_address="10.0.0.99",
        hostname="server-gamma",
        status="online",
    )
    db_session.add_all([dev1, dev2, dev_other])
    db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "admin": admin_user,
        "analyst": analyst_user,
        "viewer": viewer_user,
        "other_user": other_user,
        "dev1": dev1,
        "dev2": dev2,
        "dev_other": dev_other,
    }


def _token(user, role_name: str) -> str:
    return create_access_token(
        subject=str(user.id),
        role_name=role_name,
        organization_id=str(user.organization_id),
    )


# ---------------------------------------------------------------------------
# Unit Tests: Risk Engine Formula & Storage
# ---------------------------------------------------------------------------

class TestRiskEngineCalculation:
    def test_determine_risk_band_boundaries(self):
        assert determine_risk_band(0.0) == "Low"
        assert determine_risk_band(24.9) == "Low"
        assert determine_risk_band(25.0) == "Medium"
        assert determine_risk_band(49.9) == "Medium"
        assert determine_risk_band(50.0) == "High"
        assert determine_risk_band(74.9) == "High"
        assert determine_risk_band(75.0) == "Critical"
        assert determine_risk_band(100.0) == "Critical"

    def test_zero_risk_baseline(self, setup_risk_data, db_session):
        dev = setup_risk_data["dev2"]
        org = setup_risk_data["org1"]

        risk = calculate_device_risk(db_session, dev.id, org.id)
        assert risk is not None
        assert float(risk.score) == 0.0
        assert risk.risk_band == "Low"
        assert isinstance(risk.factor_breakdown, str)

        parsed = json.loads(risk.factor_breakdown)
        assert parsed["total_score"] == 0.0
        assert parsed["vulnerabilities"]["subtotal"] == 0.0
        assert parsed["alerts"]["subtotal"] == 0.0
        assert parsed["exposure"]["exposure_score"] == 0.0

    def test_vulnerability_weights_and_caps(self, setup_risk_data, db_session):
        dev = setup_risk_data["dev1"]
        org = setup_risk_data["org1"]

        # Add 2 Critical (30 cap), 3 High (30 cap), 4 Medium (15 cap), 3 Low (5 cap)
        vulns = [
            # Critical: +30, cap 30
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="Critical", description="C1", status="open"),
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="Critical", description="C2", status="open"),
            # High: 3 * 15 = 45 -> cap 30
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="High", description="H1", status="open"),
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="High", description="H2", status="open"),
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="High", description="H3", status="open"),
            # Medium: 4 * 5 = 20 -> cap 15
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="Medium", description="M1", status="open"),
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="Medium", description="M2", status="open"),
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="Medium", description="M3", status="open"),
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="Medium", description="M4", status="open"),
            # Low: 3 * 2 = 6 -> cap 5
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="Low", description="L1", status="open"),
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="Low", description="L2", status="open"),
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="Low", description="L3", status="open"),
            # Resolved vulnerability should not count
            Vulnerability(organization_id=org.id, device_id=dev.id, severity="Critical", description="Resolved", status="resolved"),
        ]
        db_session.add_all(vulns)
        db_session.commit()

        risk = calculate_device_risk(db_session, dev.id, org.id)
        assert risk is not None

        parsed = json.loads(risk.factor_breakdown)
        # Expected vuln score: 30 (crit) + 30 (high) + 15 (med) + 5 (low) = 80.0
        assert parsed["vulnerabilities"]["critical_score"] == 30.0
        assert parsed["vulnerabilities"]["high_score"] == 30.0
        assert parsed["vulnerabilities"]["medium_score"] == 15.0
        assert parsed["vulnerabilities"]["low_score"] == 5.0
        assert parsed["vulnerabilities"]["subtotal"] == 80.0
        assert float(risk.score) == 80.0
        assert risk.risk_band == "Critical"

    def test_alert_weights_and_backfill(self, setup_risk_data, db_session):
        dev = setup_risk_data["dev1"]
        org = setup_risk_data["org1"]

        # Add 1 brute_force (+20), 1 suspicious_login (+15), 1 port_scan (+10), and 1 resolved alert
        a1 = Alert(
            organization_id=org.id,
            device_id=dev.id,
            alert_type="brute_force",
            severity="High",
            description="bf alert",
            risk_score=0.0,
            status="Open",
        )
        a2 = Alert(
            organization_id=org.id,
            device_id=dev.id,
            alert_type="suspicious_login",
            severity="High",
            description="sl alert",
            risk_score=0.0,
            status="Open",
        )
        a3 = Alert(
            organization_id=org.id,
            device_id=dev.id,
            alert_type="port_scan",
            severity="Medium",
            description="ps alert",
            risk_score=0.0,
            status="Open",
        )
        a_resolved = Alert(
            organization_id=org.id,
            device_id=dev.id,
            alert_type="brute_force",
            severity="High",
            description="resolved bf",
            risk_score=10.0,
            status="Resolved",
        )
        db_session.add_all([a1, a2, a3, a_resolved])
        db_session.commit()

        risk = calculate_device_risk(db_session, dev.id, org.id)
        # 80 (from previous vulns) + 20 + 15 + 10 = 125 -> capped at 100.0
        assert float(risk.score) == 100.0
        assert risk.risk_band == "Critical"

        # Verify backfill on open alerts: risk_score must match device risk score (100.0)
        db_session.refresh(a1)
        db_session.refresh(a2)
        db_session.refresh(a3)
        db_session.refresh(a_resolved)

        assert float(a1.risk_score) == 100.0
        assert float(a2.risk_score) == 100.0
        assert float(a3.risk_score) == 100.0
        # Resolved alert must NOT be modified
        assert float(a_resolved.risk_score) == 10.0


# ---------------------------------------------------------------------------
# Endpoint Tests: GET /devices/{device_id}/risk
# ---------------------------------------------------------------------------

class TestDeviceRiskEndpoint:
    def test_all_roles_can_read_device_risk(self, setup_risk_data):
        dev = setup_risk_data["dev1"]

        for role_name in ("Administrator", "Security Analyst", "Viewer"):
            user = (
                setup_risk_data["admin"]
                if role_name == "Administrator"
                else setup_risk_data["analyst"]
                if role_name == "Security Analyst"
                else setup_risk_data["viewer"]
            )
            token = _token(user, role_name)
            resp = client.get(
                f"/api/v1/devices/{dev.id}/risk",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["device_id"] == str(dev.id)
            assert "score" in data
            assert "risk_band" in data
            assert "factor_breakdown" in data

    def test_unauthenticated_returns_401(self, setup_risk_data):
        dev = setup_risk_data["dev1"]
        resp = client.get(f"/api/v1/devices/{dev.id}/risk")
        assert resp.status_code == 401

    def test_nonexistent_device_returns_404(self, setup_risk_data):
        token = _token(setup_risk_data["admin"], "Administrator")
        resp = client.get(
            f"/api/v1/devices/{uuid.uuid4()}/risk",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_cross_tenant_device_risk_returns_404(self, setup_risk_data):
        # User from Org2 cannot read device from Org1
        token = _token(setup_risk_data["other_user"], "Administrator")
        resp = client.get(
            f"/api/v1/devices/{setup_risk_data['dev1'].id}/risk",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Endpoint Tests: GET /risk-scores/
# ---------------------------------------------------------------------------

class TestListRiskScoresEndpoint:
    def test_all_roles_can_list_risk_scores(self, setup_risk_data):
        for role_name in ("Administrator", "Security Analyst", "Viewer"):
            user = (
                setup_risk_data["admin"]
                if role_name == "Administrator"
                else setup_risk_data["analyst"]
                if role_name == "Security Analyst"
                else setup_risk_data["viewer"]
            )
            token = _token(user, role_name)
            resp = client.get(
                "/api/v1/risk-scores/",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 2  # dev1 and dev2 in Org1

            # Check sorting: descending by score
            scores = [item["score"] for item in data]
            assert scores == sorted(scores, reverse=True)

    def test_filter_by_risk_band(self, setup_risk_data):
        token = _token(setup_risk_data["admin"], "Administrator")
        resp = client.get(
            "/api/v1/risk-scores/?risk_band=Critical",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["risk_band"] == "Critical" for item in data)

    def test_cross_tenant_isolation(self, setup_risk_data):
        # Org2 user only gets Org2 devices
        token = _token(setup_risk_data["other_user"], "Administrator")
        resp = client.get(
            "/api/v1/risk-scores/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        device_ids = [item["device_id"] for item in data]
        assert str(setup_risk_data["dev_other"].id) in device_ids
        assert str(setup_risk_data["dev1"].id) not in device_ids
        assert str(setup_risk_data["dev2"].id) not in device_ids


# ---------------------------------------------------------------------------
# Trigger Tests: Alert Status Transition -> Risk Recalculation
# ---------------------------------------------------------------------------

class TestRiskRecalculationTrigger:
    def test_resolving_alert_triggers_risk_recalculation(self, setup_risk_data, db_session):
        org = setup_risk_data["org1"]

        # Create isolated device with 1 open brute_force alert (+20) and no vulns
        dev = Device(
            organization_id=org.id,
            ip_address="192.168.1.55",
            hostname="server-trigger-test",
            status="online",
        )
        db_session.add(dev)
        db_session.flush()

        alert = Alert(
            organization_id=org.id,
            device_id=dev.id,
            alert_type="brute_force",
            severity="High",
            description="bf trigger alert",
            risk_score=20.0,
            status="Open",
        )
        db_session.add(alert)
        db_session.commit()

        # Calculate initial risk: score should be 20.0 ("Low")
        initial_risk = calculate_device_risk(db_session, dev.id, org.id)
        assert float(initial_risk.score) == 20.0
        assert initial_risk.risk_band == "Low"

        # Now transition alert: Open -> Acknowledged -> Resolved
        token = _token(setup_risk_data["analyst"], "Security Analyst")
        p1 = client.patch(
            f"/api/v1/alerts/{alert.id}",
            json={"status": "Acknowledged", "reason": "Triage"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert p1.status_code == 200

        p2 = client.patch(
            f"/api/v1/alerts/{alert.id}",
            json={"status": "Resolved", "reason": "Fixed"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert p2.status_code == 200

        # After resolution, latest device risk must have been recalculated to 0.0
        resp = client.get(
            f"/api/v1/devices/{dev.id}/risk",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        latest_risk = resp.json()
        assert latest_risk["score"] == 0.0
        assert latest_risk["risk_band"] == "Low"

    def test_exposure_score_threshold(self, setup_risk_data, db_session):
        org = setup_risk_data["org1"]
        dev = Device(
            organization_id=org.id,
            ip_address="192.168.1.77",
            hostname="server-exposure",
            status="online",
        )
        db_session.add(dev)
        db_session.flush()

        # Scan with 9 open ports (< 10 threshold)
        scan1 = Scan(
            organization_id=org.id,
            created_by_user_id=setup_risk_data["admin"].id,
            scan_type="vulnerability",
            target_scope="192.168.1.77",
            status="COMPLETED",
        )
        db_session.add(scan1)
        db_session.flush()

        scan_time = datetime.now(timezone.utc)
        res1 = ScanResult(
            organization_id=org.id,
            scan_id=scan1.id,
            device_id=dev.id,
            result_type="services",
            raw_payload={
                "services": [{"port": i, "state": "open"} for i in range(1, 10)]
            },
            created_at=scan_time,
        )
        db_session.add(res1)
        db_session.commit()

        risk1 = calculate_device_risk(db_session, dev.id, org.id)
        assert float(risk1.score) == 0.0
        parsed1 = json.loads(risk1.factor_breakdown)
        assert parsed1["exposure"]["open_ports_count"] == 9
        assert parsed1["exposure"]["exposure_score"] == 0.0

        # Now add a scan with 12 open ports (>= 10 threshold) with later timestamp
        res2 = ScanResult(
            organization_id=org.id,
            scan_id=scan1.id,
            device_id=dev.id,
            result_type="services",
            raw_payload={
                "services": [{"port": i, "state": "open"} for i in range(1, 13)]
            },
            created_at=scan_time + timedelta(seconds=2),
        )
        db_session.add(res2)
        db_session.commit()

        risk2 = calculate_device_risk(db_session, dev.id, org.id)
        assert float(risk2.score) == 10.0
        parsed2 = json.loads(risk2.factor_breakdown)
        assert parsed2["exposure"]["open_ports_count"] == 12
        assert parsed2["exposure"]["exposure_score"] == 10.0
        assert risk2.risk_band == "Low"

    def test_alert_creation_triggers_risk_recalculation(self, setup_risk_data, db_session):
        from app.services.detection_service import create_alert
        org = setup_risk_data["org1"]
        dev = Device(
            organization_id=org.id,
            ip_address="192.168.1.88",
            hostname="server-alert-trigger",
            status="online",
        )
        db_session.add(dev)
        db_session.flush()

        # Device starts with 0 risk
        initial_risk = calculate_device_risk(db_session, dev.id, org.id)
        assert float(initial_risk.score) == 0.0

        # Create alert via detection service with device_id
        alert = create_alert(
            db=db_session,
            organization_id=org.id,
            alert_type="brute_force",
            severity="High",
            description="brute force trigger test",
            risk_score=20.0,
            device_id=dev.id,
            source_ip="192.168.1.88",
        )
        assert alert is not None
        db_session.commit()

        # Device risk must now be updated (+20 for brute_force)
        token = _token(setup_risk_data["viewer"], "Viewer")
        resp = client.get(
            f"/api/v1/devices/{dev.id}/risk",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["score"] == 20.0
        assert data["risk_band"] == "Low"
