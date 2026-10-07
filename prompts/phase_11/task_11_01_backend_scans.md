# Task: 11.1 — Backend Scan Creation for Discovery

## Objective
Update the scans router to accept `discovery` scans, implement scan listing, implement scan detail retrieval, and record audit logs.

## Context
- Phase: 11 — Device Discovery
- Master Plan: prompts/phase_11/master.md
- Progress Tracker: prompts/phase_11/progress.md
- Standards: prompts/00_shared_standards.md

## Files to Inspect First
- `backend/app/api/v1/scans.py`
- `backend/app/models/scan.py`
- `backend/app/models/system.py`

## What to Implement
1. In `backend/app/api/v1/scans.py`:
   - Update `CreateTaskRequest` schema: allow `scan_type` to accept `"health_check"` and `"discovery"`.
   - In `POST /api/v1/scans/`:
     - Verify agent belongs to user's organization and is active and online.
     - Create `Scan` row with `status="PENDING"`.
     - Write an `AuditLog` entry: `actor_type="user"`, `actor_id=current_user.id`, `action="scan_created"`, `target_type="scans"`, `target_id=task.id`.
     - Commit and return the scan payload.
   - In `GET /api/v1/scans/`:
     - Add query parameters: `status` (optional), `limit` (default 50, max 200), `offset` (default 0).
     - Query `Scan` rows filtered by `current_user.organization_id`.
     - Order by `created_at.desc()`.
     - Return list of scan dictionaries.
   - In `GET /api/v1/scans/{scan_id}`:
     - Query `Scan` by `id` and `organization_id == current_user.organization_id`.
     - If not found, return 404 with error envelope `{"error": {"code": "NOT_FOUND", "message": "Scan not found.", "details": []}}`.
     - Return the scan dictionary.

## What NOT to Implement
- Do NOT implement device discovery processing or parsing in this task.
- Do NOT modify `backend/app/api/v1/devices.py`.
- Do NOT modify agent code in this task.
- Do NOT install new dependencies.

## Constraints
- Follow `prompts/00_shared_standards.md`.
- Enforce default-deny RBAC: `POST /api/v1/scans/` and `GET /api/v1/scans/` require `get_current_analyst_or_admin`.
- Errors must use standard error envelope.

## Testing
Run pytest to verify scan routes and existing test suite integrity:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/test_agents.py tests/test_rbac.py -v --tb=short
```

## Completion Criteria
- [ ] `POST /api/v1/scans/` creates discovery scans.
- [ ] `AuditLog` row created on scan creation.
- [ ] `GET /api/v1/scans/` lists scans for the organization.
- [ ] `GET /api/v1/scans/{scan_id}` retrieves scan details.
- [ ] All tests pass without regression.
- [ ] `prompts/phase_11/progress.md` updated.

## Progress Update
Update `prompts/phase_11/progress.md` with:
- Task 11.1 status set to `Completed`.
- Files changed.
- Test outcome.
- Next task set to `11.2`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start the next task.
Do not execute more commands.
Output a short summary and wait for user instruction.
