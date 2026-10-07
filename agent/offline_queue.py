import json
import logging
import os
from collections import deque
from typing import Optional, Set

logger = logging.getLogger("agent.offline_queue")
MAX_QUEUE_SIZE = 100
QUEUE_FILE = "offline_queue.json"


class OfflineQueue:
    def __init__(self, queue_dir: str = "."):
        self._queue_dir = queue_dir
        self._queue_file = os.path.join(queue_dir, QUEUE_FILE)
        self._queue: deque = deque(maxlen=MAX_QUEUE_SIZE)
        self._upload_ids: Set[str] = set()
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Load queue from disk on initialization."""
        if not os.path.exists(self._queue_file):
            logger.info("No existing queue file found. Starting with empty queue.")
            return
        
        try:
            with open(self._queue_file, 'r') as f:
                data = json.load(f)
                self._queue = deque(data.get("queue", []), maxlen=MAX_QUEUE_SIZE)
                self._upload_ids = set(data.get("upload_ids", []))
            logger.info(f"Loaded {len(self._queue)} items from offline queue")
        except Exception as e:
            logger.error(f"Failed to load queue from disk: {e}. Starting with empty queue.")
            self._queue = deque(maxlen=MAX_QUEUE_SIZE)
            self._upload_ids = set()
    
    def _save_to_disk(self):
        """Persist queue to disk."""
        try:
            data = {
                "queue": list(self._queue),
                "upload_ids": list(self._upload_ids)
            }
            with open(self._queue_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save queue to disk: {e}")
    
    def enqueue(self, item: dict) -> bool:
        """Enqueue an item. Returns True if enqueued, False if duplicate upload_id."""
        upload_id = item.get("data", {}).get("upload_id")
        
        # Prevent duplicate upload_ids
        if upload_id and upload_id in self._upload_ids:
            logger.warning(f"Duplicate upload_id {upload_id} - not queuing")
            return False
        
        if len(self._queue) >= MAX_QUEUE_SIZE:
            # Drop oldest item and its upload_id
            oldest = self._queue[0]
            oldest_upload_id = oldest.get("data", {}).get("upload_id")
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
                    upload_id = data.get("upload_id") if data else None
                    if upload_id and upload_id in self._upload_ids:
                        self._upload_ids.remove(upload_id)
                    drained += 1
                    logger.info(f"Successfully drained queued item (upload_id: {upload_id})")
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
        return len(self._queue)
    
    @property
    def is_empty(self):
        return len(self._queue) == 0
