"""
Test suite for Phase 9 — Agent management endpoints.

Tests use SQLite in-memory DB via conftest.py fixtures.
All tests import from app.* (backend/ is on sys.path via pyproject.toml).
"""

import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.models.agent import Agent, AgentCredential, AgentHeartbeat
from app.models.organization import Organization, Role
from app.models.user import User
from app.core.security import create_access_token, hash_password

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_db():
    from tests.conftest import _TestingSessionLocal
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def test_org_and_users(db_session):
    """Create org + admin + analyst + viewer for agent tests."""
    from app.models.organization import Organization, Role
    from app.models.user import User
    from app.core.seed import CANONICAL_ROLES

    org = Organization(name="AgentTestOrg", slug="agent-test-org")
    db_session.add(org)
    db_session.flush()

    # Create roles if they don't already exist (same pattern as test_auth.py)
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
        email="agentadmin@test.com",
        password_hash=hash_password("AdminPass123!"),
        username="agent-admin",
        is_active=True,
    )
    analyst = User(
        organization_id=org.id,
        role_id=roles["Security Analyst"].id,
        email="agentanalyst@test.com",
        password_hash=hash_password("AnalystPass123!"),
        username="agent-analyst",
        is_active=True,
    )
    viewer = User(
        organization_id=org.id,
        role_id=roles["Viewer"].id,
        email="agentviewer@test.com",
        password_hash=hash_password("ViewerPass123!"),
        username="agent-viewer",
        is_active=True,
    )
    db_session.add_all([admin, analyst, viewer])
    db_session.commit()
    return {"org": org, "admin": admin, "analyst": analyst, "viewer": viewer, "roles": roles}


def _token_for(user):
    from app.models.organization import Role
    from tests.conftest import _TestingSessionLocal
    db = _TestingSessionLocal()
    role = db.query(Role).filter(Role.id == user.role_id).first()
    db.close()
    return create_access_token(
        subject=str(user.id),
        role_name=role.name,
        organization_id=str(user.organization_id),
    )


# ---------------------------------------------------------------------------
# Tests: Enrollment Token
# ---------------------------------------------------------------------------

class TestEnrollmentToken:
    def test_admin_can_generate_token(self, test_org_and_users):
        admin = test_org_and_users["admin"]
        token = _token_for(admin)
        resp = client.post(
            "/api/v1/agents/enrollment-token",
            json={"agent_name": "test-agent", "expires_in_minutes": 60},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "token" in data
        assert "expires_at" in data

    def test_viewer_cannot_generate_token(self, test_org_and_users):
        viewer = test_org_and_users["viewer"]
        token = _token_for(viewer)
        resp = client.post(
            "/api/v1/agents/enrollment-token",
            json={"agent_name": "test", "expires_in_minutes": 60},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_no_auth_returns_401(self):
        resp = client.post(
            "/api/v1/agents/enrollment-token",
            json={"agent_name": "test", "expires_in_minutes": 60},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_register_with_valid_token(self, test_org_and_users):
        admin = test_org_and_users["admin"]
        admin_token = _token_for(admin)

        # Generate enrollment token
        resp = client.post(
            "/api/v1/agents/enrollment-token",
            json={"agent_name": "my-agent", "expires_in_minutes": 60},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        enrollment_token = resp.json()["token"]

        # Register
        resp2 = client.post(
            "/api/v1/agents/register",
            json={
                "enrollment_token": enrollment_token,
                "name": "my-agent",
                "hostname": "my-laptop",
                "version": "1.0.0",
            },
        )
        assert resp2.status_code == 201, resp2.text
        data = resp2.json()
        assert "id" in data
        assert data["status"] == "PENDING"
        assert "credential" in data
        assert "token" in data["credential"]

    def test_register_with_invalid_token_returns_401(self):
        resp = client.post(
            "/api/v1/agents/register",
            json={
                "enrollment_token": "invalid-token-123",
                "name": "bad-agent",
                "hostname": "bad-host",
                "version": "1.0.0",
            },
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AGENT_NOT_AUTHORIZED"


# ---------------------------------------------------------------------------
# Tests: Heartbeat
# ---------------------------------------------------------------------------

class TestHeartbeat:
    def _create_agent_with_credential(self, db_session, org_id):
        """Helper: create an Agent + AgentCredential and return (agent, raw_token)."""
        agent = Agent(
            organization_id=org_id,
            name="heartbeat-test-agent",
            hostname="test-host",
            version="1.0.0",
            status="PENDING",
            is_active=True,
        )
        db_session.add(agent)
        db_session.flush()

        raw_token = secrets.token_urlsafe(48)
        cred_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        cred = AgentCredential(
            agent_id=agent.id,
            credential_hash=cred_hash,
            type="token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            is_active=True,
        )
        db_session.add(cred)
        db_session.commit()
        return agent, raw_token

    def test_heartbeat_updates_agent_status(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        agent, raw_token = self._create_agent_with_credential(db_session, org.id)

        ts = datetime.now(timezone.utc).replace(microsecond=0)
        resp = client.post(
            "/api/v1/agents/heartbeat",
            json={
                "agent_id": str(agent.id),
                "timestamp": ts.isoformat(),
                "status": "ONLINE",
                "version": "1.0.0",
                "cpu_percent": 25.5,
                "memory_percent": 60.0,
                "details": {"disk_usage_percent": 40},
            },
            headers={"Authorization": f"Bearer {raw_token}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["status"] == "ONLINE"

    def test_heartbeat_idempotent(self, test_org_and_users, db_session):
        """Same (agent_id, timestamp) sent twice must result in only 1 DB row."""
        org = test_org_and_users["org"]
        agent, raw_token = self._create_agent_with_credential(db_session, org.id)

        ts = datetime.now(timezone.utc).replace(microsecond=0)
        payload = {
            "agent_id": str(agent.id),
            "timestamp": ts.isoformat(),
            "status": "ONLINE",
            "version": "1.0.0",
            "cpu_percent": 30.0,
            "memory_percent": 50.0,
        }
        # Send twice
        client.post("/api/v1/agents/heartbeat", json=payload,
                    headers={"Authorization": f"Bearer {raw_token}"})
        client.post("/api/v1/agents/heartbeat", json=payload,
                    headers={"Authorization": f"Bearer {raw_token}"})

        db_session.expire_all()
        count = db_session.query(AgentHeartbeat).filter(
            AgentHeartbeat.agent_id == agent.id,
        ).count()
        # Should only have 1 heartbeat row for this agent (just created)
        assert count == 1

    def test_invalid_credential_returns_401(self):
        resp = client.post(
            "/api/v1/agents/heartbeat",
            json={"agent_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(),
                  "status": "ONLINE", "version": "1.0.0"},
            headers={"Authorization": "Bearer invalid-credential-token"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AGENT_NOT_AUTHORIZED"


# ---------------------------------------------------------------------------
# Tests: List and Get agents
# ---------------------------------------------------------------------------

class TestListGetAgents:
    def test_analyst_can_list_agents(self, test_org_and_users):
        analyst = test_org_and_users["analyst"]
        token = _token_for(analyst)
        resp = client.get("/api/v1/agents/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_viewer_cannot_list_agents(self, test_org_and_users):
        viewer = test_org_and_users["viewer"]
        token = _token_for(viewer)
        resp = client.get("/api/v1/agents/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_get_nonexistent_agent_returns_404(self, test_org_and_users):
        admin = test_org_and_users["admin"]
        token = _token_for(admin)
        resp = client.get(
            f"/api/v1/agents/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_no_auth_returns_401(self):
        resp = client.get("/api/v1/agents/")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: Revoke
# ---------------------------------------------------------------------------

class TestRevoke:
    def test_admin_can_revoke_agent(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]

        # Create agent
        agent = Agent(
            organization_id=org.id,
            name="revoke-test-agent",
            hostname="revoke-host",
            status="ONLINE",
            is_active=True,
        )
        db_session.add(agent)
        db_session.commit()

        token = _token_for(admin)
        resp = client.post(
            f"/api/v1/agents/{agent.id}/revoke",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["is_active"] == False

    def test_viewer_cannot_revoke_agent(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        viewer = test_org_and_users["viewer"]

        agent = Agent(
            organization_id=org.id,
            name="no-revoke-agent",
            hostname="no-revoke-host",
            status="ONLINE",
            is_active=True,
        )
        db_session.add(agent)
        db_session.commit()

        token = _token_for(viewer)
        resp = client.post(
            f"/api/v1/agents/{agent.id}/revoke",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
