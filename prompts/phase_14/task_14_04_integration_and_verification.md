# Task: 14.4 — Log Management Integration & Final Verification

## Objective
Implement an end-to-end integration test verifying agent log collection, ingestion via `POST /api/v1/agents/logs`, database storage in `logs`, and user querying via `GET /api/v1/logs/`. Run full test suite, update handoff documentation, mark Phase 14 complete, and prepare for Phase 15.

## Context
- Phase: 14 — Log Management
- Master Plan: `prompts/phase_14/master.md`
- Progress Tracker: `prompts/phase_14/progress.md`
- Standards: `prompts/00_shared_standards.md`

## Files to Inspect First
- `tests/test_logs.py`
- `prompts/HANDOFF.md`
- `prompts/phase_14/master.md`
- `prompts/phase_14/progress.md`

## What to Implement
1. In `tests/test_logs.py`:
   - Add `TestLogManagementIntegration`:
     - Step 1: Agent sends batch of `login_failure` and `login_success` events to `POST /api/v1/agents/logs`.
     - Step 2: Backend commits events to `logs` table with correct severities (`medium` and `low`).
     - Step 3: Viewer queries `GET /api/v1/logs/` and filters by `event_type=login_failure` and `event_type=login_success`.
     - Step 4: Viewer queries single log via `GET /api/v1/logs/{id}` and verifies all fields.
2. Run full pytest suite across all test files to verify zero regressions.
3. Update `prompts/HANDOFF.md` with Phase 14 completion details (confirmed table column names, payload shape, valid event types).
4. Update `prompts/phase_14_log_management.md` and `prompts/phase_14/master.md` status to `Done`.
5. Update `prompts/phase_14/progress.md` status to `Completed`.

## Constraints
- Zero regressions across the full test suite.
- Do NOT begin Phase 15 in this task.

## Testing
Run pytest:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/ -v --tb=short
```

## Completion Criteria
- [ ] Integration test passes.
- [ ] Full regression suite passes without regressions.
- [ ] `prompts/HANDOFF.md` updated with Phase 14 details.
- [ ] Phase 14 marked `Done`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Phase 15.
Output a short summary and wait for user instruction.
