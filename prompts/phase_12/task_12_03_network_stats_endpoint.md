# Task: 12.3 — Network Stats Endpoint & Access Control

## Objective
Verify, refine, and thoroughly test the `GET /api/v1/agents/{agent_id}/network-stats` endpoint, ensuring strict RBAC enforcement (Admin + Analyst allowed, Viewer denied) and multi-tenant organization isolation.

## Context
- Phase: 12 — Network Monitoring
- Master Plan: prompts/phase_12/master.md
- Progress Tracker: prompts/phase_12/progress.md
- Standards: prompts/00_shared_standards.md

## Files to Inspect First
- `backend/app/api/v1/agents.py`
- `tests/test_agents.py`

## What to Implement
1. In `backend/app/api/v1/agents.py`:
   - Inspect `GET /agents/{agent_id}/network-stats`:
     - Confirm dependency is `get_current_analyst_or_admin`.
     - Confirm query filters by `Agent.id == agent_id` and `Agent.organization_id == current_user.organization_id`.
     - If agent not found: return 404 with error envelope `{"error": {"code": "NOT_FOUND", "message": "Agent not found.", "details": []}}`.
     - Filter heartbeats where `details != None` and `details.has_key("network")` or returns up to 10 most recent heartbeats.
2. In `tests/test_network_monitoring.py`:
   - Add tests:
     - Administrator can retrieve network stats (200 OK with list of heartbeat records containing network details).
     - Security Analyst can retrieve network stats (200 OK).
     - Viewer cannot retrieve network stats (403 Forbidden with `FORBIDDEN` error code).
     - Non-existent agent ID returns 404 NOT_FOUND.
     - Cross-organization agent access is prevented.

## What NOT to Implement
- Do NOT modify other agent endpoints.
- Do NOT begin Phase 13.

## Constraints
- Standard error envelope must be used.
- Enforce strict default-deny RBAC.

## Testing
Run pytest:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/test_network_monitoring.py -v --tb=short
```

## Completion Criteria
- [ ] `GET /api/v1/agents/{agent_id}/network-stats` returns up to 10 recent heartbeat snapshots.
- [ ] Analyst and Admin succeed with 200 OK.
- [ ] Viewer gets 403 Forbidden.
- [ ] Missing/cross-tenant agent handled cleanly.
- [ ] Tests pass in `tests/test_network_monitoring.py`.
- [ ] `prompts/phase_12/progress.md` updated.

## Progress Update
Update `prompts/phase_12/progress.md` with:
- Task 12.3 status set to `Completed`.
- Files changed.
- Test outcome.
- Next task set to `12.4`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Task 12.4.
Output a short summary and wait for user instruction.
