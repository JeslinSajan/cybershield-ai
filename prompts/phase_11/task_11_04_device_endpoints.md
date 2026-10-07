# Task: 11.4 — Backend Device Endpoints

## Objective
Implement `GET /api/v1/devices/` and `GET /api/v1/devices/{device_id}` in `backend/app/api/v1/devices.py` with multi-tenant filtering, status filtering, and pagination.

## Context
- Phase: 11 — Device Discovery
- Master Plan: prompts/phase_11/master.md
- Progress Tracker: prompts/phase_11/progress.md
- Standards: prompts/00_shared_standards.md

## Files to Inspect First
- `backend/app/api/v1/devices.py`
- `backend/app/models/device.py`
- `docs/api/device-api.md`

## What to Implement
1. In `backend/app/api/v1/devices.py`:
   - `GET /api/v1/devices/`:
     - Auth: `Depends(get_any_authenticated_user)`.
     - Query parameters:
       - `status` (optional, filter by device status)
       - `limit` (default 50, ge=1, le=200)
       - `offset` (default 0, ge=0)
     - Query `Device` rows where `organization_id == current_user.organization_id` and `deleted_at.is_(None)`.
     - Order by `last_seen_at.desc().nullslast()`, `created_at.desc()`.
     - Return array of device dictionaries matching `docs/api/device-api.md`.
   - `GET /api/v1/devices/{device_id}`:
     - Auth: `Depends(get_any_authenticated_user)`.
     - Query `Device` where `id == device_id`, `organization_id == current_user.organization_id`, and `deleted_at.is_(None)`.
     - If not found, return 404 with error envelope `{"error": {"code": "NOT_FOUND", "message": "Device not found.", "details": []}}`.
     - Return device dictionary.

## What NOT to Implement
- Do NOT implement vulnerability linking (`/devices/{id}/vulnerabilities`) in this task (Phase 13).
- Do NOT implement interface stats updates (`/devices/{id}/interfaces`) in this task (Phase 12).
- Do NOT modify frontend code in this task.

## Constraints
- Multi-tenant organization isolation: only return devices belonging to `current_user.organization_id`.
- RBAC: all authenticated users (Admin, Analyst, Viewer) can view devices.

## Testing
Test device list, device detail, status filter, and 404 behavior:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/ -v --tb=short
```

## Completion Criteria
- [ ] `GET /api/v1/devices/` implemented with pagination and status filter.
- [ ] `GET /api/v1/devices/{device_id}` implemented with 404 handling.
- [ ] Tests pass without regression.
- [ ] `prompts/phase_11/progress.md` updated.

## Progress Update
Update `prompts/phase_11/progress.md` with:
- Task 11.4 status set to `Completed`.
- Files changed.
- Test outcome.
- Next task set to `11.5`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start the next task.
Do not execute more commands.
Output a short summary and wait for user instruction.
