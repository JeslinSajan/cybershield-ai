"""Tests for scan management endpoints (Phase 11.1)."""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.agent import Agent
from app.models.organization import Organization, Role
from app.models.scan import Scan
from app.models.system import AuditLog
from app.models.user import User
from app.core.security import create_access_token, hash_password
from app.core.seed import CANONICAL_ROLES

client = TestClient(app)


@pytest.fixture(scope="module")
def test_org_and_users(db_session):
    """Create org + admin + analyst + viewer for scan tests."""
    org = Organization(name="ScanTestOrg", slug="scan-test-org")
    db_session.add(org)
    db_session.flush()

    roles = {}
    for name, desc in CANONICAL_ROLES:
        existing = db_session.query(Role).filter(Role.name == name).first()
        if existing:
            roles[name] = existing
        else:
            r = Role(name=name, description=desc)
            db_session.add(r)
            db_session.flush()
            roles[name] = r

    admin = User(
        organization_id=org.id,
        role_id=roles["Administrator"].id,
        email="scanadmin@test.com",
        password_hash=hash_password("AdminPass123!"),
        username="scan-admin",
        is_active=True,
    )
    analyst = User(
        organization_id=org.id,
        role_id=roles["Security Analyst"].id,
        email="scananalyst@test.com",
        password_hash=hash_password("AnalystPass123!"),
        username="scan-analyst",
        is_active=True,
    )
    viewer = User(
        organization_id=org.id,
        role_id=roles["Viewer"].id,
        email="scanviewer@test.com",
        password_hash=hash_password("ViewerPass123!"),
        username="scan-viewer",
        is_active=True,
    )
    db_session.add_all([admin, analyst, viewer])
    db_session.commit()
    return {"org": org, "admin": admin, "analyst": analyst, "viewer": viewer}


def _token_for(user):
    from conftest import _TestingSessionLocal
    db = _TestingSessionLocal()
    role = db.query(Role).filter(Role.id == user.role_id).first()
    db.close()
    return create_access_token(
        subject=str(user.id),
        role_name=role.name,
        organization_id=str(user.organization_id),
    )


def _create_online_agent(db_session, org_id):
    agent = Agent(
        organization_id=org_id,
        name="scan-test-agent",
        hostname="scan-host",
        version="1.0.0",
        status="ONLINE",
        is_active=True,
    )
    db_session.add(agent)
    db_session.commit()
    return agent


class TestScanCreation:
    def test_analyst_can_create_discovery_scan(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        analyst = test_org_and_users["analyst"]
        agent = _create_online_agent(db_session, org.id)
        token = _token_for(analyst)

        response = client.post(
            "/api/v1/scans/",
            json={
                "agent_id": str(agent.id),
                "scan_type": "discovery",
                "target_scope": "192.168.1.0/24",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["scan_type"] == "discovery"
        assert data["status"] == "PENDING"
        assert data["target_scope"] == "192.168.1.0/24"
        assert data["agent_id"] == str(agent.id)

        # Check AuditLog
        audit = db_session.query(AuditLog).filter(
            AuditLog.target_id == uuid.UUID(data["id"]),
            AuditLog.action == "scan_created",
        ).first()
        assert audit is not None
        assert audit.actor_id == analyst.id

    def test_viewer_cannot_create_scan(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        viewer = test_org_and_users["viewer"]
        agent = _create_online_agent(db_session, org.id)
        token = _token_for(viewer)

        response = client.post(
            "/api/v1/scans/",
            json={
                "agent_id": str(agent.id),
                "scan_type": "discovery",
                "target_scope": "192.168.1.0/24",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestScanRetrieval:
    def test_list_scans(self, test_org_and_users, db_session):
        viewer = test_org_and_users["viewer"]
        token = _token_for(viewer)

        response = client.get("/api/v1/scans/", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_scan_by_id(self, test_org_and_users, db_session):
        analyst = test_org_and_users["analyst"]
        token = _token_for(analyst)

        # Get existing scan from list
        list_resp = client.get("/api/v1/scans/", headers={"Authorization": f"Bearer {token}"})
        scan_id = list_resp.json()[0]["id"]

        detail_resp = client.get(f"/api/v1/scans/{scan_id}", headers={"Authorization": f"Bearer {token}"})
        assert detail_resp.status_code == 200
        assert detail_resp.json()["id"] == scan_id

    def test_get_nonexistent_scan_returns_404(self, test_org_and_users):
        token = _token_for(test_org_and_users["analyst"])
        random_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/scans/{random_id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"
