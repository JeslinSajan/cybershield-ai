import logging
from datetime import datetime, timezone
from typing import Optional
import uuid

import psutil

from agent.api_client import APIClient

logger = logging.getLogger("agent.heartbeat")


def collect_metrics() -> dict:
    """Collect system metrics using psutil."""
    try:
        disk = psutil.disk_usage("/").percent
    except Exception:
        try:
            disk = psutil.disk_usage("C:\\").percent
        except Exception:
            disk = 0

    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": psutil.virtual_memory().percent,
        "details": {
            "disk_usage_percent": disk,
        },
    }


def send_heartbeat(api_client: APIClient, agent_id: str) -> bool:
    """Send a heartbeat to the backend. Returns True on success."""
    metrics = collect_metrics()
    payload = {
        "agent_id": agent_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "ONLINE",
        "version": "1.0.0",
        "cpu_percent": metrics["cpu_percent"],
        "memory_percent": metrics["memory_percent"],
        "details": metrics["details"],
    }

    result = api_client.post("/agents/heartbeat", payload)
    if result is not None:
        logger.info(f"Heartbeat sent — CPU: {metrics['cpu_percent']}%, RAM: {metrics['memory_percent']}%")
        return True
    else:
        logger.warning("Heartbeat failed — backend may be unreachable")
        return False
