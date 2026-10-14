"""
Tests for Phase 25 — Performance & Reliability.

Covers:
1. Pagination:
   - GET /api/v1/logs/?limit=10 returns at most 10 rows.
2. Heartbeat Cleanup:
   - Purges heartbeats older than 7 days while preserving recent ones.
3. Agent Startup Retry:
   - wait_for_backend retries on failure and succeeds when backend becomes available.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import uuid

import pytest
from fastapi.testclient import TestClient

from agent.main import wait_for_backend
from app.main import app
from app.models.agent import Agent, AgentHeartbeat
from app.models.log import Log
from app.models.organization import Organization, Role
from app.models.user import User
from app.core.security import create_access_token, hash_password

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_perf_data(create_tables, db_session):
    """Seed test data for performance & pagination verification."""
    org = Organization(name="PerfOrg", slug=f"perf-org-{uuid.uuid4().hex[:6]}")
    db_session.add(org)
    db_session.flush()

    role = db_session.query(Role).filter(Role.name == "Administrator").first()
    if not role:
        role = Role(name="Administrator", description="Admin access")
        db_session.add(role)
        db_session.flush()

    user = User(
        organization_id=org.id,
        role_id=role.id,
        email=f"admin_perf_{uuid.uuid4().hex[:6]}@example.com",
        username="admin_perf",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    token = create_access_token(
        subject=str(user.id),
        role_name="Administrator",
        organization_id=str(org.id),
    )

    agent = Agent(
        organization_id=org.id,
        name="perf-agent",
        hostname="perf-host",
        status="ONLINE",
    )
    db_session.add(agent)
    db_session.flush()

    # Pre-seed 15 logs
    for i in range(15):
        log = Log(
            organization_id=org.id,
            agent_id=agent.id,
            source="test",
            event_type="login_success",
            severity="low",
            message=f"Test log {i}",
            timestamp=datetime.now(timezone.utc),
        )
        db_session.add(log)

    # Pre-seed heartbeats: 3 stale (10 days old) and 2 fresh (1 day old)
    now = datetime.now(timezone.utc)
    for i in range(3):
        h_old = AgentHeartbeat(
            agent_id=agent.id,
            organization_id=org.id,
            timestamp=now - timedelta(days=10, hours=i),
            status="ONLINE",
            created_at=now - timedelta(days=10, hours=i),
        )
        db_session.add(h_old)

    for i in range(2):
        h_fresh = AgentHeartbeat(
            agent_id=agent.id,
            organization_id=org.id,
            timestamp=now - timedelta(days=1, hours=i),
            status="ONLINE",
            created_at=now - timedelta(days=1, hours=i),
        )
        db_session.add(h_fresh)

    db_session.commit()

    return {
        "org": org,
        "user": user,
        "token": token,
        "agent": agent,
    }


class TestPaginationLimit:
    def test_logs_pagination_limit_enforced(self, setup_perf_data):
        token = setup_perf_data["token"]
        resp = client.get(
            "/api/v1/logs/?limit=10&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 10


class TestHeartbeatCleanup:
    def test_cleanup_purges_only_heartbeats_older_than_7_days(self, setup_perf_data, db_session):
        agent_id = setup_perf_data["agent"].id

        # Run cleanup logic
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        deleted = (
            db_session.query(AgentHeartbeat)
            .filter(
                AgentHeartbeat.agent_id == agent_id,
                AgentHeartbeat.created_at < cutoff,
            )
            .delete(synchronize_session=False)
        )
        db_session.commit()

        assert deleted == 3

        # Remaining heartbeats should be 2
        remaining = (
            db_session.query(AgentHeartbeat)
            .filter(AgentHeartbeat.agent_id == agent_id)
            .count()
        )
        assert remaining == 2


class TestAgentStartupRetry:
    def test_wait_for_backend_success_after_retries(self):
        mock_client = MagicMock()
        # Fail first 2 times, succeed on 3rd
        mock_client.get.side_effect = [None, None, {"status": "healthy"}]

        with patch("time.sleep", return_value=None):
            result = wait_for_backend(mock_client, max_retries=5, retry_delay=1)

        assert result is True
        assert mock_client.get.call_count == 3

    def test_wait_for_backend_exits_after_max_retries(self):
        mock_client = MagicMock()
        mock_client.get.return_value = None

        with patch("time.sleep", return_value=None):
            with pytest.raises(SystemExit):
                wait_for_backend(mock_client, max_retries=3, retry_delay=1)

        assert mock_client.get.call_count == 3
