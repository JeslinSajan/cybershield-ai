import logging
from datetime import datetime, timezone
from typing import Optional
import uuid

import psutil

from agent.api_client import APIClient

logger = logging.getLogger("agent.heartbeat")


def collect_network_stats() -> dict:
    """Collect network interface stats and connection count using psutil.

    Returns:
        {
            "interfaces": [
                {
                    "name": "eth0",
                    "is_up": True,
                    "bytes_sent": 1024,
                    "bytes_received": 2048,
                    "speed_mbps": 1000,
                    "mac_address": "00:11:22:33:44:55",
                    "ip_address": "192.168.1.10"
                }
            ],
            "active_connections": 15
        }
    """
    counters = {}
    stats = {}
    addrs = {}

    try:
        counters = psutil.net_io_counters(pernic=True)
    except Exception as e:
        logger.warning(f"Failed to collect net_io_counters: {e}")

    try:
        stats = psutil.net_if_stats()
    except Exception as e:
        logger.warning(f"Failed to collect net_if_stats: {e}")

    try:
        addrs = psutil.net_if_addrs()
    except Exception as e:
        logger.warning(f"Failed to collect net_if_addrs: {e}")

    all_names = set(counters.keys()) | set(stats.keys()) | set(addrs.keys())
    interfaces = []

    for name in sorted(all_names):
        io = counters.get(name)
        st = stats.get(name)
        iface_addrs = addrs.get(name, [])

        is_up = getattr(st, "isup", False) if st else False
        speed = getattr(st, "speed", 0) if st else 0
        bytes_sent = io.bytes_sent if io else 0
        bytes_recv = io.bytes_recv if io else 0

        mac_address = None
        ip_address = None

        for addr in iface_addrs:
            fam_str = str(addr.family)
            fam_name = getattr(addr.family, "name", fam_str)

            if fam_name in ("AF_PACKET", "AF_LINK") or "AF_PACKET" in fam_str or "AF_LINK" in fam_str:
                if addr.address:
                    mac_address = addr.address.replace("-", ":").lower()
            elif fam_name == "AF_INET" or "AF_INET" in fam_str:
                if addr.address and not addr.address.startswith("127."):
                    ip_address = addr.address

            if not mac_address and addr.address:
                parts = addr.address.replace("-", ":").split(":")
                if len(parts) == 6 and all(len(p) == 2 for p in parts):
                    mac_address = addr.address.replace("-", ":").lower()

        interfaces.append({
            "name": name,
            "is_up": bool(is_up),
            "bytes_sent": int(bytes_sent),
            "bytes_received": int(bytes_recv),
            "speed_mbps": int(speed) if speed is not None else 0,
            "mac_address": mac_address,
            "ip_address": ip_address,
        })

    try:
        connections = len(psutil.net_connections())
    except (psutil.AccessDenied, PermissionError):
        connections = -1
    except Exception as e:
        logger.debug(f"Could not retrieve net_connections: {e}")
        connections = -1

    return {
        "interfaces": interfaces,
        "active_connections": connections,
    }


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
            "network": collect_network_stats(),
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
