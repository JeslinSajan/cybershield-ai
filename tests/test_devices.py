"""Tests for Device inventory endpoints (Phase 11.4)."""

import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.models.device import Device
from app.models.organization import Organization, Role
from app.models.user import User
from app.core.security import create_access_token, hash_password
from app.core.seed import CANONICAL_ROLES

client = TestClient(app)


@pytest.fixture(scope="module")
def device_test_setup(db_session):
    """Create two organizations with devices for multi-tenancy testing."""
    org1 = Organization(name="DeviceOrg1", slug="device-org-1")
    org2 = Organization(name="DeviceOrg2", slug="device-org-2")
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

    user_org1 = User(
        organization_id=org1.id,
        role_id=roles["Viewer"].id,
        email="viewer_org1@test.com",
        password_hash=hash_password("Pass123!"),
        username="viewer-org1",
        is_active=True,
    )
    user_org2 = User(
        organization_id=org2.id,
        role_id=roles["Administrator"].id,
        email="admin_org2@test.com",
        password_hash=hash_password("Pass123!"),
        username="admin-org2",
        is_active=True,
    )
    db_session.add_all([user_org1, user_org2])
    db_session.flush()

    # Create devices in org1
    dev1 = Device(
        organization_id=org1.id,
        ip_address="10.0.0.1",
        mac_address="00:11:22:33:44:01",
        hostname="gateway-1",
        vendor="Cisco",
        status="online",
        last_seen_at=datetime.now(timezone.utc),
    )
    dev2 = Device(
        organization_id=org1.id,
        ip_address="10.0.0.2",
        mac_address="00:11:22:33:44:02",
        hostname="server-1",
        vendor="Dell",
        status="offline",
        last_seen_at=datetime.now(timezone.utc),
    )

    # Create device in org2
    dev_org2 = Device(
        organization_id=org2.id,
        ip_address="192.168.1.1",
        mac_address="AA:BB:CC:DD:EE:FF",
        hostname="other-org-device",
        status="online",
        last_seen_at=datetime.now(timezone.utc),
    )

    db_session.add_all([dev1, dev2, dev_org2])
    db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "user_org1": user_org1,
        "user_org2": user_org2,
        "dev1": dev1,
        "dev2": dev2,
        "dev_org2": dev_org2,
    }


def _token(user):
    from conftest import _TestingSessionLocal
    db = _TestingSessionLocal()
    role = db.query(Role).filter(Role.id == user.role_id).first()
    db.close()
    return create_access_token(
        subject=str(user.id),
        role_name=role.name,
        organization_id=str(user.organization_id),
    )


class TestDeviceEndpoints:
    def test_list_devices(self, device_test_setup):
        token = _token(device_test_setup["user_org1"])
        resp = client.get("/api/v1/devices/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        ips = [d["ip_address"] for d in data]
        assert "10.0.0.1" in ips
        assert "10.0.0.2" in ips

    def test_filter_devices_by_status(self, device_test_setup):
        token = _token(device_test_setup["user_org1"])
        resp = client.get("/api/v1/devices/?status=offline", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["ip_address"] == "10.0.0.2"
        assert data[0]["status"] == "offline"

    def test_get_device_by_id(self, device_test_setup):
        token = _token(device_test_setup["user_org1"])
        dev_id = str(device_test_setup["dev1"].id)
        resp = client.get(f"/api/v1/devices/{dev_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == dev_id
        assert data["hostname"] == "gateway-1"
        assert data["vendor"] == "Cisco"

    def test_get_nonexistent_device_returns_404(self, device_test_setup):
        token = _token(device_test_setup["user_org1"])
        random_id = str(uuid.uuid4())
        resp = client.get(f"/api/v1/devices/{random_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_organization_isolation(self, device_test_setup):
        """User from Org 1 cannot see devices belonging to Org 2."""
        token_org1 = _token(device_test_setup["user_org1"])
        dev_org2_id = str(device_test_setup["dev_org2"].id)

        # Listing in Org 1 does not return Org 2's device
        list_resp = client.get("/api/v1/devices/", headers={"Authorization": f"Bearer {token_org1}"})
        org1_ips = [d["ip_address"] for d in list_resp.json()]
        assert "192.168.1.1" not in org1_ips

        # Direct GET of Org 2's device by Org 1 returns 404
        detail_resp = client.get(f"/api/v1/devices/{dev_org2_id}", headers={"Authorization": f"Bearer {token_org1}"})
        assert detail_resp.status_code == 404


class TestDeviceDiscoveryIntegration:
    def test_full_device_discovery_loop(self, device_test_setup, db_session):
        """End-to-end loop: Scan creation → Agent poll → Result upload → Device query."""
        import secrets, hashlib
        from app.models.agent import Agent, AgentCredential
        from app.models.scan import Scan

        org = device_test_setup["org1"]
        admin = device_test_setup["user_org2"]  # Admin user
        # Give admin access to org1 or use an admin in org1
        from app.models.organization import Role
        admin_role = db_session.query(Role).filter(Role.name == "Administrator").first()
        admin_org1 = User(
            organization_id=org.id,
            role_id=admin_role.id,
            email="admin_org1_loop@test.com",
            password_hash=hash_password("Pass123!"),
            username="admin-org1-loop",
            is_active=True,
        )
        db_session.add(admin_org1)
        db_session.flush()

        # Create Agent in org1
        agent = Agent(
            organization_id=org.id,
            name="loop-agent",
            hostname="loop-host",
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

        # Step 1: Admin creates discovery scan
        admin_token = _token(admin_org1)
        scan_resp = client.post(
            "/api/v1/scans/",
            json={
                "agent_id": str(agent.id),
                "scan_type": "discovery",
                "target_scope": "172.16.0.0/24",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert scan_resp.status_code == 201
        scan_id = scan_resp.json()["id"]

        # Step 2: Agent polls pending tasks
        poll_resp = client.get("/api/v1/agents/tasks", headers={"Authorization": f"Bearer {raw_token}"})
        assert poll_resp.status_code == 200
        tasks = poll_resp.json()
        assert any(t["id"] == scan_id for t in tasks)

        # Step 3: Agent uploads discovery results
        discovered_hosts = [
            {
                "ip_address": "172.16.0.10",
                "mac_address": "11:22:33:44:55:66",
                "hostname": "printer-e2e.local",
                "vendor": "HP",
                "status": "online",
            },
            {
                "ip_address": "172.16.0.20",
                "mac_address": "11:22:33:44:55:77",
                "hostname": "nas-e2e.local",
                "vendor": "Synology",
                "status": "online",
            },
        ]
        result_resp = client.post(
            "/api/v1/agents/results",
            json={
                "scan_id": scan_id,
                "device_id": None,
                "upload_id": str(uuid.uuid4()),
                "result_type": "discovery",
                "raw_payload": {"hosts": discovered_hosts},
            },
            headers={"Authorization": f"Bearer {raw_token}"},
        )
        assert result_resp.status_code == 201

        # Step 4: Verify scan is COMPLETED
        scan_detail = client.get(f"/api/v1/scans/{scan_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert scan_detail.status_code == 200
        assert scan_detail.json()["status"] == "COMPLETED"

        # Step 5: Viewer queries devices and sees the new devices
        viewer_token = _token(device_test_setup["user_org1"])
        devices_resp = client.get("/api/v1/devices/", headers={"Authorization": f"Bearer {viewer_token}"})
        assert devices_resp.status_code == 200
        discovered_ips = [d["ip_address"] for d in devices_resp.json()]
        assert "172.16.0.10" in discovered_ips
        assert "172.16.0.20" in discovered_ips

