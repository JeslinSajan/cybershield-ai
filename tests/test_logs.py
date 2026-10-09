"""
Test suite for Phase 14 — Log Management.
Covers agent log ingestion, auto-severity mapping, and validation.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.core.seed import CANONICAL_ROLES
from app.main import app
from app.models.agent import Agent, AgentCredential
from app.models.device import Device
from app.models.log import Log
from app.models.organization import Organization, Role
from app.models.user import User

client = TestClient(app)


class TestAgentLogIngestion:
    @pytest.fixture
    def setup_agent_env(self, db_session):
        uid = uuid.uuid4().hex[:8]
        org = Organization(name=f"LogOrg-{uid}", slug=f"log-org-{uid}")
        db_session.add(org)
        db_session.flush()

        agent = Agent(
            organization_id=org.id,
            name=f"log-agent-{uid}",
            hostname="log-host",
            status="ONLINE",
            is_active=True,
        )
        db_session.add(agent)
        db_session.flush()

        raw_cred = secrets.token_urlsafe(48)
        cred_hash = hashlib.sha256(raw_cred.encode()).hexdigest()
        cred = AgentCredential(
            agent_id=agent.id,
            credential_hash=cred_hash,
            type="token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            is_active=True,
        )
        db_session.add(cred)

        # Linked device for this agent
        device = Device(
            organization_id=org.id,
            agent_id=agent.id,
            ip_address="192.168.1.77",
            hostname="log-host",
            status="online",
        )
        db_session.add(device)
        db_session.commit()

        return {
            "org": org,
            "agent": agent,
            "raw_cred": raw_cred,
            "device": device,
        }

    def test_agent_can_ingest_single_log(self, db_session, setup_agent_env):
        env = setup_agent_env
        raw_cred = env["raw_cred"]
        agent = env["agent"]

        payload = {
            "logs": [
                {
                    "source": "auth.log",
                    "event_type": "login_failure",
                    "message": "Failed password for invalid user admin from 10.0.0.99 port 22",
                    "source_ip": "10.0.0.99",
                    "username": "admin",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ]
        }

        resp = client.post(
            "/api/v1/agents/logs",
            headers={"Authorization": f"Bearer {raw_cred}"},
            json=payload,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["ingested_count"] == 1
        assert len(data["log_ids"]) == 1

        log_id = uuid.UUID(data["log_ids"][0])
        log_row = db_session.query(Log).filter(Log.id == log_id).first()
        assert log_row is not None
        assert log_row.organization_id == agent.organization_id
        assert log_row.agent_id == agent.id
        assert log_row.source == "auth.log"
        assert log_row.event_type == "login_failure"
        assert log_row.severity == "medium"  # auto-mapped
        assert log_row.source_ip == "10.0.0.99"
        assert log_row.username == "admin"
        assert log_row.device_id == env["device"].id  # linked to agent's device

    def test_agent_can_ingest_batch_logs(self, db_session, setup_agent_env):
        env = setup_agent_env
        raw_cred = env["raw_cred"]

        payload = {
            "logs": [
                {
                    "source": "windows_security",
                    "event_type": "login_success",
                    "message": "An account was successfully logged on: Administrator",
                    "source_ip": "192.168.1.10",
                    "username": "Administrator",
                },
                {
                    "source": "windows_security",
                    "event_type": "login_failure",
                    "message": "An account failed to log on: Guest",
                    "source_ip": "192.168.1.20",
                    "username": "Guest",
                },
                {
                    "source": "auth.log",
                    "event_type": "session_close",
                    "message": "session closed for user ubuntu",
                    "username": "ubuntu",
                },
            ]
        }

        resp = client.post(
            "/api/v1/agents/logs",
            headers={"Authorization": f"Bearer {raw_cred}"},
            json=payload,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["ingested_count"] == 3
        assert len(data["log_ids"]) == 3

    def test_auto_severity_mapping(self, db_session, setup_agent_env):
        env = setup_agent_env
        raw_cred = env["raw_cred"]

        payload = {
            "logs": [
                {
                    "source": "auth.log",
                    "event_type": "login_failure",
                    "message": "failed password",
                },
                {
                    "source": "auth.log",
                    "event_type": "login_success",
                    "message": "accepted password",
                },
                {
                    "source": "auth.log",
                    "event_type": "custom_event",
                    "message": "some info event",
                },
                {
                    "source": "auth.log",
                    "event_type": "login_failure",
                    "severity": "Critical",
                    "message": "critical brute force",
                },
            ]
        }

        resp = client.post(
            "/api/v1/agents/logs",
            headers={"Authorization": f"Bearer {raw_cred}"},
            json=payload,
        )
        assert resp.status_code == 201
        ids = [uuid.UUID(i) for i in resp.json()["log_ids"]]

        logs = db_session.query(Log).filter(Log.id.in_(ids)).all()
        by_msg = {l.message: l.severity for l in logs}

        assert by_msg["failed password"] == "medium"
        assert by_msg["accepted password"] == "low"
        assert by_msg["some info event"] == "info"
        assert by_msg["critical brute force"] == "critical"

    def test_raw_list_payload_supported(self, db_session, setup_agent_env):
        """Endpoints accepts list directly as well as {"logs": [...]} envelope."""
        env = setup_agent_env
        raw_cred = env["raw_cred"]

        raw_list_payload = [
            {
                "source": "auth.log",
                "event_type": "login_success",
                "message": "Accepted publickey",
            }
        ]

        resp = client.post(
            "/api/v1/agents/logs",
            headers={"Authorization": f"Bearer {raw_cred}"},
            json=raw_list_payload,
        )
        assert resp.status_code == 201
        assert resp.json()["ingested_count"] == 1

    def test_unauthenticated_or_invalid_credential_rejected(self):
        # Missing auth header
        resp_no_auth = client.post(
            "/api/v1/agents/logs",
            json={"logs": [{"source": "test", "event_type": "login_success", "message": "msg"}]},
        )
        assert resp_no_auth.status_code == 401

        # Invalid token
        resp_bad_auth = client.post(
            "/api/v1/agents/logs",
            headers={"Authorization": "Bearer invalid_token_123"},
            json={"logs": [{"source": "test", "event_type": "login_success", "message": "msg"}]},
        )
        assert resp_bad_auth.status_code == 401
        assert resp_bad_auth.json()["error"]["code"] == "AGENT_NOT_AUTHORIZED"

    def test_empty_logs_rejected(self, setup_agent_env):
        env = setup_agent_env
        raw_cred = env["raw_cred"]

        resp = client.post(
            "/api/v1/agents/logs",
            headers={"Authorization": f"Bearer {raw_cred}"},
            json={"logs": []},
        )
        assert resp.status_code == 422


class TestLogQueryEndpoints:
    @pytest.fixture
    def setup_query_env(self, db_session):
        uid = uuid.uuid4().hex[:8]
        org1 = Organization(name=f"QueryOrg1-{uid}", slug=f"query-org-1-{uid}")
        org2 = Organization(name=f"QueryOrg2-{uid}", slug=f"query-org-2-{uid}")
        db_session.add_all([org1, org2])
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

        admin1 = User(
            organization_id=org1.id,
            role_id=roles["Administrator"].id,
            email=f"admin-{uid}@test.com",
            username=f"admin-{uid}",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        analyst1 = User(
            organization_id=org1.id,
            role_id=roles["Security Analyst"].id,
            email=f"analyst-{uid}@test.com",
            username=f"analyst-{uid}",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        viewer1 = User(
            organization_id=org1.id,
            role_id=roles["Viewer"].id,
            email=f"viewer-{uid}@test.com",
            username=f"viewer-{uid}",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        viewer2 = User(
            organization_id=org2.id,
            role_id=roles["Viewer"].id,
            email=f"viewer2-{uid}@test.com",
            username=f"viewer2-{uid}",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        db_session.add_all([admin1, analyst1, viewer1, viewer2])
        db_session.flush()

        # Agents
        agent1 = Agent(
            organization_id=org1.id,
            name=f"agent1-{uid}",
            hostname="host-1",
            status="ONLINE",
            is_active=True,
        )
        agent2 = Agent(
            organization_id=org2.id,
            name=f"agent2-{uid}",
            hostname="host-2",
            status="ONLINE",
            is_active=True,
        )
        db_session.add_all([agent1, agent2])
        db_session.flush()

        # Devices
        dev1 = Device(
            organization_id=org1.id,
            agent_id=agent1.id,
            ip_address="192.168.1.50",
            hostname="server-50",
            status="online",
        )
        db_session.add(dev1)
        db_session.flush()

        # Logs in Org1
        t1 = datetime(2026, 8, 24, 10, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 8, 24, 11, 0, 0, tzinfo=timezone.utc)
        t3 = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
        t4 = datetime(2026, 8, 24, 13, 0, 0, tzinfo=timezone.utc)

        log1 = Log(
            organization_id=org1.id,
            agent_id=agent1.id,
            device_id=dev1.id,
            source="auth.log",
            event_type="login_failure",
            severity="medium",
            message="Failed password for invalid user root",
            source_ip="192.168.1.50",
            username="root",
            timestamp=t1,
        )
        log2 = Log(
            organization_id=org1.id,
            agent_id=agent1.id,
            device_id=dev1.id,
            source="auth.log",
            event_type="login_success",
            severity="low",
            message="Accepted publickey for ubuntu",
            source_ip="192.168.1.50",
            username="ubuntu",
            timestamp=t2,
        )
        log3 = Log(
            organization_id=org1.id,
            agent_id=agent1.id,
            source="windows_security",
            event_type="login_failure",
            severity="medium",
            message="An account failed to log on: Administrator",
            source_ip="10.0.0.5",
            username="Administrator",
            timestamp=t3,
        )
        log4 = Log(
            organization_id=org1.id,
            agent_id=agent1.id,
            source="syslog",
            event_type="system_warning",
            severity="high",
            message="Disk space low",
            source_ip="127.0.0.1",
            username=None,
            timestamp=t4,
        )

        # Log in Org2
        log_org2 = Log(
            organization_id=org2.id,
            agent_id=agent2.id,
            source="auth.log",
            event_type="login_failure",
            severity="medium",
            message="Org2 log event",
            source_ip="10.200.0.1",
            username="admin2",
            timestamp=t4,
        )

        db_session.add_all([log1, log2, log3, log4, log_org2])
        db_session.commit()

        token_admin = create_access_token(str(admin1.id), "Administrator", str(org1.id))
        token_analyst = create_access_token(str(analyst1.id), "Security Analyst", str(org1.id))
        token_viewer = create_access_token(str(viewer1.id), "Viewer", str(org1.id))
        token_org2 = create_access_token(str(viewer2.id), "Viewer", str(org2.id))

        return {
            "org1": org1,
            "org2": org2,
            "agent1": agent1,
            "dev1": dev1,
            "log1": log1,
            "log2": log2,
            "log3": log3,
            "log4": log4,
            "log_org2": log_org2,
            "tokens": {
                "admin": token_admin,
                "analyst": token_analyst,
                "viewer": token_viewer,
                "org2": token_org2,
            },
        }

    def test_all_three_roles_can_list_logs(self, setup_query_env):
        tokens = setup_query_env["tokens"]
        for role in ["admin", "analyst", "viewer"]:
            resp = client.get(
                "/api/v1/logs/",
                headers={"Authorization": f"Bearer {tokens[role]}"},
            )
            assert resp.status_code == 200, f"Role {role} failed: {resp.text}"
            logs = resp.json()
            assert len(logs) == 4
            # Verify ordering is newest first (t4 down to t1)
            timestamps = [item["timestamp"] for item in logs]
            assert timestamps == sorted(timestamps, reverse=True)

    def test_unauthenticated_request_rejected(self, setup_query_env):
        resp_list = client.get("/api/v1/logs/")
        assert resp_list.status_code == 401

        log1 = setup_query_env["log1"]
        resp_detail = client.get(f"/api/v1/logs/{log1.id}")
        assert resp_detail.status_code == 401

    def test_filter_by_event_type(self, setup_query_env):
        token = setup_query_env["tokens"]["analyst"]
        resp = client.get(
            "/api/v1/logs/?event_type=login_failure",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 2
        for item in logs:
            assert item["event_type"] == "login_failure"

    def test_filter_by_source(self, setup_query_env):
        token = setup_query_env["tokens"]["viewer"]
        resp = client.get(
            "/api/v1/logs/?source=windows_security",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 1
        assert logs[0]["source"] == "windows_security"
        assert logs[0]["username"] == "Administrator"

    def test_filter_by_severity(self, setup_query_env):
        token = setup_query_env["tokens"]["admin"]
        resp = client.get(
            "/api/v1/logs/?severity=high",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 1
        assert logs[0]["severity"] == "high"
        assert logs[0]["message"] == "Disk space low"

    def test_filter_by_username_and_source_ip(self, setup_query_env):
        token = setup_query_env["tokens"]["analyst"]
        # Filter by username
        resp_user = client.get(
            "/api/v1/logs/?username=root",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_user.status_code == 200
        logs = resp_user.json()
        assert len(logs) == 1
        assert logs[0]["username"] == "root"

        # Filter by source IP
        resp_ip = client.get(
            "/api/v1/logs/?source_ip=192.168.1.50",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_ip.status_code == 200
        logs_ip = resp_ip.json()
        assert len(logs_ip) == 2
        for item in logs_ip:
            assert item["source_ip"] == "192.168.1.50"

    def test_filter_by_date_range(self, setup_query_env):
        token = setup_query_env["tokens"]["viewer"]
        # Only t2 (11:00) and t3 (12:00)
        from_str = "2026-08-24T10:30:00Z"
        to_str = "2026-08-24T12:30:00Z"

        resp = client.get(
            f"/api/v1/logs/?from_date={from_str}&to_date={to_str}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 2
        event_types = {item["event_type"] for item in logs}
        assert event_types == {"login_success", "login_failure"}

        # Test start_time and end_time aliases
        resp_alias = client.get(
            f"/api/v1/logs/?start_time={from_str}&end_time={to_str}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_alias.status_code == 200
        assert len(resp_alias.json()) == 2

    def test_pagination(self, setup_query_env):
        token = setup_query_env["tokens"]["admin"]
        # Limit 2, Offset 0 -> returns first 2 logs (newest)
        resp1 = client.get(
            "/api/v1/logs/?limit=2&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 200
        page1 = resp1.json()
        assert len(page1) == 2

        # Limit 2, Offset 2 -> returns next 2 logs
        resp2 = client.get(
            "/api/v1/logs/?limit=2&offset=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 200
        page2 = resp2.json()
        assert len(page2) == 2

        ids_page1 = {item["id"] for item in page1}
        ids_page2 = {item["id"] for item in page2}
        assert ids_page1.isdisjoint(ids_page2)

    def test_get_single_log_success(self, setup_query_env):
        tokens = setup_query_env["tokens"]
        log1 = setup_query_env["log1"]

        for role in ["admin", "analyst", "viewer"]:
            resp = client.get(
                f"/api/v1/logs/{log1.id}",
                headers={"Authorization": f"Bearer {tokens[role]}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == str(log1.id)
            assert data["source"] == "auth.log"
            assert data["event_type"] == "login_failure"
            assert data["severity"] == "medium"
            assert data["username"] == "root"
            assert data["source_ip"] == "192.168.1.50"
            assert data["device_id"] == str(setup_query_env["dev1"].id)
            assert data["agent_id"] == str(setup_query_env["agent1"].id)

    def test_get_single_log_not_found(self, setup_query_env):
        token = setup_query_env["tokens"]["analyst"]
        missing_id = uuid.uuid4()
        resp = client.get(
            f"/api/v1/logs/{missing_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        error_body = resp.json()
        assert "error" in error_body
        assert error_body["error"]["code"] == "NOT_FOUND"

    def test_organization_isolation(self, setup_query_env):
        token_org2 = setup_query_env["tokens"]["org2"]
        log1_org1 = setup_query_env["log1"]
        log_org2 = setup_query_env["log_org2"]

        # Org2 listing only sees its own logs
        resp = client.get(
            "/api/v1/logs/",
            headers={"Authorization": f"Bearer {token_org2}"},
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 1
        assert logs[0]["id"] == str(log_org2.id)

        # Org2 attempting to read Org1 log by ID receives 404
        resp_isolated = client.get(
            f"/api/v1/logs/{log1_org1.id}",
            headers={"Authorization": f"Bearer {token_org2}"},
        )
        assert resp_isolated.status_code == 404
        assert resp_isolated.json()["error"]["code"] == "NOT_FOUND"
