"""
Test suite for Phase 12 — Network Monitoring.
Tests agent network stats collection and backend interface upsert.
"""

from unittest.mock import MagicMock, patch
import pytest

from agent.heartbeat import collect_network_stats, collect_metrics


class TestAgentNetworkStatsUnit:
    def test_collect_network_stats_structure(self):
        """collect_network_stats returns a dict with interfaces list and active_connections int."""
        stats = collect_network_stats()
        assert isinstance(stats, dict)
        assert "interfaces" in stats
        assert "active_connections" in stats
        assert isinstance(stats["interfaces"], list)
        assert isinstance(stats["active_connections"], int)

    def test_collect_network_stats_interface_keys(self):
        """Interface entries contain required metadata and counter fields."""
        stats = collect_network_stats()
        for iface in stats["interfaces"]:
            assert "name" in iface
            assert isinstance(iface["name"], str)
            assert "is_up" in iface
            assert isinstance(iface["is_up"], bool)
            assert "bytes_sent" in iface
            assert isinstance(iface["bytes_sent"], int)
            assert iface["bytes_sent"] >= 0
            assert "bytes_received" in iface
            assert isinstance(iface["bytes_received"], int)
            assert iface["bytes_received"] >= 0
            assert "speed_mbps" in iface
            assert isinstance(iface["speed_mbps"], int)
            assert "mac_address" in iface
            assert "ip_address" in iface

    def test_collect_metrics_includes_network(self):
        """collect_metrics embeds network statistics inside details['network']."""
        metrics = collect_metrics()
        assert "details" in metrics
        assert "network" in metrics["details"]
        net = metrics["details"]["network"]
        assert "interfaces" in net
        assert "active_connections" in net

    def test_collect_network_stats_with_mocked_interfaces(self):
        """Test parsing of mocked network interfaces and MAC address normalisation."""
        mock_counters = {
            "eth0": MagicMock(bytes_sent=1024, bytes_recv=2048),
        }
        mock_stats = {
            "eth0": MagicMock(isup=True, speed=1000),
        }
        addr_ip = MagicMock()
        addr_ip.family = "AF_INET"
        addr_ip.address = "192.168.1.50"

        addr_mac = MagicMock()
        addr_mac.family = "AF_LINK"
        addr_mac.address = "00-11-22-33-44-55"

        mock_addrs = {
            "eth0": [addr_ip, addr_mac],
        }

        with patch("psutil.net_io_counters", return_value=mock_counters), \
             patch("psutil.net_if_stats", return_value=mock_stats), \
             patch("psutil.net_if_addrs", return_value=mock_addrs), \
             patch("psutil.net_connections", return_value=[1, 2, 3]):
            stats = collect_network_stats()

        assert stats["active_connections"] == 3
        assert len(stats["interfaces"]) == 1
        eth0 = stats["interfaces"][0]
        assert eth0["name"] == "eth0"
        assert eth0["is_up"] is True
        assert eth0["bytes_sent"] == 1024
        assert eth0["bytes_received"] == 2048
        assert eth0["speed_mbps"] == 1000
        assert eth0["mac_address"] == "00:11:22:33:44:55"
        assert eth0["ip_address"] == "192.168.1.50"

    def test_collect_network_stats_handles_permission_error(self):
        """Handles PermissionError when querying connections without elevated privileges."""
        with patch("psutil.net_connections", side_effect=PermissionError("Access denied")):
            stats = collect_network_stats()
            assert stats["active_connections"] == -1


import uuid
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.models.agent import Agent, AgentCredential, AgentHeartbeat
from app.models.device import Device, DeviceInterface
from app.models.organization import Organization

client = TestClient(app)


@pytest.fixture
def monitoring_setup(db_session):
    """Setup org, agent with credentials, and linked device."""
    uid = uuid.uuid4().hex[:8]
    org = Organization(name=f"MonitoringOrg-{uid}", slug=f"monitoring-org-{uid}")
    db_session.add(org)
    db_session.flush()

    agent = Agent(
        organization_id=org.id,
        name="net-agent",
        hostname="net-host",
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

    device = Device(
        organization_id=org.id,
        agent_id=agent.id,
        ip_address="192.168.1.10",
        mac_address="00:11:22:33:44:55",
        hostname="net-device",
        status="online",
    )
    db_session.add(device)
    db_session.commit()

    return {
        "org": org,
        "agent": agent,
        "token": raw_token,
        "device": device,
    }


class TestBackendDeviceInterfaceUpsert:
    def test_heartbeat_upserts_device_interfaces(self, monitoring_setup, db_session):
        """Heartbeat with network stats creates DeviceInterface records for linked device."""
        setup = monitoring_setup
        agent = setup["agent"]
        token = setup["token"]
        device = setup["device"]

        ts = datetime.now(timezone.utc).replace(microsecond=0)
        payload = {
            "agent_id": str(agent.id),
            "timestamp": ts.isoformat(),
            "status": "ONLINE",
            "version": "1.0.0",
            "cpu_percent": 15.0,
            "memory_percent": 30.0,
            "details": {
                "disk_usage_percent": 45,
                "network": {
                    "interfaces": [
                        {
                            "name": "eth0",
                            "is_up": True,
                            "bytes_sent": 50000,
                            "bytes_received": 100000,
                            "speed_mbps": 1000,
                            "mac_address": "00:11:22:33:44:55",
                            "ip_address": "192.168.1.10",
                        },
                        {
                            "name": "wlan0",
                            "is_up": True,
                            "bytes_sent": 20000,
                            "bytes_received": 40000,
                            "speed_mbps": 300,
                            "mac_address": "00:11:22:33:44:66",
                            "ip_address": "192.168.1.11",
                        },
                    ],
                    "active_connections": 10,
                },
            },
        }

        resp = client.post(
            "/api/v1/agents/heartbeat",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        # Verify device_interfaces rows in DB
        db_session.expire_all()
        ifaces = db_session.query(DeviceInterface).filter(
            DeviceInterface.device_id == device.id,
        ).order_by(DeviceInterface.name).all()

        assert len(ifaces) == 2
        eth0 = next(i for i in ifaces if i.name == "eth0")
        assert eth0.bytes_sent == 50000
        assert eth0.bytes_received == 100000
        assert eth0.mac_address == "00:11:22:33:44:55"
        assert str(eth0.ip_address) == "192.168.1.10"

        wlan0 = next(i for i in ifaces if i.name == "wlan0")
        assert wlan0.bytes_sent == 20000
        assert wlan0.bytes_received == 40000

    def test_repeat_heartbeat_updates_existing_interfaces(self, monitoring_setup, db_session):
        """Successive heartbeats update byte counters without creating duplicate interface rows."""
        setup = monitoring_setup
        agent = setup["agent"]
        token = setup["token"]
        device = setup["device"]

        ts1 = datetime.now(timezone.utc).replace(microsecond=0)
        payload1 = {
            "agent_id": str(agent.id),
            "timestamp": ts1.isoformat(),
            "status": "ONLINE",
            "details": {
                "network": {
                    "interfaces": [
                        {
                            "name": "eth0",
                            "bytes_sent": 1000,
                            "bytes_received": 2000,
                            "mac_address": "00:11:22:33:44:55",
                            "ip_address": "192.168.1.10",
                        }
                    ]
                }
            },
        }
        resp1 = client.post(
            "/api/v1/agents/heartbeat",
            json=payload1,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 200

        # Second heartbeat with higher byte counts and different timestamp
        ts2 = ts1 + timedelta(seconds=30)
        payload2 = {
            "agent_id": str(agent.id),
            "timestamp": ts2.isoformat(),
            "status": "ONLINE",
            "details": {
                "network": {
                    "interfaces": [
                        {
                            "name": "eth0",
                            "bytes_sent": 5000,
                            "bytes_received": 8000,
                            "mac_address": "00:11:22:33:44:55",
                            "ip_address": "192.168.1.10",
                        }
                    ]
                }
            },
        }
        resp2 = client.post(
            "/api/v1/agents/heartbeat",
            json=payload2,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 200

        db_session.expire_all()
        ifaces = db_session.query(DeviceInterface).filter(
            DeviceInterface.device_id == device.id,
        ).all()

        assert len(ifaces) == 1
        assert ifaces[0].bytes_sent == 5000
        assert ifaces[0].bytes_received == 8000

    def test_heartbeat_without_linked_device_succeeds_silently(self, db_session):
        """Heartbeat for an agent with no linked device still succeeds with 200 and skips interface creation."""
        uid = uuid.uuid4().hex[:8]
        org = Organization(name=f"NoDevOrg-{uid}", slug=f"no-dev-org-{uid}")
        db_session.add(org)
        db_session.flush()

        agent = Agent(
            organization_id=org.id,
            name="orphan-agent",
            hostname="orphan-host",
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

        ts = datetime.now(timezone.utc).replace(microsecond=0)
        payload = {
            "agent_id": str(agent.id),
            "timestamp": ts.isoformat(),
            "status": "ONLINE",
            "details": {
                "network": {
                    "interfaces": [
                        {"name": "eth0", "bytes_sent": 100, "bytes_received": 200}
                    ]
                }
            },
        }
        resp = client.post(
            "/api/v1/agents/heartbeat",
            json=payload,
            headers={"Authorization": f"Bearer {raw_token}"},
        )
        assert resp.status_code == 200

        db_session.expire_all()
        count = db_session.query(DeviceInterface).filter(
            DeviceInterface.organization_id == org.id,
        ).count()
        assert count == 0

