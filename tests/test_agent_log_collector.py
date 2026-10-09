"""
Unit tests for agent/collectors/log_collector.py (Phase 14.3).
Tests Linux auth.log parsing, Windows fallback handling, state tracking, and log transmission.
"""

import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from agent.collectors.log_collector import (
    parse_auth_log_line,
    collect_linux_logs,
    collect_windows_logs,
    collect_logs,
    load_last_sent_timestamp,
    save_last_sent_timestamp,
    collect_and_send_logs,
)


class TestLogLineParsing:
    def test_parse_failed_password_syslog(self):
        line = "Oct  9 20:15:32 myhost sshd[1234]: Failed password for invalid user admin from 192.168.1.100 port 54321 ssh2"
        res = parse_auth_log_line(line, default_year=2026)
        assert res is not None
        assert res["source"] == "auth.log"
        assert res["event_type"] == "login_failure"
        assert res["severity"] == "medium"
        assert res["username"] == "admin"
        assert res["source_ip"] == "192.168.1.100"
        assert "2026-10-09T20:15:32" in res["timestamp"]

    def test_parse_failed_password_valid_user(self):
        line = "Oct  9 20:15:32 myhost sshd[1234]: Failed password for root from 10.0.0.5 port 22 ssh2"
        res = parse_auth_log_line(line, default_year=2026)
        assert res is not None
        assert res["event_type"] == "login_failure"
        assert res["username"] == "root"
        assert res["source_ip"] == "10.0.0.5"

    def test_parse_accepted_password_iso(self):
        line = "2026-10-09T20:15:32+00:00 myhost sshd[1234]: Accepted password for ubuntu from 192.168.1.50 port 54321 ssh2"
        res = parse_auth_log_line(line)
        assert res is not None
        assert res["source"] == "auth.log"
        assert res["event_type"] == "login_success"
        assert res["severity"] == "low"
        assert res["username"] == "ubuntu"
        assert res["source_ip"] == "192.168.1.50"
        assert "2026-10-09T20:15:32" in res["timestamp"]

    def test_parse_accepted_publickey(self):
        line = "Oct  9 20:15:32 myhost sshd[1234]: Accepted publickey for deployer from 172.16.0.4 port 22 ssh2"
        res = parse_auth_log_line(line, default_year=2026)
        assert res is not None
        assert res["event_type"] == "login_success"
        assert res["severity"] == "low"
        assert res["username"] == "deployer"
        assert res["source_ip"] == "172.16.0.4"

    def test_unrelated_syslog_line_ignored(self):
        line = "Oct  9 20:15:32 myhost systemd[1]: Started Session 1 of user root."
        res = parse_auth_log_line(line, default_year=2026)
        assert res is None

    def test_line_older_than_since_timestamp_ignored(self):
        line = "Oct  9 20:15:32 myhost sshd[1234]: Failed password for root from 10.0.0.5 port 22 ssh2"
        cutoff = datetime(2026, 10, 9, 21, 0, 0, tzinfo=timezone.utc)
        res = parse_auth_log_line(line, since_timestamp=cutoff, default_year=2026)
        assert res is None


class TestWindowsFallback:
    def test_windows_fallback_when_pywin32_missing(self):
        with patch.dict(sys.modules, {"win32evtlog": None}):
            logs = collect_windows_logs()
            assert isinstance(logs, list)
            assert len(logs) == 0


class TestStateTracking:
    def test_state_file_persistence_and_loading(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            tmp_path = tf.name

        try:
            # File is empty/brand new
            assert load_last_sent_timestamp(tmp_path) is None

            test_ts = datetime(2026, 8, 24, 12, 30, 0, tzinfo=timezone.utc)
            save_last_sent_timestamp(test_ts, tmp_path)

            loaded = load_last_sent_timestamp(tmp_path)
            assert loaded is not None
            assert loaded == test_ts
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_deduplication_via_state(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as lf:
            lf.write("2026-10-09T10:00:00+00:00 host sshd[1]: Failed password for u1 from 1.1.1.1 port 22\n")
            lf.write("2026-10-09T11:00:00+00:00 host sshd[1]: Failed password for u2 from 1.1.1.2 port 22\n")
            lf.write("2026-10-09T12:00:00+00:00 host sshd[1]: Accepted password for u3 from 1.1.1.3 port 22\n")
            log_path = lf.name

        try:
            # First pass: no since_timestamp
            all_logs = collect_linux_logs(since_timestamp=None, log_file=log_path)
            assert len(all_logs) == 3

            # Second pass: since_timestamp at 11:00
            t_mid = datetime(2026, 10, 9, 11, 0, 0, tzinfo=timezone.utc)
            mid_logs = collect_linux_logs(since_timestamp=t_mid, log_file=log_path)
            assert len(mid_logs) == 1
            assert mid_logs[0]["username"] == "u3"

            # Third pass: since_timestamp at 12:00 -> none returned
            t_end = datetime(2026, 10, 9, 12, 0, 0, tzinfo=timezone.utc)
            end_logs = collect_linux_logs(since_timestamp=t_end, log_file=log_path)
            assert len(end_logs) == 0
        finally:
            if os.path.exists(log_path):
                os.remove(log_path)


class TestCollectAndSendLogs:
    def test_collect_and_send_success_and_deduplication(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as lf:
            lf.write("2026-10-09T10:00:00+00:00 host sshd[1]: Failed password for u1 from 1.1.1.1 port 22\n")
            lf.write("2026-10-09T11:00:00+00:00 host sshd[1]: Accepted password for u2 from 1.1.1.2 port 22\n")
            log_path = lf.name

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as sf:
            state_path = sf.name

        try:
            mock_client = MagicMock()
            mock_client.post.return_value = {"ingested_count": 2, "log_ids": ["id1", "id2"]}

            sent = collect_and_send_logs(
                mock_client,
                agent_id="test-agent",
                state_file=state_path,
                log_file_override=log_path,
            )
            assert sent == 2
            mock_client.post.assert_called_once()
            called_payload = mock_client.post.call_args[0][1]
            assert len(called_payload["logs"]) == 2

            # Verify state was saved to 11:00
            saved_ts = load_last_sent_timestamp(state_path)
            assert saved_ts == datetime(2026, 10, 9, 11, 0, 0, tzinfo=timezone.utc)

            # Second call: no new logs should be sent
            mock_client.reset_mock()
            sent2 = collect_and_send_logs(
                mock_client,
                agent_id="test-agent",
                state_file=state_path,
                log_file_override=log_path,
            )
            assert sent2 == 0
            mock_client.post.assert_not_called()

        finally:
            if os.path.exists(log_path):
                os.remove(log_path)
            if os.path.exists(state_path):
                os.remove(state_path)

    def test_collect_and_send_handles_backend_failure(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as lf:
            lf.write("2026-10-09T10:00:00+00:00 host sshd[1]: Failed password for u1 from 1.1.1.1 port 22\n")
            log_path = lf.name

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as sf:
            state_path = sf.name

        try:
            mock_client = MagicMock()
            mock_client.post.return_value = None  # Backend error/timeout

            sent = collect_and_send_logs(
                mock_client,
                agent_id="test-agent",
                state_file=state_path,
                log_file_override=log_path,
            )
            assert sent == 0

            # State timestamp must NOT be advanced when backend fails
            saved_ts = load_last_sent_timestamp(state_path)
            assert saved_ts is None
        finally:
            if os.path.exists(log_path):
                os.remove(log_path)
            if os.path.exists(state_path):
                os.remove(state_path)
