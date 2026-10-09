"""
Log collector module for CyberShield Agent.
Collects authentication and security events on Linux (/var/log/auth.log or /var/log/secure)
and Windows (Security Event Log via pywin32), normalizes them, and submits them to the backend.
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger("agent.log_collector")

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_log_state.json")

# Regex patterns for SSH authentication logs
FAILED_PASSWORD_RE = re.compile(
    r"Failed password for (?:invalid user )?(\S+) from (\S+) port \d+",
    re.IGNORECASE,
)
ACCEPTED_LOGIN_RE = re.compile(
    r"Accepted (?:password|publickey) for (\S+) from (\S+) port \d+",
    re.IGNORECASE,
)
SYSLOG_TS_RE = re.compile(r"^([A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})")
ISO_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)")


def parse_timestamp(timestamp_str: str, default_year: Optional[int] = None) -> Optional[datetime]:
    """Parse syslog or ISO-8601 timestamp string into a UTC datetime."""
    timestamp_str = timestamp_str.strip()
    try:
        dt = datetime.fromisoformat(timestamp_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass

    year = default_year or datetime.now(timezone.utc).year
    normalized = " ".join(timestamp_str.split())
    for fmt in ("%b %d %H:%M:%S", "%b %d %Y %H:%M:%S"):
        try:
            if "%Y" in fmt:
                dt = datetime.strptime(normalized, fmt)
            else:
                dt = datetime.strptime(f"{year} {normalized}", f"%Y {fmt}")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def parse_auth_log_line(
    line: str,
    since_timestamp: Optional[datetime] = None,
    default_year: Optional[int] = None,
) -> Optional[dict]:
    """Parse a single auth.log line into normalized dictionary if matching login event."""
    line = line.strip()
    if not line:
        return None

    # Extract timestamp
    parsed_dt: Optional[datetime] = None
    iso_match = ISO_TS_RE.match(line)
    if iso_match:
        parsed_dt = parse_timestamp(iso_match.group(1), default_year=default_year)
    else:
        syslog_match = SYSLOG_TS_RE.match(line)
        if syslog_match:
            parsed_dt = parse_timestamp(syslog_match.group(1), default_year=default_year)

    if parsed_dt is None:
        parsed_dt = datetime.now(timezone.utc)

    # Check if entry is older than since_timestamp
    if since_timestamp and parsed_dt <= since_timestamp:
        return None

    # Check for login failure
    fail_match = FAILED_PASSWORD_RE.search(line)
    if fail_match:
        username = fail_match.group(1)
        source_ip = fail_match.group(2)
        return {
            "source": "auth.log",
            "event_type": "login_failure",
            "severity": "medium",
            "message": line,
            "source_ip": source_ip,
            "username": username,
            "timestamp": parsed_dt.isoformat(),
        }

    # Check for login success
    success_match = ACCEPTED_LOGIN_RE.search(line)
    if success_match:
        username = success_match.group(1)
        source_ip = success_match.group(2)
        return {
            "source": "auth.log",
            "event_type": "login_success",
            "severity": "low",
            "message": line,
            "source_ip": source_ip,
            "username": username,
            "timestamp": parsed_dt.isoformat(),
        }

    return None


def load_last_sent_timestamp(state_file: Optional[str] = None) -> Optional[datetime]:
    """Load last sent log timestamp from state file."""
    target_file = state_file or STATE_FILE
    if not os.path.exists(target_file):
        return None
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            ts_str = data.get("last_sent_timestamp")
            if ts_str:
                dt = datetime.fromisoformat(ts_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
    except Exception as e:
        logger.warning(f"Failed to read log collector state from {target_file}: {e}")
    return None


def save_last_sent_timestamp(ts: datetime, state_file: Optional[str] = None) -> None:
    """Save last sent log timestamp to state file."""
    target_file = state_file or STATE_FILE
    try:
        data = {"last_sent_timestamp": ts.isoformat()}
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save log collector state to {target_file}: {e}")


def collect_linux_logs(
    since_timestamp: Optional[datetime] = None,
    log_file: Optional[str] = None,
    default_year: Optional[int] = None,
) -> List[dict]:
    """Read Linux authentication logs and return normalized entries."""
    paths_to_check = [log_file] if log_file else ["/var/log/auth.log", "/var/log/secure"]
    target_path = None
    for p in paths_to_check:
        if p and os.path.exists(p):
            target_path = p
            break

    if not target_path:
        return []

    collected = []
    try:
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                parsed = parse_auth_log_line(line, since_timestamp=since_timestamp, default_year=default_year)
                if parsed:
                    collected.append(parsed)
    except Exception as e:
        logger.warning(f"Could not read Linux log file {target_path}: {e}")

    return collected


def collect_windows_logs(since_timestamp: Optional[datetime] = None) -> List[dict]:
    """Collect Windows Security Event Logs (Event IDs 4624, 4625) using pywin32 if available."""
    try:
        import win32evtlog  # type: ignore
        import win32con  # type: ignore
    except ImportError:
        logger.warning("pywin32 not installed; Windows Event Log collection disabled.")
        return []

    server = "localhost"
    log_type = "Security"
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

    collected = []
    try:
        handle = win32evtlog.OpenEventLog(server, log_type)
        if not handle:
            return []

        events_batch = win32evtlog.ReadEventLog(handle, flags, 0)
        while events_batch:
            for event in events_batch:
                event_id = event.EventID & 0xFFFF
                time_generated = event.TimeGenerated.replace(tzinfo=timezone.utc)
                if since_timestamp and time_generated <= since_timestamp:
                    continue

                if event_id not in (4624, 4625):
                    continue

                event_type = "login_success" if event_id == 4624 else "login_failure"
                severity = "low" if event_id == 4624 else "medium"

                username = None
                source_ip = None
                if event.StringInserts and len(event.StringInserts) > 5:
                    username = event.StringInserts[5] if len(event.StringInserts) > 5 else None
                    if len(event.StringInserts) > 18:
                        source_ip = event.StringInserts[18]

                collected.append({
                    "source": "windows_security",
                    "event_type": event_type,
                    "severity": severity,
                    "message": f"Windows Security Logon Event ({event_id})",
                    "source_ip": source_ip,
                    "username": username,
                    "timestamp": time_generated.isoformat(),
                })

            events_batch = win32evtlog.ReadEventLog(handle, flags, 0)

        win32evtlog.CloseEventLog(handle)
    except Exception as e:
        logger.warning(f"Error reading Windows Event Log: {e}")

    return collected


def collect_logs(
    since_timestamp: Optional[datetime] = None,
    log_file_override: Optional[str] = None,
) -> List[dict]:
    """Collect logs according to platform or log_file_override."""
    if log_file_override:
        return collect_linux_logs(since_timestamp=since_timestamp, log_file=log_file_override)

    if sys.platform.startswith("win"):
        return collect_windows_logs(since_timestamp=since_timestamp)
    elif sys.platform.startswith("linux"):
        return collect_linux_logs(since_timestamp=since_timestamp)
    else:
        return []


def collect_and_send_logs(
    api_client,
    agent_id: Optional[str] = None,
    state_file: Optional[str] = None,
    log_file_override: Optional[str] = None,
) -> int:
    """Collect new security logs and transmit them to the backend."""
    last_ts = load_last_sent_timestamp(state_file)
    logs = collect_logs(since_timestamp=last_ts, log_file_override=log_file_override)
    if not logs:
        return 0

    payload = {"logs": logs}
    resp = api_client.post("/agents/logs", payload)
    if resp is not None:
        ingested = resp.get("ingested_count", len(logs))
        timestamps = [
            datetime.fromisoformat(l["timestamp"])
            for l in logs
            if l.get("timestamp")
        ]
        if timestamps:
            max_ts = max(timestamps)
            save_last_sent_timestamp(max_ts, state_file)
        return ingested

    return 0
