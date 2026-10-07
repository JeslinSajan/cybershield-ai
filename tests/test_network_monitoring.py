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
