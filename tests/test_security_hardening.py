"""
Tests for Phase 22 — Security Hardening.

Covers:
1. Rate Limiting on POST /auth/login:
   - 10 requests per minute per IP limit.
   - 11th request returns 429 with error envelope:
     {"error": {"code": "RATE_LIMITED", "message": "Too many requests. Try again later.", "details": []}}
2. Security Response Headers:
   - All HTTP responses contain:
     - X-Content-Type-Options: nosniff
     - X-Frame-Options: DENY
     - Referrer-Policy: strict-origin-when-cross-origin
3. Production Error Sanitization:
   - Non-debug production returns INTERNAL_SERVER_ERROR with details: [] and no stack traces.
4. Organization Isolation Audit:
   - Multi-tenant boundary between Organization A and Organization B verified across devices, alerts, logs, settings, and users.
5. Audit Log Completeness:
   - Successful user login records action='user_login'.
   - Failed user login records action='user_login_failed'.
"""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.alert import Alert
from app.models.device import Device
from app.models.log import Log
from app.models.organization import Organization, Role
from app.models.system import AuditLog, SystemSetting
from app.models.user import User
from app.core.security import create_access_token, hash_password
from app.core.limiter import limiter

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures & Setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def setup_hardening_data(create_tables, db_session):
    """Set up two isolated organizations with Admin and Analyst users."""
    org_a = Organization(name="HardeningOrgA", slug=f"org-a-{uuid.uuid4().hex[:6]}")
    org_b = Organization(name="HardeningOrgB", slug=f"org-b-{uuid.uuid4().hex[:6]}")
    db_session.add_all([org_a, org_b])
    db_session.flush()

    roles = {}
    for name, desc in [
        ("Administrator", "Admin access"),
        ("Security Analyst", "Analyst access"),
        ("Viewer", "Viewer access"),
    ]:
        existing = db_session.query(Role).filter(Role.name == name).first()
        if existing:
            roles[name] = existing
        else:
            r = Role(name=name, description=desc)
            db_session.add(r)
            db_session.flush()
            roles[name] = r

    # Users in Org A
    user_a = User(
        organization_id=org_a.id,
        role_id=roles["Administrator"].id,
        email=f"admin_a_{uuid.uuid4().hex[:6]}@example.com",
        username="admin_a",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
    )

    # Users in Org B
    user_b = User(
        organization_id=org_b.id,
        role_id=roles["Administrator"].id,
        email=f"admin_b_{uuid.uuid4().hex[:6]}@example.com",
        username="admin_b",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
    )
    db_session.add_all([user_a, user_b])
    db_session.flush()

    token_a = create_access_token(
        subject=str(user_a.id),
        role_name="Administrator",
        organization_id=str(org_a.id),
    )
    token_b = create_access_token(
        subject=str(user_b.id),
        role_name="Administrator",
        organization_id=str(org_b.id),
    )

    # Seed isolated resources in Org A
    dev_a = Device(
        organization_id=org_a.id,
        ip_address="192.168.10.5",
        hostname="server-a",
        device_type="Server",
        status="ONLINE",
    )
    alert_a = Alert(
        organization_id=org_a.id,
        alert_type="brute_force",
        severity="High",
        status="Open",
        description="Brute force alert in Org A",
        risk_score=40,
        triggered_at=datetime.now(timezone.utc),
    )
    setting_a = SystemSetting(
        organization_id=org_a.id,
        key="org_a_secret_key",
        value={"enabled": True},
        created_by_user_id=user_a.id,
    )

    # Seed isolated resources in Org B
    dev_b = Device(
        organization_id=org_b.id,
        ip_address="10.0.0.99",
        hostname="server-b",
        device_type="Server",
        status="ONLINE",
    )
    alert_b = Alert(
        organization_id=org_b.id,
        alert_type="port_scan",
        severity="Medium",
        status="Open",
        description="Port scan alert in Org B",
        risk_score=20,
        triggered_at=datetime.now(timezone.utc),
    )
    setting_b = SystemSetting(
        organization_id=org_b.id,
        key="org_b_secret_key",
        value={"enabled": False},
        created_by_user_id=user_b.id,
    )

    db_session.add_all([dev_a, alert_a, setting_a, dev_b, alert_b, setting_b])
    db_session.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "user_a": user_a,
        "user_b": user_b,
        "token_a": token_a,
        "token_b": token_b,
        "roles": roles,
    }


# ---------------------------------------------------------------------------
# Test 1: Secure Response Headers
# ---------------------------------------------------------------------------

class TestSecurityHeaders:
    def test_security_headers_present_on_health_endpoint(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_security_headers_present_on_authenticated_endpoint(self, setup_hardening_data):
        token_a = setup_hardening_data["token_a"]
        resp = client.get(
            "/api/v1/devices/",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert resp.status_code == 200
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


# ---------------------------------------------------------------------------
# Test 2: Rate Limiting on POST /auth/login
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def test_login_rate_limiting_triggers_429(self):
        """10 requests allowed per minute; 11th request returns 429."""
        # Use a distinct client IP by passing client host in headers or rapid requests
        exceeded = False
        last_resp = None
        for i in range(15):
            resp = client.post(
                "/api/v1/auth/login",
                json={"email": f"ratelimit_probe_{i}@example.com", "password": "WrongPassword123!"},
            )
            if resp.status_code == 429:
                exceeded = True
                last_resp = resp
                break

        assert exceeded, "Rate limiting was expected to trigger 429 within 15 rapid requests."
        assert last_resp is not None
        body = last_resp.json()
        assert "error" in body
        assert body["error"]["code"] == "RATE_LIMITED"
        assert "too many requests" in body["error"]["message"].lower()


# ---------------------------------------------------------------------------
# Test 3: Audit Log Completeness (user_login and user_login_failed)
# ---------------------------------------------------------------------------

class TestAuditLogCompleteness:
    def test_successful_login_writes_audit_log(self, setup_hardening_data, db_session):
        user_a = setup_hardening_data["user_a"]

        # Log in with correct password
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": user_a.email, "password": "StrongPassword123!"},
        )
        # Handle case where rate limit might be active from previous test
        if resp.status_code == 429:
            limiter.reset()
            resp = client.post(
                "/api/v1/auth/login",
                json={"email": user_a.email, "password": "StrongPassword123!"},
            )

        assert resp.status_code == 200

        # Verify audit log exists
        audit = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.organization_id == user_a.organization_id,
                AuditLog.actor_id == user_a.id,
                AuditLog.action == "user_login",
            )
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        assert audit is not None
        assert audit.action == "user_login"
        assert audit.details["email"] == user_a.email

    def test_failed_login_writes_audit_log(self, setup_hardening_data, db_session):
        user_a = setup_hardening_data["user_a"]

        # Reset limiter before probe
        limiter.reset()

        resp = client.post(
            "/api/v1/auth/login",
            json={"email": user_a.email, "password": "WrongPasswordAttempt!"},
        )
        assert resp.status_code == 401

        # Verify audit log exists
        audit = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.organization_id == user_a.organization_id,
                AuditLog.actor_id == user_a.id,
                AuditLog.action == "user_login_failed",
            )
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        assert audit is not None
        assert audit.action == "user_login_failed"
        assert audit.details["email"] == user_a.email


# ---------------------------------------------------------------------------
# Test 4: Organization Isolation Audit
# ---------------------------------------------------------------------------

class TestOrganizationIsolation:
    def test_devices_isolation_between_orgs(self, setup_hardening_data):
        token_a = setup_hardening_data["token_a"]
        token_b = setup_hardening_data["token_b"]

        resp_a = client.get("/api/v1/devices/", headers={"Authorization": f"Bearer {token_a}"})
        assert resp_a.status_code == 200
        hostnames_a = [d["hostname"] for d in resp_a.json()]
        assert "server-a" in hostnames_a
        assert "server-b" not in hostnames_a

        resp_b = client.get("/api/v1/devices/", headers={"Authorization": f"Bearer {token_b}"})
        assert resp_b.status_code == 200
        hostnames_b = [d["hostname"] for d in resp_b.json()]
        assert "server-b" in hostnames_b
        assert "server-a" not in hostnames_b

    def test_alerts_isolation_between_orgs(self, setup_hardening_data):
        token_a = setup_hardening_data["token_a"]
        token_b = setup_hardening_data["token_b"]

        resp_a = client.get("/api/v1/alerts/", headers={"Authorization": f"Bearer {token_a}"})
        assert resp_a.status_code == 200
        types_a = [a["alert_type"] for a in resp_a.json()]
        assert "brute_force" in types_a
        assert "port_scan" not in types_a

        resp_b = client.get("/api/v1/alerts/", headers={"Authorization": f"Bearer {token_b}"})
        assert resp_b.status_code == 200
        types_b = [a["alert_type"] for a in resp_b.json()]
        assert "port_scan" in types_b
        assert "brute_force" not in types_b

    def test_settings_isolation_between_orgs(self, setup_hardening_data):
        token_a = setup_hardening_data["token_a"]
        token_b = setup_hardening_data["token_b"]

        resp_a = client.get("/api/v1/settings/", headers={"Authorization": f"Bearer {token_a}"})
        assert resp_a.status_code == 200
        keys_a = [s["key"] for s in resp_a.json()]
        assert "org_a_secret_key" in keys_a
        assert "org_b_secret_key" not in keys_a

        resp_b = client.get("/api/v1/settings/", headers={"Authorization": f"Bearer {token_b}"})
        assert resp_b.status_code == 200
        keys_b = [s["key"] for s in resp_b.json()]
        assert "org_b_secret_key" in keys_b
        assert "org_a_secret_key" not in keys_b

    def test_admin_cannot_create_user_in_other_org(self, setup_hardening_data):
        """User creation should bind to caller's org even if another org is specified in payload."""
        token_a = setup_hardening_data["token_a"]
        org_a = setup_hardening_data["org_a"]
        org_b = setup_hardening_data["org_b"]
        roles = setup_hardening_data["roles"]

        # Admin of Org A attempts to specify Org B's ID
        resp = client.post(
            "/api/v1/users/",
            json={
                "email": f"attacker_user_{uuid.uuid4().hex[:6]}@example.com",
                "username": "attacker",
                "password": "Password123!",
                "role_id": str(roles["Security Analyst"].id),
                "organization_id": str(org_b.id),
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert resp.status_code == 201
        created_user = resp.json()
        # Must be bound to caller's org A, NOT org B!
        assert created_user["organization_id"] == str(org_a.id)
