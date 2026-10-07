"""
Network scanner collector for CyberShield Agent (Phase 11).

Discovers devices on the local network using Nmap if available,
or falls back to ARP table and interface inspection when Nmap is absent.
"""

import logging
import re
import shutil
import socket
import subprocess
from typing import Dict, List, Optional

import psutil

logger = logging.getLogger("agent.network_scanner")


def _is_valid_unicast_ip(ip: str) -> bool:
    """Filter out multicast, loopback, and broadcast IPv4 addresses."""
    if not ip or not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
        return False
    octets = [int(p) for p in ip.split(".")]
    if any(o < 0 or o > 255 for o in octets):
        return False
    # Filter 127.x.x.x (loopback), 0.x.x.x, 224-239.x.x.x (multicast), 255.255.255.255 (broadcast)
    if octets[0] == 127 or octets[0] == 0 or 224 <= octets[0] <= 239 or octets[0] == 255:
        return False
    if octets[3] == 255:  # subnet broadcast
        return False
    return True


def _format_mac(mac: Optional[str]) -> Optional[str]:
    """Normalize MAC address to colon-separated uppercase."""
    if not mac:
        return None
    cleaned = re.sub(r"[^0-9a-fA-F]", "", mac)
    if len(cleaned) == 12:
        return ":".join(cleaned[i:i+2].upper() for i in range(0, 12, 2))
    return mac.replace("-", ":").upper()


def _resolve_hostname(ip: str) -> Optional[str]:
    """Attempt reverse DNS lookup with a short timeout."""
    try:
        orig_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(0.5)
        try:
            name, _, _ = socket.gethostbyaddr(ip)
            return name
        finally:
            socket.setdefaulttimeout(orig_timeout)
    except Exception:
        return None


def _scan_with_nmap(target_network: str) -> Optional[List[dict]]:
    """Scan using Nmap if python-nmap and nmap binary are available."""
    if not shutil.which("nmap"):
        return None

    try:
        import nmap
        nm = nmap.PortScanner()
        args = "-sn"
        target = target_network if target_network and target_network != "local" else "127.0.0.1"
        nm.scan(hosts=target, arguments=args)
        hosts = []
        for host in nm.all_hosts():
            if not _is_valid_unicast_ip(host):
                continue
            mac = nm[host]["addresses"].get("mac")
            vendor = list(nm[host]["vendor"].values())[0] if nm[host].get("vendor") else None
            hosts.append({
                "ip_address": host,
                "mac_address": _format_mac(mac),
                "hostname": nm[host].hostname() or None,
                "vendor": vendor,
                "status": "online" if nm[host].state() == "up" else "unknown"
            })
        return hosts
    except Exception as e:
        logger.warning(f"Nmap scan failed ({e}), falling back to ARP discovery")
        return None


def _scan_with_arp() -> List[dict]:
    """Fallback scanner reading the system ARP table and local interfaces."""
    discovered: Dict[str, dict] = {}

    # 1. Add local host interfaces
    try:
        local_hostname = socket.gethostname()
        for iface_name, addrs in psutil.net_if_addrs().items():
            mac = None
            for addr in addrs:
                if addr.family == psutil.AF_LINK or str(addr.family) in ("-1", "AF_LINK"):
                    mac = _format_mac(addr.address)
            for addr in addrs:
                if addr.family == socket.AF_INET and _is_valid_unicast_ip(addr.address):
                    discovered[addr.address] = {
                        "ip_address": addr.address,
                        "mac_address": mac,
                        "hostname": local_hostname,
                        "vendor": None,
                        "status": "online"
                    }
    except Exception as e:
        logger.debug(f"Failed reading local interfaces: {e}")

    # 2. Parse ARP cache via 'arp -a'
    try:
        res = subprocess.run(["arp", "-a"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        output = res.stdout if hasattr(res, "stdout") else ""
        # Match lines like: 192.168.1.1  00-11-22-33-44-55  dynamic
        pattern = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fA-F-]{17})\s+(\w+)")
        for match in pattern.finditer(output):
            ip, mac_raw, entry_type = match.groups()
            if _is_valid_unicast_ip(ip) and entry_type.lower() != "invalid":
                if ip not in discovered:
                    discovered[ip] = {
                        "ip_address": ip,
                        "mac_address": _format_mac(mac_raw),
                        "hostname": None,
                        "vendor": None,
                        "status": "online"
                    }
    except Exception as e:
        logger.warning(f"ARP cache inspection failed: {e}")

    # 3. Resolve hostnames where missing
    for host in discovered.values():
        if not host.get("hostname"):
            host["hostname"] = _resolve_hostname(host["ip_address"])

    return list(discovered.values())


def discover_devices(target_network: str = "local") -> dict:
    """
    Main discovery entry point.
    Discovers devices on the target scope and returns a structured dictionary.
    """
    logger.info(f"Starting device discovery for scope: {target_network}")
    hosts = _scan_with_nmap(target_network)
    if hosts is None:
        hosts = _scan_with_arp()

    logger.info(f"Device discovery complete: {len(hosts)} hosts found")
    return {
        "target_network": target_network,
        "hosts": hosts
    }
