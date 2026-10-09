# Task: 14.2 — Backend Log Query Endpoints

## Objective
Implement `GET /api/v1/logs/` and `GET /api/v1/logs/{id}` in `backend/app/api/v1/logs.py` allowing authenticated users across all three roles (Viewer, Security Analyst, Administrator) to query, filter, and paginate security logs with organization isolation.

## Context
- Phase: 14 — Log Management
- Master Plan: `prompts/phase_14/master.md`
- Progress Tracker: `prompts/phase_14/progress.md`
- Standards: `prompts/00_shared_standards.md`

## Files to Inspect First
- `backend/app/models/log.py`
- `backend/app/api/v1/logs.py`
- `docs/api/log-api.md`

## What to Implement
1. In `backend/app/api/v1/logs.py`:
   - Replace stubs with functional endpoints:
     - `GET /api/v1/logs/`:
       - Dependency: `get_any_authenticated_user`.
       - Query parameters:
         - `event_type`: Optional[str]
         - `source`: Optional[str]
         - `severity`: Optional[str]
         - `username`: Optional[str]
         - `source_ip`: Optional[str]
         - `from_date`: Optional[datetime] (alias `start_time`)
         - `to_date`: Optional[datetime] (alias `end_time`)
         - `limit`: int (default 50, max 200)
         - `offset`: int (default 0)
       - Filters strictly by `organization_id == current_user.organization_id`.
       - Orders by `timestamp.desc()`.
       - Returns list of log entries.
     - `GET /api/v1/logs/{log_id}`:
       - Dependency: `get_any_authenticated_user`.
       - Returns a single log entry.
       - Returns 404 with standard error envelope if not found in caller's organization.
2. In `tests/test_logs.py`:
   - Add tests verifying:
     - All 3 roles (Admin, Analyst, Viewer) can read `/logs/` and `/logs/{id}`.
     - Filtering by `event_type`, `source`, `severity`, `from_date`, `to_date`.
     - Pagination (`limit` and `offset`).
     - Single log retrieval and 404 handling.
     - Multi-tenant organization isolation (User in Org A cannot view Org B logs).

## What NOT to Implement
- Do NOT implement agent log collection in this task (Task 14.3).

## Testing
Run pytest:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/test_logs.py -v --tb=short
```

## Completion Criteria
- [ ] `GET /api/v1/logs/` works with all filters and pagination.
- [ ] `GET /api/v1/logs/{id}` returns single log and 404 envelope on missing.
- [ ] All three roles have read access.
- [ ] Tests pass in `tests/test_logs.py`.
- [ ] `prompts/phase_14/progress.md` updated.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Task 14.3.
Output a short summary and wait for user instruction.
