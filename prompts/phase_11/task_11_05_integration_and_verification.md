# Task: 11.5 — Device Discovery End-to-End Integration & Verification

## Objective
Implement an end-to-end integration test verifying the entire discovery loop: Analyst creates scan task → Agent polls task → Agent executes discovery → Agent uploads results → Backend upserts devices → User retrieves discovered devices via API. Verify full regression test suite, update documentation, and mark Phase 11 complete.

## Context
- Phase: 11 — Device Discovery
- Master Plan: prompts/phase_11/master.md
- Progress Tracker: prompts/phase_11/progress.md
- Standards: prompts/00_shared_standards.md

## Files to Inspect First
- `tests/test_devices.py`
- `tests/test_scans.py`
- `agent/task_poller.py`

## What to Implement
1. In `tests/test_devices.py`:
   - Add `TestDeviceDiscoveryIntegration`:
     - Step 1: Admin/Analyst calls `POST /api/v1/scans/` with `scan_type="discovery"` and `target_scope="192.168.1.0/24"`.
     - Step 2: Agent calls `GET /api/v1/agents/tasks` to receive the pending task.
     - Step 3: Agent runs discovery and posts result to `POST /api/v1/agents/results`.
     - Step 4: Verify task status is now `COMPLETED`.
     - Step 5: Viewer calls `GET /api/v1/devices/` and retrieves the newly discovered devices.
2. Run full pytest suite across all test files to verify zero regressions.
3. Update `prompts/HANDOFF.md` with Phase 11 completion record.
4. Update `prompts/phase_11_device_discovery.md` and `prompts/phase_11/master.md` status to `Done`.

## What NOT to Implement
- Do NOT begin Phase 12 in this task.
- Do NOT modify unrelated models or migrations.

## Constraints
- Zero regressions across the existing test suite.

## Testing
Run the complete test suite:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/ -v --tb=short
```

## Completion Criteria
- [ ] End-to-end integration test passes.
- [ ] Full test suite passes without regressions.
- [ ] `prompts/HANDOFF.md` updated.
- [ ] `prompts/phase_11/progress.md` marked `Completed`.
- [ ] Phase 11 status marked `Done`.

## Progress Update
Update `prompts/phase_11/progress.md` with:
- Task 11.5 status set to `Completed`.
- Phase status set to `Completed`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Phase 12.
Do not execute more commands.
Output a short summary and wait for user instruction.
