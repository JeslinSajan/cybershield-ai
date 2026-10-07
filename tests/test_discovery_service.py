"""Tests for discovery result processing and device upsertion (Phase 11.3)."""

import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.models.agent import Agent, AgentCredential
from app.models.device import Device
from app.models.organization import Organization, Role
from app.models.scan import Scan, ScanResult
from app.core.security import create_access_token, hash_password
from app.core.seed import CANONICAL_ROLES
import secrets, hashlib

client = TestClient(app)


@pytest.fixture(scope="module")
def discovery_test_env(db_session):
    """Create test organization, admin, and agent."""
    org = Organization(name="DiscoveryTestOrg", slug="discovery-test-org")
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
        email="discoveryadmin@test.com",
        password_hash=hash_password("AdminPass123!"),
        username="discovery-admin",
        is_active=True,
    )
    db_session.add(admin)
    db_session.flush()

    agent = Agent(
        organization_id=org.id,
        name="discovery-agent",
        hostname="discovery-host",
        version="1.0.0",
        status="ONLINE",
        is_active=True,
    )
    db_session.add(agent)
    db_session.flush()

    raw_token = secrets.token_urlsafe(48)
    cred_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    from datetime import timedelta
    cred = AgentCredential(
        agent_id=agent.id,
        credential_hash=cred_hash,
        type="token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        is_active=True,
    )
    db_session.add(cred)
    db_session.commit()

    return {"org": org, "admin": admin, "agent": agent, "agent_token": raw_token}


from app.models.user import User


class TestDiscoveryProcessing:
    def test_discovery_result_creates_devices(self, discovery_test_env, db_session):
        agent = discovery_test_env["agent"]
        agent_token = discovery_test_env["agent_token"]
        admin = discovery_test_env["admin"]

        # 1. Create a discovery scan
        scan = Scan(
            organization_id=agent.organization_id,
            agent_id=agent.id,
            created_by_user_id=admin.id,
            scan_type="discovery",
            status="RUNNING",
            target_scope="192.168.1.0/24",
        )
        db_session.add(scan)
        db_session.commit()

        # 2. Upload discovery results via Agent API
        hosts_payload = [
            {
                "ip_address": "192.168.1.1",
                "mac_address": "00:11:22:33:44:01",
                "hostname": "router.local",
                "vendor": "Netgear",
                "status": "online",
            },
            {
                "ip_address": "192.168.1.100",
                "mac_address": "00:11:22:33:44:02",
                "hostname": "workstation-1",
                "vendor": "Dell",
                "status": "online",
            },
        ]

        resp = client.post(
            "/api/v1/agents/results",
            json={
                "scan_id": str(scan.id),
                "device_id": None,
                "upload_id": str(uuid.uuid4()),
                "result_type": "discovery",
                "raw_payload": {"target_network": "192.168.1.0/24", "hosts": hosts_payload},
            },
            headers={"Authorization": f"Bearer {agent_token}"},
        )
        assert resp.status_code == 201

        # 3. Verify devices exist in DB
        dev1 = db_session.query(Device).filter(
            Device.organization_id == agent.organization_id,
            Device.ip_address == "192.168.1.1",
        ).first()
        assert dev1 is not None
        assert dev1.hostname == "router.local"
        assert dev1.vendor == "Netgear"
        assert dev1.status == "online"

        dev2 = db_session.query(Device).filter(
            Device.organization_id == agent.organization_id,
            Device.ip_address == "192.168.1.100",
        ).first()
        assert dev2 is not None
        assert dev2.hostname == "workstation-1"

    def test_repeat_discovery_updates_existing_device(self, discovery_test_env, db_session):
        agent = discovery_test_env["agent"]
        agent_token = discovery_test_env["agent_token"]
        admin = discovery_test_env["admin"]

        scan = Scan(
            organization_id=agent.organization_id,
            agent_id=agent.id,
            created_by_user_id=admin.id,
            scan_type="discovery",
            status="RUNNING",
            target_scope="192.168.1.0/24",
        )
        db_session.add(scan)
        db_session.commit()

        initial_count = db_session.query(Device).filter(
            Device.organization_id == agent.organization_id
        ).count()

        # Update hostname of 192.168.1.100
        updated_hosts = [
            {
                "ip_address": "192.168.1.100",
                "mac_address": "00:11:22:33:44:02",
                "hostname": "workstation-renamed",
                "vendor": "Dell Inc",
                "status": "online",
            }
        ]

        resp = client.post(
            "/api/v1/agents/results",
            json={
                "scan_id": str(scan.id),
                "device_id": None,
                "upload_id": str(uuid.uuid4()),
                "result_type": "discovery",
                "raw_payload": {"hosts": updated_hosts},
            },
            headers={"Authorization": f"Bearer {agent_token}"},
        )
        assert resp.status_code == 201

        new_count = db_session.query(Device).filter(
            Device.organization_id == agent.organization_id
        ).count()
        assert new_count == initial_count  # No duplicate created

        dev = db_session.query(Device).filter(
            Device.organization_id == agent.organization_id,
            Device.ip_address == "192.168.1.100",
        ).first()
        assert dev.hostname == "workstation-renamed"
        assert dev.vendor == "Dell Inc"
