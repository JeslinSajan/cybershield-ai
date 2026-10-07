# Task: 11.3 — Discovery Result Processing Service

## Objective
Implement `process_discovery_result` in `backend/app/services/discovery_service.py` to parse discovery payloads and upsert `Device` rows, and connect it to `POST /agents/results` in `backend/app/api/v1/agents.py`.

## Context
- Phase: 11 — Device Discovery
- Master Plan: prompts/phase_11/master.md
- Progress Tracker: prompts/phase_11/progress.md
- Standards: prompts/00_shared_standards.md

## Files to Inspect First
- `backend/app/models/device.py`
- `backend/app/models/scan.py`
- `backend/app/api/v1/agents.py`

## What to Implement
1. Create `backend/app/services/discovery_service.py`:
   - Function `process_discovery_result(db: Session, scan_result: ScanResult, agent: Agent) -> int`:
     - Reads `scan_result.raw_payload.get("hosts", [])`.
     - For each host:
       - Validate `ip_address` exists.
       - Query existing device with:
         `Device.organization_id == agent.organization_id`, `Device.ip_address == ip_address`, `Device.deleted_at.is_(None)`.
       - If device exists:
         - Update `last_seen_at = func.now()`.
         - Update `status = host.get("status", "unknown")`.
         - Update `hostname = host.get("hostname") or existing.hostname`.
         - Update `mac_address = host.get("mac_address") or existing.mac_address`.
         - Update `vendor = host.get("vendor") or existing.vendor`.
         - Update `agent_id = agent.id`.
       - If device does not exist:
         - Create new `Device`:
           - `organization_id = agent.organization_id`
           - `agent_id = agent.id`
           - `ip_address = ip_address`
           - `mac_address = host.get("mac_address")`
           - `hostname = host.get("hostname")`
           - `vendor = host.get("vendor")`
           - `status = host.get("status", "unknown")`
           - `last_seen_at = func.now()`
         - Add to session.
     - Commit changes and return count of processed devices.
2. In `backend/app/api/v1/agents.py`:
   - In `upload_result()` endpoint:
     - When `result.result_type == "discovery"`:
       - Call `process_discovery_result(db, result, agent)`.

## What NOT to Implement
- Do NOT implement vulnerability matching in this task.
- Do NOT modify `backend/app/api/v1/devices.py` in this task (handled in Task 11.4).

## Constraints
- Follow `UniqueConstraint('organization_id', 'ip_address')`.
- Multi-tenant isolation: always use `agent.organization_id`.

## Testing
Run pytest to verify result upload and integration:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/test_agents.py tests/test_scans.py -v --tb=short
```

## Completion Criteria
- [ ] `process_discovery_result()` implemented.
- [ ] `POST /agents/results` executes discovery processing when `result_type == "discovery"`.
- [ ] Repeat scans update devices without duplicates.
- [ ] Tests pass without regression.
- [ ] `prompts/phase_11/progress.md` updated.

## Progress Update
Update `prompts/phase_11/progress.md` with:
- Task 11.3 status set to `Completed`.
- Files changed.
- Test outcome.
- Next task set to `11.4`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start the next task.
Do not execute more commands.
Output a short summary and wait for user instruction.
