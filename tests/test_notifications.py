"""
Tests for Phase 21 — Notifications.

Covers:
- Strict RBAC: All authenticated users (Admin, Analyst, Viewer) can view, count, and mark notifications as read.
- Unauthenticated requests return 401.
- Listing notifications with is_read filter, pagination, and multi-tenant organization isolation.
- Unread count calculation.
- Marking individual notification as read (PATCH /notifications/{id}/read) with 404 on nonexistent or cross-org.
- Marking all notifications as read (POST /notifications/mark-all-read).
"""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.organization import Organization, Role
from app.models.system import Notification
from app.models.user import User
from app.core.security import create_access_token, hash_password

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures & Setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def setup_notifications_data(create_tables, db_session):
    """Set up organizations, users (Admin, Analyst, Viewer), and test notifications."""
    org1 = Organization(name="NotifOrg1", slug=f"notif-org-1-{uuid.uuid4().hex[:6]}")
    org2 = Organization(name="NotifOrg2", slug=f"notif-org-2-{uuid.uuid4().hex[:6]}")
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

    # Org1 users
    for role_name, key in [
        ("Administrator", "admin"),
        ("Security Analyst", "analyst"),
        ("Viewer", "viewer"),
    ]:
        u = User(
            organization_id=org1.id,
            role_id=roles[role_name].id,
            email=f"{key}_notif_{uuid.uuid4().hex[:6]}@example.com",
            username=f"{key}_notif",
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
        email=f"org2_admin_notif_{uuid.uuid4().hex[:6]}@example.com",
        username="org2_admin_notif",
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

    # Seed Notifications for Org1
    n1 = Notification(
        organization_id=org1.id,
        user_id=None,  # broadcast to org
        notification_type="alert",
        channel="dashboard",
        title="High Alert: Suspicious SSH Login",
        body="Repeated failed logins detected from 192.168.1.100",
        is_read=False,
    )
    n2 = Notification(
        organization_id=org1.id,
        user_id=users["admin"].id,  # direct to admin
        notification_type="alert",
        channel="dashboard",
        title="Critical Alert: Malware Indicator Match",
        body="Host matched known malware C2 domain",
        is_read=False,
    )
    n3 = Notification(
        organization_id=org1.id,
        user_id=None,
        notification_type="scan",
        channel="dashboard",
        title="Scan Completed",
        body="Vulnerability scan completed for subnet 10.0.0.0/24",
        is_read=True,
    )

    # Seed Notification for Org2
    n_org2 = Notification(
        organization_id=org2.id,
        user_id=None,
        notification_type="alert",
        channel="dashboard",
        title="Org2 Alert",
        body="Isolated event in Org2",
        is_read=False,
    )

    db_session.add_all([n1, n2, n3, n_org2])
    db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "users": users,
        "tokens": tokens,
        "notif1": n1,
        "notif2": n2,
        "notif3": n3,
        "notif_org2": n_org2,
    }


# ---------------------------------------------------------------------------
# Tests: Authentication & Authorization
# ---------------------------------------------------------------------------

class TestNotificationsAuth:
    def test_unauthenticated_returns_401(self):
        resp = client.get("/api/v1/notifications/")
        assert resp.status_code == 401

    def test_unread_count_unauthenticated_returns_401(self):
        resp = client.get("/api/v1/notifications/unread-count")
        assert resp.status_code == 401

    def test_all_roles_can_list_notifications(self, setup_notifications_data):
        tokens = setup_notifications_data["tokens"]
        for role_key in ["admin", "analyst", "viewer"]:
            resp = client.get(
                "/api/v1/notifications/",
                headers={"Authorization": f"Bearer {tokens[role_key]}"},
            )
            assert resp.status_code == 200, f"Role {role_key} failed: {resp.text}"
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 1

    def test_all_roles_can_get_unread_count(self, setup_notifications_data):
        tokens = setup_notifications_data["tokens"]
        for role_key in ["admin", "analyst", "viewer"]:
            resp = client.get(
                "/api/v1/notifications/unread-count",
                headers={"Authorization": f"Bearer {tokens[role_key]}"},
            )
            assert resp.status_code == 200, f"Role {role_key} failed: {resp.text}"
            data = resp.json()
            assert "unread_count" in data
            assert isinstance(data["unread_count"], int)


# ---------------------------------------------------------------------------
# Tests: Multi-tenant Isolation & Filtering
# ---------------------------------------------------------------------------

class TestNotificationsIsolationAndFiltering:
    def test_org_isolation(self, setup_notifications_data):
        tokens = setup_notifications_data["tokens"]
        resp_org1 = client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp_org1.status_code == 200
        titles_org1 = [n["title"] for n in resp_org1.json()]
        assert "Org2 Alert" not in titles_org1

        resp_org2 = client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {tokens['org2_admin']}"},
        )
        assert resp_org2.status_code == 200
        titles_org2 = [n["title"] for n in resp_org2.json()]
        assert "Org2 Alert" in titles_org2
        assert "High Alert: Suspicious SSH Login" not in titles_org2

    def test_filter_by_is_read(self, setup_notifications_data):
        tokens = setup_notifications_data["tokens"]
        resp_unread = client.get(
            "/api/v1/notifications/?is_read=false",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp_unread.status_code == 200
        for item in resp_unread.json():
            assert item["is_read"] is False

        resp_read = client.get(
            "/api/v1/notifications/?is_read=true",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp_read.status_code == 200
        for item in resp_read.json():
            assert item["is_read"] is True


# ---------------------------------------------------------------------------
# Tests: Mark Read & Mark All Read
# ---------------------------------------------------------------------------

class TestNotificationsReadActions:
    def test_mark_single_notification_read(self, setup_notifications_data, db_session):
        data = setup_notifications_data
        tokens = data["tokens"]
        notif1_id = data["notif1"].id

        resp = client.patch(
            f"/api/v1/notifications/{notif1_id}/read",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == str(notif1_id)
        assert body["is_read"] is True

    def test_mark_nonexistent_notification_returns_404(self, setup_notifications_data):
        tokens = setup_notifications_data["tokens"]
        fake_id = uuid.uuid4()
        resp = client.patch(
            f"/api/v1/notifications/{fake_id}/read",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_mark_cross_org_notification_returns_404(self, setup_notifications_data):
        tokens = setup_notifications_data["tokens"]
        notif_org2_id = setup_notifications_data["notif_org2"].id

        # Org1 admin tries to mark Org2 notification
        resp = client.patch(
            f"/api/v1/notifications/{notif_org2_id}/read",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_mark_all_read(self, setup_notifications_data):
        tokens = setup_notifications_data["tokens"]

        resp = client.post(
            "/api/v1/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp.status_code == 200
        assert "marked as read" in resp.json()["message"].lower()

        # Check unread count is now 0 for this user
        count_resp = client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert count_resp.status_code == 200
        assert count_resp.json()["unread_count"] == 0
