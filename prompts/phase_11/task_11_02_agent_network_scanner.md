# Task: 11.2 — Agent Network Scanner Module

## Objective
Implement `agent/collectors/network_scanner.py` to discover hosts on a target network scope, and connect the scanner to `agent/task_poller.py` for `scan_type == "discovery"`.

## Context
- Phase: 11 — Device Discovery
- Master Plan: prompts/phase_11/master.md
- Progress Tracker: prompts/phase_11/progress.md
- Standards: prompts/00_shared_standards.md

## Files to Inspect First
- `agent/task_poller.py`
- `agent/heartbeat.py`
- `agent/config.py`

## What to Implement
1. Create `agent/collectors/network_scanner.py`:
   - Function `discover_devices(target_scope: str) -> dict`.
   - Returns structured dictionary:
     ```python
     {
         "target_network": target_scope,
         "hosts": [
             {
                 "ip_address": "...",
                 "mac_address": "...",
                 "hostname": "...",
                 "vendor": "...",
                 "status": "online"
             }
         ]
     }
     ```
   - Resilient discovery strategy:
     - Check if `nmap` is available on the system.
     - If `nmap` is present, run ping sweep `nmap -sn <target_scope>`.
     - If `nmap` is not present, use standard ARP / socket ping fallback (e.g. read local ARP table / socket connects) so the agent does not crash.
2. In `agent/task_poller.py`:
   - Add handler for `scan_type == "discovery"`:
     - Mark task `RUNNING` via `POST /agents/tasks/{task_id}/status`.
     - Call `discover_devices(task.get("target_scope", "local"))`.
     - Post result via `POST /agents/results` with `result_type="discovery"`, `raw_payload=result`, `device_id=None`.
     - If upload fails, enqueue into `offline_queue` if provided.
     - If upload succeeds, mark task `COMPLETED` via `POST /agents/tasks/{task_id}/status`.

## What NOT to Implement
- Do NOT implement vulnerability detection or port scanning beyond host discovery in this task.
- Do NOT implement database parsing of discovery results in this task (handled in Task 11.3).
- Do NOT modify `backend/app/api/v1/devices.py`.

## Constraints
- Do not crash if `nmap` is not installed on the host. Log a clear warning.
- Keep dependencies pinned if adding any library.

## Testing
Test the network scanner directly via unit test or test script:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/test_agents.py tests/test_scans.py -v --tb=short
```

## Completion Criteria
- [ ] `agent/collectors/network_scanner.py` implemented.
- [ ] `agent/task_poller.py` executes discovery tasks.
- [ ] Graceful fallback operates when `nmap` binary is absent.
- [ ] Tests pass without regression.
- [ ] `prompts/phase_11/progress.md` updated.

## Progress Update
Update `prompts/phase_11/progress.md` with:
- Task 11.2 status set to `Completed`.
- Files changed.
- Test outcome.
- Next task set to `11.3`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start the next task.
Do not execute more commands.
Output a short summary and wait for user instruction.
