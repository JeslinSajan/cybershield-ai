"""Unit tests for agent network scanner (Phase 11.2)."""

import pytest
from unittest.mock import MagicMock, patch

from agent.collectors.network_scanner import (
    _format_mac,
    _is_valid_unicast_ip,
    discover_devices,
)
from agent.task_poller import handle_task


class TestNetworkScannerUnit:
    def test_ip_filtering(self):
        assert _is_valid_unicast_ip("192.168.1.1") is True
        assert _is_valid_unicast_ip("10.0.0.1") is True
        # Reject invalid
        assert _is_valid_unicast_ip("127.0.0.1") is False
        assert _is_valid_unicast_ip("224.0.0.1") is False
        assert _is_valid_unicast_ip("239.255.255.250") is False
        assert _is_valid_unicast_ip("255.255.255.255") is False
        assert _is_valid_unicast_ip("192.168.1.255") is False
        assert _is_valid_unicast_ip("invalid_ip") is False

    def test_mac_formatting(self):
        assert _format_mac("00-11-22-33-44-55") == "00:11:22:33:44:55"
        assert _format_mac("001122334455") == "00:11:22:33:44:55"
        assert _format_mac("aa:bb:cc:dd:ee:ff") == "AA:BB:CC:DD:EE:FF"
        assert _format_mac(None) is None

    def test_discover_devices_fallback_returns_hosts(self):
        result = discover_devices("local")
        assert "target_network" in result
        assert "hosts" in result
        assert isinstance(result["hosts"], list)
        assert len(result["hosts"]) >= 1

        first_host = result["hosts"][0]
        assert "ip_address" in first_host
        assert "status" in first_host
        assert first_host["status"] == "online"


class TestTaskPollerDiscovery:
    def test_discovery_task_dispatch(self):
        mock_client = MagicMock()
        mock_client.post.return_value = {"id": "res-123"}

        task = {
            "id": "task-uuid-1234",
            "scan_type": "discovery",
            "target_scope": "192.168.1.0/24",
        }

        with patch("agent.collectors.network_scanner.discover_devices") as mock_discover:
            mock_discover.return_value = {
                "target_network": "192.168.1.0/24",
                "hosts": [
                    {"ip_address": "192.168.1.10", "status": "online", "mac_address": "AA:BB:CC:DD:EE:FF"}
                ],
            }

            handle_task(task, mock_client)

            # Check status calls: RUNNING then COMPLETED
            calls = [call[0] for call in mock_client.post.call_args_list]
            assert calls[0][0] == "/agents/tasks/task-uuid-1234/status"
            assert calls[0][1] == {"status": "RUNNING"}

            # Check result upload
            assert calls[1][0] == "/agents/results"
            result_payload = calls[1][1]
            assert result_payload["result_type"] == "discovery"
            assert result_payload["scan_id"] == "task-uuid-1234"
            assert len(result_payload["raw_payload"]["hosts"]) == 1

            # Check completion
            assert calls[2][0] == "/agents/tasks/task-uuid-1234/status"
            assert calls[2][1] == {"status": "COMPLETED"}
