import json
import logging
import os
import threading
from collections import deque
from typing import Optional, Set

logger = logging.getLogger("agent.offline_queue")
MAX_QUEUE_SIZE = 100
QUEUE_FILE = "offline_queue.json"


class OfflineQueue:
    """Thread-safe, disk-persisted bounded queue for offline resilience."""

    def __init__(self, queue_dir: str = ".", queue_file: Optional[str] = None):
        self._queue_dir = queue_dir
        self._queue_file = queue_file if queue_file else os.path.join(queue_dir, QUEUE_FILE)
        self._lock = threading.RLock()
        self._queue: deque = deque(maxlen=MAX_QUEUE_SIZE)
        self._upload_ids: Set[str] = set()
        self._load_from_disk()

    def _set_restrictive_permissions(self, filepath: str) -> None:
        """Apply 0600 permissions on Unix (no-op on Windows)."""
        try:
            os.chmod(filepath, 0o600)
        except (OSError, AttributeError):
            pass

    def _load_from_disk(self):
        """Load queue from disk on initialization."""
        with self._lock:
            if not os.path.exists(self._queue_file):
                logger.info("No existing queue file found. Starting with empty queue.")
                return

            if os.path.islink(self._queue_file):
                logger.error("Refusing to load queue from symbolic link.")
                return

            try:
                with open(self._queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._queue = deque(data.get("queue", []), maxlen=MAX_QUEUE_SIZE)
                    self._upload_ids = set(data.get("upload_ids", []))
                self._set_restrictive_permissions(self._queue_file)
                logger.info(f"Loaded {len(self._queue)} items from offline queue")
            except Exception as e:
                logger.error(f"Failed to load queue from disk: {e}. Starting with empty queue.")
                self._queue = deque(maxlen=MAX_QUEUE_SIZE)
                self._upload_ids = set()

    def _save_to_disk(self):
        """Persist queue to disk safely with restrictive permissions."""
        with self._lock:
            if os.path.islink(self._queue_file):
                logger.error("Refusing to write queue to symbolic link.")
                return

            try:
                data = {
                    "queue": list(self._queue),
                    "upload_ids": list(self._upload_ids)
                }
                # Open with restrictive permissions on creation
                flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW

                try:
                    fd = os.open(self._queue_file, flags, 0o600)
                    with open(fd, 'w', encoding='utf-8') as f:
                        json.dump(data, f)
                except OSError:
                    # Fallback for systems where os.open flags behave differently
                    with open(self._queue_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f)

                self._set_restrictive_permissions(self._queue_file)
            except Exception as e:
                logger.error(f"Failed to save queue to disk: {e}")

    def enqueue(self, item: dict) -> bool:
        """Enqueue an item. Returns True if enqueued, False if duplicate upload_id."""
        with self._lock:
            data = item.get("data", {})
            upload_id = data.get("upload_id") if isinstance(data, dict) else None

            # Prevent duplicate upload_ids
            if upload_id and upload_id in self._upload_ids:
                logger.warning(f"Duplicate upload_id {upload_id} - not queuing")
                return False

            if len(self._queue) >= MAX_QUEUE_SIZE:
                # Drop oldest item and its upload_id
                oldest = self._queue[0]
                oldest_data = oldest.get("data", {})
                oldest_upload_id = oldest_data.get("upload_id") if isinstance(oldest_data, dict) else None
                if oldest_upload_id and oldest_upload_id in self._upload_ids:
                    self._upload_ids.remove(oldest_upload_id)
                logger.warning("Offline queue full — dropping oldest item")

            self._queue.append(item)
            if upload_id:
                self._upload_ids.add(upload_id)

            self._save_to_disk()
            logger.info(f"Queued item (queue size: {len(self._queue)})")
            return True

    def drain(self, api_client) -> int:
        """Drain queued items when backend is reachable. Returns number of items drained."""
        with self._lock:
            drained = 0
            while self._queue:
                item = self._queue[0]  # Peek at first item
                method = item.get("method", "post")
                path = item.get("path")
                data = item.get("data")

                try:
                    result = getattr(api_client, method)(path, data) if data else api_client.get(path)
                    if result is not None:
                        # Success - remove from queue
                        self._queue.popleft()
                        upload_id = data.get("upload_id") if isinstance(data, dict) else None
                        if upload_id and upload_id in self._upload_ids:
                            self._upload_ids.remove(upload_id)
                        drained += 1
                        logger.info(f"Successfully drained queued item: {path}")
                    else:
                        # Failed - keep in queue and stop draining
                        logger.warning("Failed to drain queued item - will retry later")
                        break
                except Exception as e:
                    logger.error(f"Error draining queued item: {e}")
                    break

            if drained:
                self._save_to_disk()
                logger.info(f"Drained {drained} items from offline queue")

            return drained

    def __len__(self):
        with self._lock:
            return len(self._queue)

    @property
    def size(self):
        with self._lock:
            return len(self._queue)

    @property
    def is_empty(self):
        with self._lock:
            return len(self._queue) == 0

    def peek(self) -> list:
        """Return a copy of items currently in the queue without dequeuing."""
        with self._lock:
            return list(self._queue)
