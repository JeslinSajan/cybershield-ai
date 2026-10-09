"""
Test suite for Phase 16 — Alert Management endpoints.

Tests:
  - GET /alerts/summary
  - GET /alerts/
  - GET /alerts/{alert_id}
  - GET /alerts/{alert_id}/history
  - PATCH /alerts/{alert_id} (status transitions, validation, RBAC)
"""

import uuid
from decimal import Decimal
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.security import create_access_token, hash_password
from app.core.seed import CANONICAL_ROLES
from app.models.alert import Alert, AlertEvent
from app.models.organization import Organization, Role
from app.models.system import AuditLog
from app.models.user import User

client = TestClient(app)


def _token(user: User, role_name: str) -> str:
    return create_access_token(
        subject=str(user.id),
        role_name=role_name,
        organization_id=str(user.organization_id),
    )


@pytest.fixture(scope="module")
def alert_test_data(create_tables, db_session):
    """Seed org, users (admin, analyst, viewer), and initial alerts."""
    db = db_session
    org = Organization(name="Alert Test Org", slug=f"alert-test-{uuid.uuid4().hex[:6]}")
    other_org = Organization(name="Other Alert Org", slug=f"other-alert-{uuid.uuid4().hex[:6]}")
    db.add_all([org, other_org])
    db.flush()

    roles = {}
    for name, desc in CANONICAL_ROLES:
        existing = db.query(Role).filter(Role.name == name).first()
        if existing:
            roles[name] = existing
        else:
            r = Role(name=name, description=desc)
            db.add(r)
            db.flush()
            roles[name] = r

    admin = User(
        organization_id=org.id,
        role_id=roles["Administrator"].id,
        email="alert_admin@test.com",
        username="alert_admin",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    analyst = User(
        organization_id=org.id,
        role_id=roles["Security Analyst"].id,
        email="alert_analyst@test.com",
        username="alert_analyst",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    viewer = User(
        organization_id=org.id,
        role_id=roles["Viewer"].id,
        email="alert_viewer@test.com",
        username="alert_viewer",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    other_user = User(
        organization_id=other_org.id,
        role_id=roles["Administrator"].id,
        email="other_admin@test.com",
        username="other_admin",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )

    db.add_all([admin, analyst, viewer, other_user])
    db.flush()

    # Create alerts for org
    alert_open_crit = Alert(
        organization_id=org.id,
        alert_type="brute_force",
        severity="Critical",
        status="Open",
        description="Multiple failed authentications from 192.168.1.100",
        risk_score=Decimal("85.00"),
        triggered_at=datetime.now(timezone.utc),
    )
    alert_open_high = Alert(
        organization_id=org.id,
        alert_type="port_scan",
        severity="High",
        status="Open",
        description="Port sweep detected on host",
        risk_score=Decimal("60.00"),
        triggered_at=datetime.now(timezone.utc),
    )
    alert_ack_med = Alert(
        organization_id=org.id,
        alert_type="suspicious_login",
        severity="Medium",
        status="Acknowledged",
        description="Login following failure burst",
        risk_score=Decimal("40.00"),
        triggered_at=datetime.now(timezone.utc),
    )
    alert_inv_low = Alert(
        organization_id=org.id,
        alert_type="policy_violation",
        severity="Low",
        status="Investigating",
        description="Off-hours workstation activity",
        risk_score=Decimal("15.00"),
        triggered_at=datetime.now(timezone.utc),
    )
    alert_resolved = Alert(
        organization_id=org.id,
        alert_type="test_alert",
        severity="Low",
        status="Resolved",
        description="Resolved test alert",
        risk_score=Decimal("10.00"),
        triggered_at=datetime.now(timezone.utc),
    )

    # Create alert for other_org
    other_alert = Alert(
        organization_id=other_org.id,
        alert_type="brute_force",
        severity="Critical",
        status="Open",
        description="Other org alert",
        risk_score=Decimal("90.00"),
        triggered_at=datetime.now(timezone.utc),
    )

    db.add_all([
        alert_open_crit,
        alert_open_high,
        alert_ack_med,
        alert_inv_low,
        alert_resolved,
        other_alert,
    ])
    db.commit()

    return {
        "org": org,
        "other_org": other_org,
        "admin": admin,
        "analyst": analyst,
        "viewer": viewer,
        "other_user": other_user,
        "alerts": {
            "open_crit": alert_open_crit,
            "open_high": alert_open_high,
            "ack_med": alert_ack_med,
            "inv_low": alert_inv_low,
            "resolved": alert_resolved,
            "other": other_alert,
        },
    }


# ===========================================================================
# 1. Tests for GET /alerts/summary
# ===========================================================================

class TestAlertsSummary:
    def test_summary_returns_correct_counts(self, alert_test_data):
        data = alert_test_data
        token = _token(data["analyst"], "Security Analyst")

        resp = client.get("/api/v1/alerts/summary", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, resp.text
        summary = resp.json()

        # Check required keys
        expected_keys = {
            "open", "acknowledged", "investigating", "resolved", "false_positive",
            "critical", "high", "medium", "low"
        }
        assert expected_keys.issubset(set(summary.keys()))

        # Counts: org has 2 Open, 1 Acknowledged, 1 Investigating, 1 Resolved
        assert summary["open"] == 2
        assert summary["acknowledged"] == 1
        assert summary["investigating"] == 1
        assert summary["resolved"] == 1
        assert summary["critical"] == 1
        assert summary["high"] == 1
        assert summary["medium"] == 1
        assert summary["low"] == 2

    def test_summary_unauthenticated_returns_401(self):
        resp = client.get("/api/v1/alerts/summary")
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "NOT_AUTHENTICATED"

    def test_summary_viewer_allowed(self, alert_test_data):
        data = alert_test_data
        token = _token(data["viewer"], "Viewer")
        resp = client.get("/api/v1/alerts/summary", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200


# ===========================================================================
# 2. Tests for GET /alerts/ (List)
# ===========================================================================

class TestListAlerts:
    def test_all_roles_can_list_alerts(self, alert_test_data):
        data = alert_test_data
        for role, user in [("Administrator", data["admin"]), ("Security Analyst", data["analyst"]), ("Viewer", data["viewer"])]:
            token = _token(user, role)
            resp = client.get("/api/v1/alerts/", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)
            assert len(resp.json()) == 5

    def test_filter_by_status(self, alert_test_data):
        data = alert_test_data
        token = _token(data["admin"], "Administrator")
        resp = client.get("/api/v1/alerts/?status=Open", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        alerts = resp.json()
        assert len(alerts) == 2
        for a in alerts:
            assert a["status"] == "Open"

    def test_filter_by_severity(self, alert_test_data):
        data = alert_test_data
        token = _token(data["admin"], "Administrator")
        resp = client.get("/api/v1/alerts/?severity=Critical", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        alerts = resp.json()
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "Critical"

    def test_filter_by_alert_type(self, alert_test_data):
        data = alert_test_data
        token = _token(data["admin"], "Administrator")
        resp = client.get("/api/v1/alerts/?alert_type=brute_force", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        alerts = resp.json()
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "brute_force"

    def test_pagination_limit_and_offset(self, alert_test_data):
        data = alert_test_data
        token = _token(data["admin"], "Administrator")
        resp = client.get("/api/v1/alerts/?limit=2&offset=0", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_cross_org_isolation(self, alert_test_data):
        data = alert_test_data
        token = _token(data["other_user"], "Administrator")
        resp = client.get("/api/v1/alerts/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        alerts = resp.json()
        assert len(alerts) == 1
        assert alerts[0]["description"] == "Other org alert"

    def test_unauthenticated_returns_401(self):
        resp = client.get("/api/v1/alerts/")
        assert resp.status_code == 401


# ===========================================================================
# 3. Tests for GET /alerts/{alert_id} & /history
# ===========================================================================

class TestGetAlertDetail:
    def test_get_alert_detail_success(self, alert_test_data):
        data = alert_test_data
        token = _token(data["analyst"], "Security Analyst")
        target_id = data["alerts"]["open_crit"].id

        resp = client.get(f"/api/v1/alerts/{target_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        res = resp.json()
        assert res["id"] == str(target_id)
        assert res["status"] == "Open"
        assert "history" in res

    def test_get_nonexistent_alert_returns_404(self, alert_test_data):
        data = alert_test_data
        token = _token(data["analyst"], "Security Analyst")
        fake_id = uuid.uuid4()

        resp = client.get(f"/api/v1/alerts/{fake_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_cross_org_get_alert_returns_404(self, alert_test_data):
        data = alert_test_data
        token = _token(data["other_user"], "Administrator")
        target_id = data["alerts"]["open_crit"].id

        resp = client.get(f"/api/v1/alerts/{target_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_get_alert_history_endpoint(self, alert_test_data):
        data = alert_test_data
        token = _token(data["viewer"], "Viewer")
        target_id = data["alerts"]["open_crit"].id

        resp = client.get(f"/api/v1/alerts/{target_id}/history", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ===========================================================================
# 4. Tests for PATCH /alerts/{alert_id} (Transitions & RBAC)
# ===========================================================================

class TestPatchAlertStatus:
    def test_analyst_can_transition_open_to_acknowledged(self, alert_test_data, db_session):
        data = alert_test_data
        token = _token(data["analyst"], "Security Analyst")
        alert = data["alerts"]["open_crit"]

        resp = client.patch(
            f"/api/v1/alerts/{alert.id}",
            json={"status": "Acknowledged", "reason": "Analyst triaging alert"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        res = resp.json()
        assert res["status"] == "Acknowledged"
        assert res["from_status"] == "Open"
        assert res["reason"] == "Analyst triaging alert"

        # Verify DB Alert state
        db_session.expire_all()
        refreshed = db_session.query(Alert).filter(Alert.id == alert.id).first()
        assert refreshed.status == "Acknowledged"

        # Verify AlertEvent created
        event = db_session.query(AlertEvent).filter(
            AlertEvent.alert_id == alert.id,
            AlertEvent.to_status == "Acknowledged",
        ).first()
        assert event is not None
        assert event.from_status == "Open"
        assert event.actor_user_id == data["analyst"].id

        # Verify AuditLog written
        audit = db_session.query(AuditLog).filter(
            AuditLog.target_id == alert.id,
            AuditLog.action == "alert_status_changed",
        ).first()
        assert audit is not None
        assert audit.actor_type == "user"
        assert audit.actor_id == data["analyst"].id

    def test_transition_acknowledged_to_investigating(self, alert_test_data):
        data = alert_test_data
        token = _token(data["admin"], "Administrator")
        alert = data["alerts"]["ack_med"]

        resp = client.patch(
            f"/api/v1/alerts/{alert.id}",
            json={"status": "Investigating", "reason": "Deep dive investigation"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "Investigating"

    def test_transition_investigating_to_resolved(self, alert_test_data):
        data = alert_test_data
        token = _token(data["analyst"], "Security Analyst")
        alert = data["alerts"]["inv_low"]

        resp = client.patch(
            f"/api/v1/alerts/{alert.id}",
            json={"status": "Resolved", "reason": "Root cause remediated"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "Resolved"

    def test_transition_open_to_false_positive(self, alert_test_data):
        data = alert_test_data
        token = _token(data["analyst"], "Security Analyst")
        alert = data["alerts"]["open_high"]

        resp = client.patch(
            f"/api/v1/alerts/{alert.id}",
            json={"status": "False Positive", "reason": "Authorized network audit"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "False Positive"

    def test_invalid_transition_open_to_resolved_returns_400(self, alert_test_data, db_session):
        data = alert_test_data
        token = _token(data["analyst"], "Security Analyst")

        # Create fresh Open alert
        fresh = Alert(
            organization_id=data["org"].id,
            alert_type="test",
            severity="Low",
            status="Open",
            description="Testing invalid jump",
            risk_score=Decimal("10.00"),
            triggered_at=datetime.now(timezone.utc),
        )
        db_session.add(fresh)
        db_session.commit()

        resp = client.patch(
            f"/api/v1/alerts/{fresh.id}",
            json={"status": "Resolved", "reason": "Skipping triage"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        err = resp.json()["error"]
        assert err["code"] == "VALIDATION_ERROR"
        assert "Invalid status transition" in err["message"]

    def test_invalid_transition_from_resolved_returns_400(self, alert_test_data):
        data = alert_test_data
        token = _token(data["analyst"], "Security Analyst")
        alert = data["alerts"]["resolved"]

        resp = client.patch(
            f"/api/v1/alerts/{alert.id}",
            json={"status": "Open", "reason": "Trying to reopen"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_unknown_status_value_returns_400(self, alert_test_data):
        data = alert_test_data
        token = _token(data["analyst"], "Security Analyst")
        alert = data["alerts"]["ack_med"]

        resp = client.patch(
            f"/api/v1/alerts/{alert.id}",
            json={"status": "InvalidStatusXYZ", "reason": "Testing bad status"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_viewer_cannot_patch_alert_returns_403(self, alert_test_data):
        data = alert_test_data
        token = _token(data["viewer"], "Viewer")
        alert = data["alerts"]["ack_med"]

        resp = client.patch(
            f"/api/v1/alerts/{alert.id}",
            json={"status": "Resolved"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_patch_nonexistent_alert_returns_404(self, alert_test_data):
        data = alert_test_data
        token = _token(data["analyst"], "Security Analyst")
        fake_id = uuid.uuid4()

        resp = client.patch(
            f"/api/v1/alerts/{fake_id}",
            json={"status": "Acknowledged"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"
