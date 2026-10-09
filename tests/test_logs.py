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
