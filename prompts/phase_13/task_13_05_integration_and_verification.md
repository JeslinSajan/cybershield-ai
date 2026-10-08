# Task: 13.5 — Vulnerability Scanning Integration & Final Verification

## Objective
Implement an end-to-end integration test covering the entire vulnerability scanning lifecycle, run the complete regression test suite, update handoff documentation, mark Phase 13 complete, and prepare for Phase 14.

## Context
- Phase: 13 — Vulnerability Scanning
- Master Plan: prompts/phase_13/master.md
- Progress Tracker: prompts/phase_13/progress.md
- Standards: prompts/00_shared_standards.md

## Files to Inspect First
- `tests/test_vulnerabilities.py`
- `prompts/HANDOFF.md`
- `prompts/phase_13/master.md`
- `prompts/phase_13/progress.md`

## What to Implement
1. In `tests/test_vulnerabilities.py`:
   - Add `TestVulnerabilityScanningIntegration`:
     - Step 1: Seed CVEs for test organization.
     - Step 2: Analyst creates vulnerability scan via `POST /api/v1/scans/` targeting a device IP.
     - Step 3: Agent polls task via `GET /api/v1/agents/tasks`.
     - Step 4: Agent executes vulnerability scan and uploads results via `POST /api/v1/agents/results` with `result_type="services"`.
     - Step 5: Backend processes result, matches services against CVE database, creates `Vulnerability` entries, and sets scan status to `COMPLETED`.
     - Step 6: Viewer queries `GET /api/v1/vulnerabilities/` and verifies presence of created vulnerabilities.
     - Step 7: Viewer queries `GET /api/v1/devices/{device_id}/vulnerabilities` and verifies device-specific vulnerabilities.
2. Run full pytest suite across all test files to verify zero regressions.
3. Update `prompts/HANDOFF.md` with Phase 13 completion record.
4. Update `prompts/phase_13_vulnerability_scanning.md` and `prompts/phase_13/master.md` status to `Done`.
5. Update `prompts/phase_13/progress.md` status to `Completed`.

## What NOT to Implement
- Do NOT begin Phase 14 in this task.
- Do NOT modify unrelated models or migrations.

## Constraints
- Zero regressions across the full test suite.

## Testing
Run pytest:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/ -v --tb=short
```

## Completion Criteria
- [ ] Integration test passes.
- [ ] Full test suite passes without regressions.
- [ ] `prompts/HANDOFF.md` updated.
- [ ] `prompts/phase_13/progress.md` marked `Completed`.
- [ ] Phase 13 status marked `Done`.

## Progress Update
Update `prompts/phase_13/progress.md` with:
- Task 13.5 status set to `Completed`.
- Phase status set to `Completed`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Phase 14.
Output a short summary and wait for user instruction.
