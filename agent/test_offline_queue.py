"""
Test suite for Phase 10.4 — Agent Offline Result Queue.

Tests verify queue persistence, idempotency, and retry behavior.
Run with: python test_offline_queue.py
"""

import json
import os
import sys
import tempfile
import uuid
from unittest.mock import Mock

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from offline_queue import OfflineQueue, MAX_QUEUE_SIZE


def test_enqueue_and_size():
    """Basic enqueue operation and size tracking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        queue = OfflineQueue(queue_dir=tmpdir)
        assert len(queue) == 0
        assert queue.is_empty
        
        item = {"method": "post", "path": "/test", "data": {"upload_id": str(uuid.uuid4())}}
        queue.enqueue(item)
        assert len(queue) == 1
        assert not queue.is_empty
    print("✓ test_enqueue_and_size passed")


def test_duplicate_upload_id_not_queued():
    """Duplicate upload_id should not be queued twice."""
    with tempfile.TemporaryDirectory() as tmpdir:
        queue = OfflineQueue(queue_dir=tmpdir)
        upload_id = str(uuid.uuid4())
        
        item1 = {"method": "post", "path": "/test", "data": {"upload_id": upload_id}}
        item2 = {"method": "post", "path": "/test", "data": {"upload_id": upload_id}}
        
        result1 = queue.enqueue(item1)
        result2 = queue.enqueue(item2)
        
        assert result1 is True
        assert result2 is False
        assert len(queue) == 1
    print("✓ test_duplicate_upload_id_not_queued passed")


def test_queue_persists_to_disk():
    """Queue should persist to disk on enqueue."""
    with tempfile.TemporaryDirectory() as tmpdir:
        queue_file = os.path.join(tmpdir, "offline_queue.json")
        queue = OfflineQueue(queue_dir=tmpdir)
        
        upload_id = str(uuid.uuid4())
        item = {"method": "post", "path": "/test", "data": {"upload_id": upload_id}}
        queue.enqueue(item)
        
        assert os.path.exists(queue_file)
        
        with open(queue_file, 'r') as f:
            data = json.load(f)
            assert len(data["queue"]) == 1
            assert upload_id in data["upload_ids"]
    print("✓ test_queue_persists_to_disk passed")


def test_queue_survives_restart():
    """Queue should load from disk on initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        upload_id = str(uuid.uuid4())
        item = {"method": "post", "path": "/test", "data": {"upload_id": upload_id}}
        
        # First queue instance
        queue1 = OfflineQueue(queue_dir=tmpdir)
        queue1.enqueue(item)
        assert len(queue1) == 1
        
        # Second queue instance (simulates restart)
        queue2 = OfflineQueue(queue_dir=tmpdir)
        assert len(queue2) == 1
        assert upload_id in queue2._upload_ids
    print("✓ test_queue_survives_restart passed")


def test_successful_drain_removes_item():
    """Successful drain should remove item from queue."""
    with tempfile.TemporaryDirectory() as tmpdir:
        queue = OfflineQueue(queue_dir=tmpdir)
        upload_id = str(uuid.uuid4())
        item = {"method": "post", "path": "/test", "data": {"upload_id": upload_id}}
        queue.enqueue(item)
        
        # Mock API client that returns success
        mock_client = Mock()
        mock_client.post = Mock(return_value={"id": "result-123"})
        
        drained = queue.drain(mock_client)
        
        assert drained == 1
        assert len(queue) == 0
        assert upload_id not in queue._upload_ids
    print("✓ test_successful_drain_removes_item passed")


def test_failed_drain_keeps_item():
    """Failed drain should keep item in queue."""
    with tempfile.TemporaryDirectory() as tmpdir:
        queue = OfflineQueue(queue_dir=tmpdir)
        upload_id = str(uuid.uuid4())
        item = {"method": "post", "path": "/test", "data": {"upload_id": upload_id}}
        queue.enqueue(item)
        
        # Mock API client that returns None (failure)
        mock_client = Mock()
        mock_client.post = Mock(return_value=None)
        
        drained = queue.drain(mock_client)
        
        assert drained == 0
        assert len(queue) == 1
        assert upload_id in queue._upload_ids
    print("✓ test_failed_drain_keeps_item passed")


def test_drain_stops_on_first_failure():
    """Drain should stop on first failure and keep remaining items."""
    with tempfile.TemporaryDirectory() as tmpdir:
        queue = OfflineQueue(queue_dir=tmpdir)
        upload_id1 = str(uuid.uuid4())
        upload_id2 = str(uuid.uuid4())
        
        item1 = {"method": "post", "path": "/test", "data": {"upload_id": upload_id1}}
        item2 = {"method": "post", "path": "/test", "data": {"upload_id": upload_id2}}
        queue.enqueue(item1)
        queue.enqueue(item2)
        
        # Mock API client that fails on first call
        mock_client = Mock()
        mock_client.post = Mock(return_value=None)
        
        drained = queue.drain(mock_client)
        
        assert drained == 0
        assert len(queue) == 2
    print("✓ test_drain_stops_on_first_failure passed")


def test_queue_max_size_drops_oldest():
    """Queue should drop oldest item when full."""
    # Temporarily modify MAX_QUEUE_SIZE
    import offline_queue
    original_max = offline_queue.MAX_QUEUE_SIZE
    offline_queue.MAX_QUEUE_SIZE = 3
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = OfflineQueue(queue_dir=tmpdir)
            
            upload_id1 = str(uuid.uuid4())
            upload_id2 = str(uuid.uuid4())
            upload_id3 = str(uuid.uuid4())
            upload_id4 = str(uuid.uuid4())
            
            queue.enqueue({"method": "post", "path": "/test", "data": {"upload_id": upload_id1}})
            queue.enqueue({"method": "post", "path": "/test", "data": {"upload_id": upload_id2}})
            queue.enqueue({"method": "post", "path": "/test", "data": {"upload_id": upload_id3}})
            assert len(queue) == 3
            
            # Adding 4th item should drop the first
            queue.enqueue({"method": "post", "path": "/test", "data": {"upload_id": upload_id4}})
            assert len(queue) == 3
            assert upload_id1 not in queue._upload_ids
            assert upload_id4 in queue._upload_ids
    finally:
        # Restore original MAX_QUEUE_SIZE
        offline_queue.MAX_QUEUE_SIZE = original_max
    print("✓ test_queue_max_size_drops_oldest passed")


def test_empty_queue_file_creates_empty_queue():
    """Missing queue file should create empty queue."""
    with tempfile.TemporaryDirectory() as tmpdir:
        queue = OfflineQueue(queue_dir=tmpdir)
        assert len(queue) == 0
        assert queue.is_empty
    print("✓ test_empty_queue_file_creates_empty_queue passed")


def test_corrupted_queue_file_creates_empty_queue():
    """Corrupted queue file should create empty queue."""
    with tempfile.TemporaryDirectory() as tmpdir:
        queue_file = os.path.join(tmpdir, "offline_queue.json")
        with open(queue_file, 'w') as f:
            f.write("invalid json")
        
        queue = OfflineQueue(queue_dir=tmpdir)
        assert len(queue) == 0
        assert queue.is_empty
    print("✓ test_corrupted_queue_file_creates_empty_queue passed")


if __name__ == "__main__":
    print("Running offline queue tests...")
    test_enqueue_and_size()
    test_duplicate_upload_id_not_queued()
    test_queue_persists_to_disk()
    test_queue_survives_restart()
    test_successful_drain_removes_item()
    test_failed_drain_keeps_item()
    test_drain_stops_on_first_failure()
    test_queue_max_size_drops_oldest()
    test_empty_queue_file_creates_empty_queue()
    test_corrupted_queue_file_creates_empty_queue()
    print("\n✓ All tests passed!")
