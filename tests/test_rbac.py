"""
RBAC enforcement tests — Phase 8.

Uses conftest.py for SQLite-compatible DB setup.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.core.seed import CANONICAL_ROLES
from app.models.organization import Organization, Role
from app.models.user import User


@pytest.fixture(scope="module")
def seeded_data(create_tables, db_session):
    """Create org and roles for RBAC tests.
    
    Uses get-or-create pattern for roles since test_auth.py may have
    already inserted them in the shared session-scoped db.
    """
    db = db_session
    org = Organization(name="RBAC Test Org", slug=f"rbac-test-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()

    roles = {}
    for name, desc in CANONICAL_ROLES:
        # Get or create role — avoid unique constraint violation
        existing = db.query(Role).filter(Role.name == name).first()
        if existing:
            roles[name] = existing
        else:
            r = Role(name=name, description=desc)
            db.add(r)
            db.flush()
            roles[name] = r

    users = {}
    for role_name, role in roles.items():
        u = User(
            organization_id=org.id,
            role_id=role.id,
            email=f"{role_name.lower().replace(' ', '_')}@rbac-test.com",
            username=role_name.lower().replace(" ", "_"),
            password_hash=hash_password("TestPass!123"),
            is_active=True,
            failed_login_count=0,
        )
        db.add(u)
        db.flush()
        users[role_name] = u

    db.commit()
    return {"org": org, "roles": roles, "users": users}


def _token_for(user: User, role_name: str) -> str:
    return create_access_token(
        subject=str(user.id),
        role_name=role_name,
        organization_id=str(user.organization_id),
    )


@pytest.fixture()
def client():
    return TestClient(__import__("app.main", fromlist=["app"]).app)


@pytest.fixture()
def db(db_session):
    return db_session


@pytest.fixture()
def admin_token(seeded_data):
    return _token_for(seeded_data["users"]["Administrator"], "Administrator")


@pytest.fixture()
def analyst_token(seeded_data):
    return _token_for(seeded_data["users"]["Security Analyst"], "Security Analyst")


@pytest.fixture()
def viewer_token(seeded_data):
    return _token_for(seeded_data["users"]["Viewer"], "Viewer")


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# No-token baseline
# ---------------------------------------------------------------------------

class TestNoToken:
    def test_protected_endpoint_without_token_is_401(self, client):
        """Missing token → 401 (not 403)."""
        for path in ["/api/v1/users/", "/api/v1/scans/", "/api/v1/settings/"]:
            resp = client.get(path)
            assert resp.status_code == 401, f"Expected 401 for {path}, got {resp.status_code}"


# ---------------------------------------------------------------------------
# Viewer restrictions (FR-3.2)
# ---------------------------------------------------------------------------

class TestViewerRestrictions:
    def test_viewer_cannot_post_scans(self, client, viewer_token):
        resp = client.post("/api/v1/scans/", json={}, headers=auth(viewer_token))
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_viewer_cannot_patch_alert(self, client, viewer_token):
        resp = client.patch("/api/v1/alerts/some-id", json={}, headers=auth(viewer_token))
        assert resp.status_code == 403

    def test_viewer_cannot_use_ai(self, client, viewer_token):
        resp = client.get("/api/v1/ai/conversations", headers=auth(viewer_token))
        assert resp.status_code == 403

    def test_viewer_cannot_post_devices(self, client, viewer_token):
        resp = client.post("/api/v1/devices/", json={}, headers=auth(viewer_token))
        assert resp.status_code == 403

    def test_viewer_can_read_devices(self, client, viewer_token):
        resp = client.get("/api/v1/devices/", headers=auth(viewer_token))
        assert resp.status_code not in (401, 403)

    def test_viewer_can_read_alerts(self, client, viewer_token):
        resp = client.get("/api/v1/alerts/", headers=auth(viewer_token))
        assert resp.status_code not in (401, 403)

    def test_viewer_can_read_dashboard(self, client, viewer_token):
        resp = client.get("/api/v1/dashboard/", headers=auth(viewer_token))
        assert resp.status_code not in (401, 403)


# ---------------------------------------------------------------------------
# Analyst restrictions (FR-3.3)
# ---------------------------------------------------------------------------

class TestAnalystRestrictions:
    def test_analyst_cannot_manage_users(self, client, analyst_token):
        resp = client.get("/api/v1/users/", headers=auth(analyst_token))
        assert resp.status_code == 403

    def test_analyst_cannot_create_user(self, client, analyst_token):
        resp = client.post("/api/v1/users/", json={}, headers=auth(analyst_token))
        assert resp.status_code == 403

    def test_analyst_cannot_access_settings(self, client, analyst_token):
        resp = client.get("/api/v1/settings/", headers=auth(analyst_token))
        assert resp.status_code == 403

    def test_analyst_cannot_register_agent(self, client, analyst_token):
        resp = client.post("/api/v1/agents/", json={}, headers=auth(analyst_token))
        assert resp.status_code == 403

    def test_analyst_can_run_scans(self, client, analyst_token):
        resp = client.post("/api/v1/scans/", json={}, headers=auth(analyst_token))
        assert resp.status_code not in (401, 403)

    def test_analyst_can_read_reports(self, client, analyst_token):
        resp = client.get("/api/v1/reports/", headers=auth(analyst_token))
        assert resp.status_code not in (401, 403)


# ---------------------------------------------------------------------------
# Admin access
# ---------------------------------------------------------------------------

class TestAdminAccess:
    def test_admin_can_list_users(self, client, admin_token):
        resp = client.get("/api/v1/users/", headers=auth(admin_token))
        assert resp.status_code not in (401, 403)

    def test_admin_can_access_settings(self, client, admin_token):
        resp = client.get("/api/v1/settings/", headers=auth(admin_token))
        assert resp.status_code not in (401, 403)

    def test_admin_can_register_agent(self, client, admin_token):
        resp = client.post("/api/v1/agents/", json={}, headers=auth(admin_token))
        assert resp.status_code not in (401, 403)

    def test_admin_can_run_scans(self, client, admin_token):
        resp = client.post("/api/v1/scans/", json={}, headers=auth(admin_token))
        assert resp.status_code not in (401, 403)

    def test_admin_can_view_threat_intelligence(self, client, admin_token):
        resp = client.get("/api/v1/threat-intelligence/", headers=auth(admin_token))
        assert resp.status_code not in (401, 403)


# ---------------------------------------------------------------------------
# Last-Administrator protection (FR-2.3)
# ---------------------------------------------------------------------------

class TestLastAdminProtection:
    def _make_admin(self, db: Session, org_id, admin_role: Role) -> User:
        u = User(
            organization_id=org_id,
            role_id=admin_role.id,
            email=f"solo_admin_{uuid.uuid4().hex[:6]}@test.com",
            username=f"solo_{uuid.uuid4().hex[:4]}",
            password_hash=hash_password("TestPass!123"),
            is_active=True,
            failed_login_count=0,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return u

    def test_cannot_demote_last_admin(self, client, db, seeded_data):
        admin_role = seeded_data["roles"]["Administrator"]
        analyst_role = seeded_data["roles"]["Security Analyst"]
        org_id = seeded_data["org"].id

        # Deactivate seeded admin to make solo the only one
        seed_admin = seeded_data["users"]["Administrator"]
        seed_admin.is_active = False
        db.commit()

        solo = self._make_admin(db, org_id, admin_role)
        token = _token_for(solo, "Administrator")

        resp = client.patch(
            f"/api/v1/users/{solo.id}",
            json={"role_id": str(analyst_role.id)},
            headers=auth(token),
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "LAST_ADMINISTRATOR"

        seed_admin.is_active = True
        solo.is_active = False
        db.commit()

    def test_cannot_deactivate_last_admin(self, client, db, seeded_data):
        admin_role = seeded_data["roles"]["Administrator"]
        org_id = seeded_data["org"].id

        seed_admin = seeded_data["users"]["Administrator"]
        seed_admin.is_active = False
        db.commit()

        solo = self._make_admin(db, org_id, admin_role)
        token = _token_for(solo, "Administrator")

        resp = client.post(f"/api/v1/users/{solo.id}/deactivate", headers=auth(token))
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "LAST_ADMINISTRATOR"

        seed_admin.is_active = True
        solo.is_active = False
        db.commit()

    def test_can_demote_when_another_admin_exists(self, client, db, seeded_data):
        admin_role = seeded_data["roles"]["Administrator"]
        analyst_role = seeded_data["roles"]["Security Analyst"]
        org_id = seeded_data["org"].id

        second = self._make_admin(db, org_id, admin_role)
        token = _token_for(second, "Administrator")

        resp = client.patch(
            f"/api/v1/users/{second.id}",
            json={"role_id": str(analyst_role.id)},
            headers=auth(token),
        )
        assert resp.status_code == 200
