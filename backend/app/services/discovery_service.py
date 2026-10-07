"""
Discovery processing service for CyberShield AI (Phase 11).

Processes discovery payloads from agents, upserting discovered hosts
into the devices table under the agent's organization.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.device import Device
from app.models.scan import ScanResult

logger = logging.getLogger("app.services.discovery")


def process_discovery_result(db: Session, scan_result: ScanResult, agent: Agent) -> int:
    """
    Parse discovery scan results and upsert Device records.
    
    Uniqueness is enforced on (organization_id, ip_address).
    Existing devices have their last_seen_at, status, hostname, mac, and vendor updated.
    New devices are inserted.
    """
    payload = scan_result.raw_payload or {}
    hosts = payload.get("hosts", [])
    if not isinstance(hosts, list):
        logger.warning(f"Invalid discovery payload format for scan_result {scan_result.id}")
        return 0

    now = datetime.now(timezone.utc)
    processed_count = 0

    for host in hosts:
        if not isinstance(host, dict):
            continue

        ip = host.get("ip_address")
        if not ip:
            continue

        # Look up existing active device in the same organization
        existing = db.query(Device).filter(
            Device.organization_id == agent.organization_id,
            Device.ip_address == str(ip),
            Device.deleted_at.is_(None)
        ).first()

        if existing:
            existing.last_seen_at = now
            existing.status = host.get("status", "online")
            if host.get("hostname"):
                existing.hostname = host["hostname"]
            if host.get("mac_address"):
                existing.mac_address = host["mac_address"]
            if host.get("vendor"):
                existing.vendor = host["vendor"]
            existing.agent_id = agent.id
        else:
            new_device = Device(
                organization_id=agent.organization_id,
                agent_id=agent.id,
                ip_address=str(ip),
                mac_address=host.get("mac_address"),
                hostname=host.get("hostname"),
                vendor=host.get("vendor"),
                device_type=host.get("device_type", "workstation"),
                status=host.get("status", "online"),
                last_seen_at=now,
            )
            db.add(new_device)

        processed_count += 1

    logger.info(
        f"Processed {processed_count} discovered devices for org {agent.organization_id} from agent {agent.id}"
    )
    return processed_count
