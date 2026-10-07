# Task: 12.1 — Agent Network Stats Collection

## Objective
Update `agent/heartbeat.py` to collect network interface metrics (traffic counters, status, speed, MAC and IP addresses) and active connection count using `psutil`, sending them within `details["network"]` in the heartbeat payload.

## Context
- Phase: 12 — Network Monitoring
- Master Plan: prompts/phase_12/master.md
- Progress Tracker: prompts/phase_12/progress.md
- Standards: prompts/00_shared_standards.md

## Files to Inspect First
- `agent/heartbeat.py`

## What to Implement
1. In `agent/heartbeat.py`:
   - Add `collect_network_stats() -> dict`:
     - Use `psutil.net_io_counters(pernic=True)` for `bytes_sent` and `bytes_received`.
     - Use `psutil.net_if_stats()` for `is_up` (via `.isup`) and `speed_mbps` (via `.speed`).
     - Use `psutil.net_if_addrs()` to extract MAC address (handling `AF_PACKET`, `AF_LINK`, or physical MAC format) and IPv4 address.
     - Use `psutil.net_connections()` to count active connections. Catch `(psutil.AccessDenied, PermissionError)` and return `-1` if denied.
     - Return structure:
       ```python
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
       ```
   - Update `collect_metrics()`:
     - Place network statistics into `details["network"]`.
2. In `tests/test_network_monitoring.py`:
   - Add unit tests verifying `collect_network_stats()` output shape, interface keys, and exception tolerance.

## What NOT to Implement
- Do NOT modify backend routers or database models in this task.
- Do NOT implement database interface upsert yet (Task 12.2).
- Do NOT install new external dependencies (`psutil` is already pinned).

## Constraints
- Cross-platform support: Must run without crashing on both Windows and Linux hosts.
- Safe permissions: If reading connections requires elevated permissions, gracefully return `-1`.

## Testing
Run pytest:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/test_network_monitoring.py -v --tb=short
```

## Completion Criteria
- [ ] `collect_network_stats()` returns valid interface list and active connections count.
- [ ] Network stats embedded inside `details["network"]` in heartbeat payload.
- [ ] Unit tests pass in `tests/test_network_monitoring.py`.
- [ ] `prompts/phase_12/progress.md` updated.

## Progress Update
Update `prompts/phase_12/progress.md` with:
- Task 12.1 status set to `Completed`.
- Files changed.
- Test outcome.
- Next task set to `12.2`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Task 12.2.
Output a short summary and wait for user instruction.
