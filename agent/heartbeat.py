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

    # Collect network interface information
    interfaces = {}
    try:
        net_io = psutil.net_io_counters(pernic=True)
        net_addrs = psutil.net_if_addrs()
        for iface_name, addrs in net_addrs.items():
            iface_data = {
                "name": iface_name,
                "status": "up" if iface_name in net_io else "unknown",
                "addresses": []
            }
            
            for addr in addrs:
                addr_info = {
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                }
                iface_data["addresses"].append(addr_info)
            
            # Add I/O stats if available
            if iface_name in net_io:
                io = net_io[iface_name]
                iface_data["bytes_sent"] = io.bytes_sent
                iface_data["bytes_recv"] = io.bytes_recv
                iface_data["packets_sent"] = io.packets_sent
                iface_data["packets_recv"] = io.packets_recv
            
            interfaces[iface_name] = iface_data
    except Exception as e:
        logger.warning(f"Failed to collect network metrics: {e}")

    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": psutil.virtual_memory().percent,
        "details": {
            "disk_usage_percent": disk,
            "interfaces": interfaces,
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
