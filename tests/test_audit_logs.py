"""
Tests for Audit Logs endpoint (Phase 21 & Phase 23).

Covers:
- Strict RBAC: Administrator allowed (200), Security Analyst & Viewer forbidden (403 FORBIDDEN).
- Unauthenticated requests return 401.
- Endpoints:
  - GET /api/v1/audit-logs/
  - GET /api/v1/audit-logs
- Filtering by action, actor_type, limit, and offset.
- Multi-tenant organization isolation between Org 1 and Org 2.
"""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.organization import Organization, Role
from app.models.system import AuditLog
from app.models.user import User
from app.core.security import create_access_token, hash_password

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures & Setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def setup_audit_logs_data(create_tables, db_session):
    """Set up test organizations, users, and audit logs."""
    org1 = Organization(name="AuditOrg1", slug=f"aud-org-1-{uuid.uuid4().hex[:6]}")
    org2 = Organization(name="AuditOrg2", slug=f"aud-org-2-{uuid.uuid4().hex[:6]}")
    db_session.add_all([org1, org2])
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

    users = {}
    tokens = {}

    for role_name, key in [
        ("Administrator", "admin"),
        ("Security Analyst", "analyst"),
        ("Viewer", "viewer"),
    ]:
        u = User(
            organization_id=org1.id,
            role_id=roles[role_name].id,
            email=f"{key}_audit_{uuid.uuid4().hex[:6]}@example.com",
            username=f"{key}_audit",
            password_hash=hash_password("SecurePassword123!"),
            is_active=True,
        )
        db_session.add(u)
        db_session.flush()
        users[key] = u
        tokens[key] = create_access_token(
            subject=str(u.id),
            role_name=role_name,
            organization_id=str(org1.id),
        )

    # Org2 Admin
    org2_admin = User(
        organization_id=org2.id,
        role_id=roles["Administrator"].id,
        email=f"org2_admin_audit_{uuid.uuid4().hex[:6]}@example.com",
        username="org2_admin_audit",
        password_hash=hash_password("SecurePassword123!"),
        is_active=True,
    )
    db_session.add(org2_admin)
    db_session.flush()
    users["org2_admin"] = org2_admin
    tokens["org2_admin"] = create_access_token(
        subject=str(org2_admin.id),
        role_name="Administrator",
        organization_id=str(org2.id),
    )

    # Pre-seed audit logs for Org1
    al1 = AuditLog(
        organization_id=org1.id,
        actor_type="user",
        actor_id=users["admin"].id,
        action="user_login",
        target_type="users",
        target_id=users["admin"].id,
        details={"ip": "127.0.0.1"},
    )
    al2 = AuditLog(
        organization_id=org1.id,
        actor_type="system",
        actor_id=None,
        action="scan_created",
        target_type="scans",
        target_id=uuid.uuid4(),
        details={"scan_type": "discovery"},
    )
    al3 = AuditLog(
        organization_id=org1.id,
        actor_type="user",
        actor_id=users["admin"].id,
        action="report_generated",
        target_type="reports",
        target_id=uuid.uuid4(),
        details={"type": "security_overview"},
    )

    # Pre-seed audit log for Org2
    al_org2 = AuditLog(
        organization_id=org2.id,
        actor_type="user",
        actor_id=org2_admin.id,
        action="user_login",
        target_type="users",
        target_id=org2_admin.id,
        details={"ip": "10.0.0.1"},
    )
    db_session.add_all([al1, al2, al3, al_org2])
    db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "users": users,
        "tokens": tokens,
    }


# ---------------------------------------------------------------------------
# Tests: Authentication & Authorization
# ---------------------------------------------------------------------------

class TestAuditLogsAuth:
    def test_unauthenticated_returns_401(self):
        resp = client.get("/api/v1/audit-logs/")
        assert resp.status_code == 401

    def test_analyst_cannot_access_audit_logs(self, setup_audit_logs_data):
        token = setup_audit_logs_data["tokens"]["analyst"]
        resp = client.get(
            "/api/v1/audit-logs/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_viewer_cannot_access_audit_logs(self, setup_audit_logs_data):
        token = setup_audit_logs_data["tokens"]["viewer"]
        resp = client.get(
            "/api/v1/audit-logs/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_admin_can_access_audit_logs(self, setup_audit_logs_data):
        token = setup_audit_logs_data["tokens"]["admin"]
        resp = client.get(
            "/api/v1/audit-logs/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3


# ---------------------------------------------------------------------------
# Tests: Filtering & Multi-tenant Isolation
# ---------------------------------------------------------------------------

class TestAuditLogsFilteringAndIsolation:
    def test_filter_by_action(self, setup_audit_logs_data):
        token = setup_audit_logs_data["tokens"]["admin"]
        resp = client.get(
            "/api/v1/audit-logs/?action=scan_created",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        for item in data:
            assert item["action"] == "scan_created"

    def test_filter_by_actor_type(self, setup_audit_logs_data):
        token = setup_audit_logs_data["tokens"]["admin"]
        resp = client.get(
            "/api/v1/audit-logs/?actor_type=system",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        for item in data:
            assert item["actor_type"] == "system"

    def test_pagination(self, setup_audit_logs_data):
        token = setup_audit_logs_data["tokens"]["admin"]
        resp = client.get(
            "/api/v1/audit-logs/?limit=2&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) <= 2

    def test_organization_isolation(self, setup_audit_logs_data):
        token1 = setup_audit_logs_data["tokens"]["admin"]
        token2 = setup_audit_logs_data["tokens"]["org2_admin"]

        resp1 = client.get(
            "/api/v1/audit-logs/",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert resp1.status_code == 200
        for entry in resp1.json():
            assert entry["organization_id"] == str(setup_audit_logs_data["org1"].id)

        resp2 = client.get(
            "/api/v1/audit-logs/",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert resp2.status_code == 200
        for entry in resp2.json():
            assert entry["organization_id"] == str(setup_audit_logs_data["org2"].id)
