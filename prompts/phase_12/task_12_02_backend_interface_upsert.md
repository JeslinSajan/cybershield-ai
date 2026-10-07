# Task: 12.2 — Backend Device Interface Upsert on Heartbeat

## Objective
Update the `POST /api/v1/agents/heartbeat` endpoint in `backend/app/api/v1/agents.py` to inspect `details["network"]["interfaces"]` and upsert records into `device_interfaces` when a device is linked to the agent.

## Context
- Phase: 12 — Network Monitoring
- Master Plan: prompts/phase_12/master.md
- Progress Tracker: prompts/phase_12/progress.md
- Standards: prompts/00_shared_standards.md

## Files to Inspect First
- `backend/app/api/v1/agents.py`
- `backend/app/models/device.py`
- `backend/app/models/agent.py`

## What to Implement
1. In `backend/app/api/v1/agents.py`:
   - Within `agent_heartbeat()`:
     - Check if `body.details` contains a `"network"` dict with an `"interfaces"` list.
     - If present, query for a linked `Device`:
       `device = db.query(Device).filter(Device.agent_id == agent.id, Device.deleted_at == None).first()`
     - If no device is linked: skip upsert silently.
     - If linked device is found:
       - For each interface item in `interfaces`:
         - Query existing `DeviceInterface`:
           `iface_row = db.query(DeviceInterface).filter(DeviceInterface.organization_id == agent.organization_id, DeviceInterface.device_id == device.id, DeviceInterface.name == iface["name"]).first()`
         - If found:
           - Update `bytes_sent = iface.get("bytes_sent", 0)`
           - Update `bytes_received = iface.get("bytes_received", 0)`
           - If `iface.get("mac_address")`: update `mac_address`
           - If `iface.get("ip_address")`: update `ip_address`
           - Update `updated_at`
         - If not found:
           - Create new `DeviceInterface(organization_id=agent.organization_id, device_id=device.id, name=iface["name"], mac_address=iface.get("mac_address"), ip_address=iface.get("ip_address"), bytes_sent=iface.get("bytes_sent", 0), bytes_received=iface.get("bytes_received", 0))`
           - Add to db.
     - Wrap interface upsert logic defensively so failures do not prevent successful heartbeat recording.
2. In `tests/test_network_monitoring.py`:
   - Add tests verifying:
     - Heartbeat with linked device creates `DeviceInterface` records.
     - Repeat heartbeat updates byte counts without duplicating records.
     - Heartbeat without linked device succeeds without error and creates 0 interface rows.

## What NOT to Implement
- Do NOT alter scan routes or agent registration.
- Do NOT modify the `DeviceInterface` model schema.

## Constraints
- Query-then-update pattern ensures SQLite and PostgreSQL compatibility.
- Ensure multi-tenant organization isolation is maintained.

## Testing
Run pytest:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/test_network_monitoring.py -v --tb=short
```

## Completion Criteria
- [ ] `DeviceInterface` records created when linked device exists.
- [ ] `DeviceInterface` byte counters updated on successive heartbeats.
- [ ] Graceful no-op when no device is linked.
- [ ] Tests pass in `tests/test_network_monitoring.py`.
- [ ] `prompts/phase_12/progress.md` updated.

## Progress Update
Update `prompts/phase_12/progress.md` with:
- Task 12.2 status set to `Completed`.
- Files changed.
- Test outcome.
- Next task set to `12.3`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Task 12.3.
Output a short summary and wait for user instruction.
