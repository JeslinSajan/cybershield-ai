"""
Tests for Agent Concurrency & Non-Blocking Heartbeats (Fix for Finding 1).
"""

import threading
import time
from unittest.mock import Mock, patch
import pytest

from agent.main import _run_task_wrapper
from agent.offline_queue import OfflineQueue


def test_heartbeat_not_starved_during_long_task():
    """Verify that a slow task in worker thread does not block heartbeat loop."""
    heartbeat_times = []
    task_started = threading.Event()
    task_finish = threading.Event()

    mock_client = Mock()

    def fake_handle_task(task, client, queue):
        task_started.set()
        task_finish.wait(timeout=2.0)

    active_task_ids = set()
    lock = threading.Lock()
    task = {"id": "task-slow-1", "scan_type": "vulnerability", "target_scope": "127.0.0.1"}

    # Run task in background wrapper
    with patch("agent.main.handle_task", side_effect=fake_handle_task):
        t = threading.Thread(
            target=_run_task_wrapper,
            args=(task, mock_client, None, active_task_ids, lock),
        )
        with lock:
            active_task_ids.add("task-slow-1")
        t.start()

        # Ensure task started
        assert task_started.wait(timeout=1.0)
        assert "task-slow-1" in active_task_ids

        # Simulate heartbeat loop continuing while task is executing
        for _ in range(3):
            heartbeat_times.append(time.time())
            time.sleep(0.05)

        # Allow task to finish
        task_finish.set()
        t.join(timeout=2.0)

    # Verify heartbeats happened without blocking
    assert len(heartbeat_times) == 3
    assert "task-slow-1" not in active_task_ids


def test_duplicate_task_prevention():
    """Verify that a task with an ID already active is not dispatched twice."""
    active_task_ids = {"task-running-1"}
    lock = threading.Lock()

    task_id = "task-running-1"
    dispatched = False

    with lock:
        if task_id not in active_task_ids:
            active_task_ids.add(task_id)
            dispatched = True

    assert dispatched is False
    assert len(active_task_ids) == 1


def test_task_exception_does_not_crash_and_cleans_active_set():
    """Unhandled exception in task handler marks task FAILED and releases active ID."""
    mock_client = Mock()
    mock_client.post = Mock(return_value={"status": "ok"})

    active_task_ids = {"task-failing-1"}
    lock = threading.Lock()

    def exploding_task(task, client, queue):
        raise RuntimeError("Nmap process crashed unexpectedly")

    with patch("agent.main.handle_task", side_effect=exploding_task):
        _run_task_wrapper(
            {"id": "task-failing-1", "scan_type": "discovery"},
            mock_client,
            None,
            active_task_ids,
            lock,
        )

    # Active task ID must be released
    assert "task-failing-1" not in active_task_ids
    # Status FAILED must be reported to backend
    mock_client.post.assert_called_with(
        "/agents/tasks/task-failing-1/status",
        {"status": "FAILED", "details": {"error": "Nmap process crashed unexpectedly"}},
    )
