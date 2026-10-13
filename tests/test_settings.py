"""
Tests for Phase 21 — Settings and Audit Logs.

Covers:
- Strict RBAC:
  - Settings: Administrator allowed (200), Security Analyst & Viewer forbidden (403 FORBIDDEN).
  - Audit Logs: Administrator allowed (200), Security Analyst & Viewer forbidden (403 FORBIDDEN).
  - Unauthenticated requests return 401.
- Endpoints:
  - GET /api/v1/settings/
  - PUT /api/v1/settings/{key}
  - PATCH /api/v1/settings/{key}
  - GET /api/v1/settings/audit-logs and GET /api/v1/audit-logs/
- Verification of:
  - Audit log generation on setting updates (action: 'setting_updated').
  - Organization isolation on settings and audit logs.
  - Action and actor_type filtering on audit logs.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.organization import Organization, Role
from app.models.system import AuditLog, SystemSetting
from app.models.user import User
from app.core.security import create_access_token, hash_password

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures & Setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def setup_settings_data(create_tables, db_session):
    """Set up organizations, users (Admin, Analyst, Viewer), settings, and audit logs."""
    org1 = Organization(name="SettingsOrg1", slug=f"set-org-1-{uuid.uuid4().hex[:6]}")
    org2 = Organization(name="SettingsOrg2", slug=f"set-org-2-{uuid.uuid4().hex[:6]}")
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
            email=f"{key}_settings_{uuid.uuid4().hex[:6]}@example.com",
            username=f"{key}_settings",
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
        email=f"org2_admin_settings_{uuid.uuid4().hex[:6]}@example.com",
        username="org2_admin_settings",
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

    # Pre-seed a setting in Org1
    setting1 = SystemSetting(
        organization_id=org1.id,
        key="heartbeat_interval_seconds",
        value=30,
        created_by_user_id=users["admin"].id,
    )
    # Pre-seed a setting in Org2
    setting2 = SystemSetting(
        organization_id=org2.id,
        key="org2_custom_setting",
        value={"enabled": True},
        created_by_user_id=org2_admin.id,
    )
    db_session.add_all([setting1, setting2])

    # Pre-seed audit logs for Org1 and Org2
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
        action="alert_created",
        target_type="alerts",
        target_id=uuid.uuid4(),
        details={"type": "brute_force"},
    )
    al_org2 = AuditLog(
        organization_id=org2.id,
        actor_type="user",
        actor_id=org2_admin.id,
        action="user_login",
        target_type="users",
        target_id=org2_admin.id,
        details={"ip": "10.0.0.1"},
    )
    db_session.add_all([al1, al2, al_org2])
    db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "users": users,
        "tokens": tokens,
        "setting1": setting1,
    }


# ---------------------------------------------------------------------------
# Tests: Settings Authorization & Operations
# ---------------------------------------------------------------------------

class TestSettingsRBAC:
    def test_unauthenticated_returns_401(self):
        resp = client.get("/api/v1/settings/")
        assert resp.status_code == 401

    def test_analyst_cannot_access_settings(self, setup_settings_data):
        tokens = setup_settings_data["tokens"]
        resp = client.get(
            "/api/v1/settings/",
            headers={"Authorization": f"Bearer {tokens['analyst']}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_viewer_cannot_access_settings(self, setup_settings_data):
        tokens = setup_settings_data["tokens"]
        resp = client.get(
            "/api/v1/settings/",
            headers={"Authorization": f"Bearer {tokens['viewer']}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_admin_can_get_settings(self, setup_settings_data):
        tokens = setup_settings_data["tokens"]
        resp = client.get(
            "/api/v1/settings/",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        keys = [s["key"] for s in data]
        assert "heartbeat_interval_seconds" in keys

    def test_admin_can_put_and_patch_setting(self, setup_settings_data, db_session):
        tokens = setup_settings_data["tokens"]

        # PUT setting
        resp_put = client.put(
            "/api/v1/settings/offline_timeout_seconds",
            json={"value": 90},
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp_put.status_code == 200
        assert resp_put.json()["key"] == "offline_timeout_seconds"
        assert resp_put.json()["value"] == 90

        # PATCH setting
        resp_patch = client.patch(
            "/api/v1/settings/offline_timeout_seconds",
            json={"value": 120},
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp_patch.status_code == 200
        assert resp_patch.json()["value"] == 120

        # Verify audit log was created
        audit = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.action == "setting_updated",
                AuditLog.organization_id == setup_settings_data["org1"].id,
            )
            .first()
        )
        assert audit is not None
        assert audit.details["key"] == "offline_timeout_seconds"

    def test_analyst_cannot_put_setting(self, setup_settings_data):
        tokens = setup_settings_data["tokens"]
        resp = client.put(
            "/api/v1/settings/unauthorized_key",
            json={"value": "test"},
            headers={"Authorization": f"Bearer {tokens['analyst']}"},
        )
        assert resp.status_code == 403

    def test_settings_org_isolation(self, setup_settings_data):
        tokens = setup_settings_data["tokens"]
        resp = client.get(
            "/api/v1/settings/",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp.status_code == 200
        keys = [s["key"] for s in resp.json()]
        assert "org2_custom_setting" not in keys


# ---------------------------------------------------------------------------
# Tests: Audit Logs Authorization & Filtering
# ---------------------------------------------------------------------------

class TestAuditLogsRBAC:
    def test_audit_logs_unauthenticated_returns_401(self):
        resp = client.get("/api/v1/settings/audit-logs")
        assert resp.status_code == 401

    def test_analyst_cannot_access_audit_logs(self, setup_settings_data):
        tokens = setup_settings_data["tokens"]
        resp = client.get(
            "/api/v1/settings/audit-logs",
            headers={"Authorization": f"Bearer {tokens['analyst']}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_viewer_cannot_access_audit_logs(self, setup_settings_data):
        tokens = setup_settings_data["tokens"]
        resp = client.get(
            "/api/v1/settings/audit-logs",
            headers={"Authorization": f"Bearer {tokens['viewer']}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_admin_can_access_audit_logs_via_both_paths(self, setup_settings_data):
        tokens = setup_settings_data["tokens"]

        # Path 1: /settings/audit-logs
        resp1 = client.get(
            "/api/v1/settings/audit-logs",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert isinstance(data1, list)
        assert len(data1) >= 1

        # Path 2: /audit-logs/ (alias)
        resp2 = client.get(
            "/api/v1/audit-logs/",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert isinstance(data2, list)
        assert len(data2) == len(data1)

    def test_audit_logs_filtering_by_action_and_actor(self, setup_settings_data):
        tokens = setup_settings_data["tokens"]

        # Filter by action=user_login
        resp_act = client.get(
            "/api/v1/settings/audit-logs?action=user_login",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp_act.status_code == 200
        for entry in resp_act.json():
            assert entry["action"] == "user_login"

        # Filter by actor_type=system
        resp_sys = client.get(
            "/api/v1/settings/audit-logs?actor_type=system",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp_sys.status_code == 200
        for entry in resp_sys.json():
            assert entry["actor_type"] == "system"

    def test_audit_logs_org_isolation(self, setup_settings_data):
        tokens = setup_settings_data["tokens"]

        resp_org1 = client.get(
            "/api/v1/settings/audit-logs",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp_org1.status_code == 200
        for entry in resp_org1.json():
            assert entry["organization_id"] == str(setup_settings_data["org1"].id)

        resp_org2 = client.get(
            "/api/v1/settings/audit-logs",
            headers={"Authorization": f"Bearer {tokens['org2_admin']}"},
        )
        assert resp_org2.status_code == 200
        for entry in resp_org2.json():
            assert entry["organization_id"] == str(setup_settings_data["org2"].id)
