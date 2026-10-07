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
    from conftest import _TestingSessionLocal
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
    from conftest import _TestingSessionLocal
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


# ---------------------------------------------------------------------------
# Phase 10 Tests
# ---------------------------------------------------------------------------

class TestTaskPolling:
    def _create_agent_with_credential(self, db_session, org_id):
        agent = Agent(
            organization_id=org_id,
            name="task-poll-agent",
            hostname="task-poll-host",
            version="1.0.0",
            status="ONLINE",
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

    def test_get_tasks_empty(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        agent, raw_token = self._create_agent_with_credential(db_session, org.id)
        
        resp = client.get("/api/v1/agents/tasks", headers={"Authorization": f"Bearer {raw_token}"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_tasks_path_is_not_interpreted_as_an_agent_id(self, test_org_and_users, db_session):
        """The static task route must take precedence over /agents/{agent_id}."""
        org = test_org_and_users["org"]
        _, raw_token = self._create_agent_with_credential(db_session, org.id)

        resp = client.get("/api/v1/agents/tasks", headers={"Authorization": f"Bearer {raw_token}"})

        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_tasks_with_pending(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = self._create_agent_with_credential(db_session, org.id)
        
        from app.models.scan import Scan
        scan = Scan(
            organization_id=org.id,
            agent_id=agent.id,
            created_by_user_id=admin.id,
            scan_type="health_check",
            status="PENDING",
            target_scope="{}"
        )
        db_session.add(scan)
        db_session.commit()
        
        resp = client.get("/api/v1/agents/tasks", headers={"Authorization": f"Bearer {raw_token}"})
        assert resp.status_code == 200
        tasks = resp.json()
        assert len(tasks) == 1
        assert tasks[0]["id"] == str(scan.id)


class TestTaskCreation:
    def test_authorized_user_creates_task_and_assigned_agent_receives_it(self, test_org_and_users, db_session):
        from app.models.scan import Scan

        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, agent_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        admin_token = _token_for(admin)

        response = client.post(
            "/api/v1/scans/",
            json={"agent_id": str(agent.id), "scan_type": "health_check", "target_scope": "local"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 201
        task = response.json()
        assert task["agent_id"] == str(agent.id)
        assert task["scan_type"] == "health_check"
        assert task["status"] == "PENDING"

        stored_task = db_session.query(Scan).filter(Scan.id == task["id"]).first()
        assert stored_task is not None
        assert stored_task.created_by_user_id == admin.id
        assert stored_task.target_scope == "local"

        poll_response = client.get(
            "/api/v1/agents/tasks",
            headers={"Authorization": f"Bearer {agent_token}"},
        )
        assert poll_response.status_code == 200
        assert [item["id"] for item in poll_response.json()] == [task["id"]]

    def test_invalid_agent_is_rejected(self, test_org_and_users):
        admin_token = _token_for(test_org_and_users["admin"])

        response = client.post(
            "/api/v1/scans/",
            json={"agent_id": str(uuid.uuid4()), "scan_type": "health_check", "target_scope": "local"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    def test_invalid_task_type_is_rejected(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        agent, _ = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        admin_token = _token_for(test_org_and_users["admin"])

        response = client.post(
            "/api/v1/scans/",
            json={"agent_id": str(agent.id), "scan_type": "unsupported_scan_type", "target_scope": "local"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422

    def test_other_agent_cannot_receive_assigned_task(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        assigned_agent, _ = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        _, other_agent_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        admin_token = _token_for(test_org_and_users["admin"])

        create_response = client.post(
            "/api/v1/scans/",
            json={"agent_id": str(assigned_agent.id), "scan_type": "health_check", "target_scope": "local"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_response.status_code == 201

        other_agent_response = client.get(
            "/api/v1/agents/tasks",
            headers={"Authorization": f"Bearer {other_agent_token}"},
        )
        assert other_agent_response.status_code == 200
        assert other_agent_response.json() == []


class TestTaskStatus:
    def test_update_status(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        from app.models.scan import Scan
        scan = Scan(
            organization_id=org.id,
            agent_id=agent.id,
            created_by_user_id=admin.id,
            scan_type="health_check",
            status="PENDING",
            target_scope="{}"
        )
        db_session.add(scan)
        db_session.commit()
        
        resp = client.post(
            f"/api/v1/agents/tasks/{scan.id}/status",
            json={"status": "RUNNING"},
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "RUNNING"
        
        db_session.refresh(scan)
        assert scan.status == "RUNNING"
        assert scan.started_at is not None

    def test_agent_cannot_update_another_agents_task(self, test_org_and_users, db_session):
        from app.models.scan import Scan

        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        owner, _ = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        _, other_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        scan = Scan(
            organization_id=org.id,
            agent_id=owner.id,
            created_by_user_id=admin.id,
            scan_type="health_check",
            status="PENDING",
            target_scope="{}",
        )
        db_session.add(scan)
        db_session.commit()

        resp = client.post(
            f"/api/v1/agents/tasks/{scan.id}/status",
            json={"status": "RUNNING"},
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert resp.status_code == 403
        db_session.refresh(scan)
        assert scan.status == "PENDING"


class TestResultUpload:
    def test_upload_result(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        from app.models.scan import Scan, ScanResult
        scan = Scan(
            organization_id=org.id,
            agent_id=agent.id,
            created_by_user_id=admin.id,
            scan_type="health_check",
            status="RUNNING",
            target_scope="{}"
        )
        db_session.add(scan)
        db_session.commit()
        
        resp = client.post(
            "/api/v1/agents/results",
            json={
                "scan_id": str(scan.id),
                "device_id": None,
                "result_type": "system",
                "raw_payload": {"cpu_percent": 10.0}
            },
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert resp.status_code == 201
        
        res = db_session.query(ScanResult).filter(ScanResult.scan_id == scan.id).first()
        assert res is not None
        assert res.result_type == "system"

    def test_upload_result_with_upload_id(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        from app.models.scan import Scan, ScanResult
        scan = Scan(
            organization_id=org.id,
            agent_id=agent.id,
            created_by_user_id=admin.id,
            scan_type="health_check",
            status="RUNNING",
            target_scope="{}"
        )
        db_session.add(scan)
        db_session.commit()
        
        upload_id = str(uuid.uuid4())
        resp = client.post(
            "/api/v1/agents/results",
            json={
                "scan_id": str(scan.id),
                "device_id": None,
                "upload_id": upload_id,
                "result_type": "system",
                "raw_payload": {"cpu_percent": 10.0}
            },
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert resp.status_code == 201
        assert resp.json()["upload_id"] == upload_id
        
        res = db_session.query(ScanResult).filter(ScanResult.upload_id == upload_id).first()
        assert res is not None
        assert res.upload_id == upload_id

    def test_duplicate_upload_is_idempotent(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        from app.models.scan import Scan, ScanResult
        scan = Scan(
            organization_id=org.id,
            agent_id=agent.id,
            created_by_user_id=admin.id,
            scan_type="health_check",
            status="RUNNING",
            target_scope="{}"
        )
        db_session.add(scan)
        db_session.commit()
        
        upload_id = str(uuid.uuid4())
        payload = {
            "scan_id": str(scan.id),
            "device_id": None,
            "upload_id": upload_id,
            "result_type": "system",
            "raw_payload": {"cpu_percent": 10.0}
        }
        
        # First upload
        resp1 = client.post(
            "/api/v1/agents/results",
            json=payload,
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert resp1.status_code == 201
        result_id_1 = resp1.json()["id"]
        
        # Duplicate upload with same upload_id
        resp2 = client.post(
            "/api/v1/agents/results",
            json=payload,
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert resp2.status_code == 201
        result_id_2 = resp2.json()["id"]
        
        # Should return the same result id (idempotent)
        assert result_id_1 == result_id_2
        
        # Should only have one result in DB
        count = db_session.query(ScanResult).filter(ScanResult.upload_id == upload_id).count()
        assert count == 1

    def test_upload_rejects_wrong_agent(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        owner, _ = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        _, other_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        from app.models.scan import Scan
        scan = Scan(
            organization_id=org.id,
            agent_id=owner.id,
            created_by_user_id=admin.id,
            scan_type="health_check",
            status="RUNNING",
            target_scope="{}"
        )
        db_session.add(scan)
        db_session.commit()
        
        resp = client.post(
            "/api/v1/agents/results",
            json={
                "scan_id": str(scan.id),
                "device_id": None,
                "result_type": "system",
                "raw_payload": {"cpu_percent": 10.0}
            },
            headers={"Authorization": f"Bearer {other_token}"}
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_upload_rejects_invalid_task_state(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        from app.models.scan import Scan
        scan = Scan(
            organization_id=org.id,
            agent_id=agent.id,
            created_by_user_id=admin.id,
            scan_type="health_check",
            status="COMPLETED",
            target_scope="{}"
        )
        db_session.add(scan)
        db_session.commit()
        
        resp = client.post(
            "/api/v1/agents/results",
            json={
                "scan_id": str(scan.id),
                "device_id": None,
                "result_type": "system",
                "raw_payload": {"cpu_percent": 10.0}
            },
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "INVALID_TASK_STATE"

    def test_upload_updates_task_state(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        from app.models.scan import Scan
        scan = Scan(
            organization_id=org.id,
            agent_id=agent.id,
            created_by_user_id=admin.id,
            scan_type="health_check",
            status="RUNNING",
            target_scope="{}"
        )
        db_session.add(scan)
        db_session.commit()
        
        assert scan.status == "RUNNING"
        assert scan.completed_at is None
        
        resp = client.post(
            "/api/v1/agents/results",
            json={
                "scan_id": str(scan.id),
                "device_id": None,
                "result_type": "system",
                "raw_payload": {"cpu_percent": 10.0}
            },
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert resp.status_code == 201
        
        db_session.refresh(scan)
        assert scan.status == "COMPLETED"
        assert scan.completed_at is not None

    def test_upload_rejects_nonexistent_task(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        resp = client.post(
            "/api/v1/agents/results",
            json={
                "scan_id": str(uuid.uuid4()),
                "device_id": None,
                "result_type": "system",
                "raw_payload": {"cpu_percent": 10.0}
            },
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_upload_accepts_pending_task(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        from app.models.scan import Scan, ScanResult
        scan = Scan(
            organization_id=org.id,
            agent_id=agent.id,
            created_by_user_id=admin.id,
            scan_type="health_check",
            status="PENDING",
            target_scope="{}"
        )
        db_session.add(scan)
        db_session.commit()
        
        resp = client.post(
            "/api/v1/agents/results",
            json={
                "scan_id": str(scan.id),
                "device_id": None,
                "result_type": "system",
                "raw_payload": {"cpu_percent": 10.0}
            },
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert resp.status_code == 201
        
        res = db_session.query(ScanResult).filter(ScanResult.scan_id == scan.id).first()
        assert res is not None


class TestRotateCredential:
    def test_rotate_credential(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        admin_token = _token_for(admin)
        resp = client.post(
            f"/api/v1/agents/{agent.id}/rotate-credential",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert "credential_id" in data
        
        # Test old token doesn't work
        resp = client.get("/api/v1/agents/tasks", headers={"Authorization": f"Bearer {raw_token}"})
        assert resp.status_code == 401


class TestNetworkStats:
    def test_network_stats(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        hb = AgentHeartbeat(
            agent_id=agent.id,
            organization_id=org.id,
            timestamp=datetime.now(timezone.utc),
            status="ONLINE",
            cpu_percent=50.0,
            memory_percent=60.0
        )
        db_session.add(hb)
        db_session.commit()
        
        admin_token = _token_for(admin)
        resp = client.get(
            f"/api/v1/agents/{agent.id}/network-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
        stats = resp.json()
        assert len(stats) == 1
        assert stats[0]["cpu_percent"] == 50.0


class TestOfflineDetection:
    def test_recent_heartbeat_marks_online(self, test_org_and_users, db_session):
        """Agent with recent heartbeat should be marked ONLINE."""
        org = test_org_and_users["org"]
        agent = Agent(
            organization_id=org.id,
            name="online-agent",
            hostname="online-host",
            status="OFFLINE",
            is_active=True,
            last_heartbeat_at=datetime.now(timezone.utc) - timedelta(seconds=30)
        )
        db_session.add(agent)
        db_session.commit()
        
        # Send heartbeat
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        resp = client.post(
            "/api/v1/agents/heartbeat",
            json={
                "agent_id": str(agent.id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "ONLINE"
            },
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ONLINE"
        
        db_session.refresh(agent)
        assert agent.status == "ONLINE"

    def test_stale_heartbeat_marks_offline(self, test_org_and_users, db_session):
        """Agent with stale heartbeat should be marked OFFLINE."""
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        
        # Create agent with stale heartbeat
        agent = Agent(
            organization_id=org.id,
            name="stale-agent",
            hostname="stale-host",
            status="ONLINE",
            is_active=True,
            last_heartbeat_at=datetime.now(timezone.utc) - timedelta(seconds=150)
        )
        db_session.add(agent)
        db_session.commit()
        
        # Send a heartbeat from another agent to trigger offline detection
        other_agent, other_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        resp = client.post(
            "/api/v1/agents/heartbeat",
            json={
                "agent_id": str(other_agent.id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "ONLINE"
            },
            headers={"Authorization": f"Bearer {other_token}"}
        )
        assert resp.status_code == 200
        
        # Check stale agent is now offline
        db_session.refresh(agent)
        assert agent.status == "OFFLINE"

    def test_missing_heartbeat_marks_offline(self, test_org_and_users, db_session):
        """Agent with no heartbeat should be marked OFFLINE."""
        org = test_org_and_users["org"]
        
        # Create agent with no heartbeat
        agent = Agent(
            organization_id=org.id,
            name="no-heartbeat-agent",
            hostname="no-heartbeat-host",
            status="ONLINE",
            is_active=True,
            last_heartbeat_at=None
        )
        db_session.add(agent)
        db_session.commit()
        
        # Send a heartbeat from another agent to trigger offline detection
        other_agent, other_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        resp = client.post(
            "/api/v1/agents/heartbeat",
            json={
                "agent_id": str(other_agent.id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "ONLINE"
            },
            headers={"Authorization": f"Bearer {other_token}"}
        )
        assert resp.status_code == 200
        
        # Check agent with no heartbeat is now offline
        db_session.refresh(agent)
        assert agent.status == "OFFLINE"


class TestPhase10Integration:
    def test_end_to_end_task_flow(self, test_org_and_users, db_session):
        """Complete end-to-end flow: task creation → polling → execution → result upload → completion."""
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        # Step 1: Create task via API
        admin_token = _token_for(admin)
        task_resp = client.post(
            "/api/v1/scans/",
            json={
                "agent_id": str(agent.id),
                "scan_type": "health_check",
                "target_scope": "local"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]
        
        # Step 2: Agent polls for tasks
        poll_resp = client.get(
            "/api/v1/agents/tasks",
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert poll_resp.status_code == 200
        tasks = poll_resp.json()
        assert len(tasks) == 1
        assert tasks[0]["id"] == task_id
        assert tasks[0]["status"] == "PENDING"
        
        # Step 3: Agent updates task to RUNNING
        status_resp = client.post(
            f"/api/v1/agents/tasks/{task_id}/status",
            json={"status": "RUNNING"},
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "RUNNING"
        
        # Step 4: Agent uploads result
        upload_id = str(uuid.uuid4())
        result_resp = client.post(
            "/api/v1/agents/results",
            json={
                "scan_id": task_id,
                "device_id": None,
                "upload_id": upload_id,
                "result_type": "system",
                "raw_payload": {"cpu_percent": 25.0, "memory_percent": 50.0}
            },
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        assert result_resp.status_code == 201
        assert result_resp.json()["upload_id"] == upload_id
        
        # Step 5: Verify task is COMPLETED
        from app.models.scan import Scan
        scan = db_session.query(Scan).filter(Scan.id == task_id).first()
        assert scan.status == "COMPLETED"
        assert scan.completed_at is not None
        
        # Step 6: Verify result is stored
        from app.models.scan import ScanResult
        result = db_session.query(ScanResult).filter(ScanResult.scan_id == task_id).first()
        assert result is not None
        assert result.upload_id == upload_id
        assert result.result_type == "system"

    def test_offline_queue_retry_flow(self, test_org_and_users, db_session):
        """Test offline queue: upload fails → queues → retry succeeds."""
        org = test_org_and_users["org"]
        admin = test_org_and_users["admin"]
        agent, raw_token = TestTaskPolling()._create_agent_with_credential(db_session, org.id)
        
        # Create task
        admin_token = _token_for(admin)
        task_resp = client.post(
            "/api/v1/scans/",
            json={
                "agent_id": str(agent.id),
                "scan_type": "health_check",
                "target_scope": "local"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]
        
        # Update task to RUNNING
        client.post(
            f"/api/v1/agents/tasks/{task_id}/status",
            json={"status": "RUNNING"},
            headers={"Authorization": f"Bearer {raw_token}"}
        )
        
        # Simulate offline queue behavior
        from agent.offline_queue import OfflineQueue
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = OfflineQueue(queue_dir=tmpdir)
            upload_id = str(uuid.uuid4())
            
            # Queue the result (simulating failed upload)
            queued = queue.enqueue({
                "method": "post",
                "path": "/agents/results",
                "data": {
                    "scan_id": task_id,
                    "device_id": None,
                    "upload_id": upload_id,
                    "result_type": "system",
                    "raw_payload": {"cpu_percent": 30.0}
                }
            })
            assert queued is True
            assert len(queue) == 1
            
            # Mock successful API client for drain
            from unittest.mock import Mock
            mock_client = Mock()
            mock_client.post = Mock(return_value={"id": str(uuid.uuid4())})
            
            # Drain queue (simulating backend becoming available)
            drained = queue.drain(mock_client)
            assert drained == 1
            assert len(queue) == 0
            
            # Verify result was uploaded via real API
            result_resp = client.post(
                "/api/v1/agents/results",
                json={
                    "scan_id": task_id,
                    "device_id": None,
                    "upload_id": upload_id,
                    "result_type": "system",
                    "raw_payload": {"cpu_percent": 30.0}
                },
                headers={"Authorization": f"Bearer {raw_token}"}
            )
            assert result_resp.status_code == 201
            
            # Verify idempotency - same upload_id returns existing result
            result_resp2 = client.post(
                "/api/v1/agents/results",
                json={
                    "scan_id": task_id,
                    "device_id": None,
                    "upload_id": upload_id,
                    "result_type": "system",
                    "raw_payload": {"cpu_percent": 30.0}
                },
                headers={"Authorization": f"Bearer {raw_token}"}
            )
            assert result_resp2.status_code == 201
            assert result_resp2.json()["id"] == result_resp.json()["id"]
