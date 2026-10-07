# Task: 12.4 — Network Monitoring Integration & Final Verification

## Objective
Implement an end-to-end integration test for Network Monitoring, execute the full regression test suite, update handoff documentation in `prompts/HANDOFF.md`, mark Phase 12 complete, and prepare for Phase 13.

## Context
- Phase: 12 — Network Monitoring
- Master Plan: prompts/phase_12/master.md
- Progress Tracker: prompts/phase_12/progress.md
- Standards: prompts/00_shared_standards.md

## Files to Inspect First
- `tests/test_network_monitoring.py`
- `prompts/HANDOFF.md`
- `prompts/phase_12/master.md`
- `prompts/phase_12/progress.md`

## What to Implement
1. In `tests/test_network_monitoring.py`:
   - Add `TestNetworkMonitoringIntegration`:
     - Step 1: Create an Agent, Device, and link `device.agent_id = agent.id`.
     - Step 2: Agent sends heartbeat containing `details["network"]` with multiple interfaces.
     - Step 3: Verify `DeviceInterface` rows are created in database with accurate byte counters.
     - Step 4: Agent sends updated heartbeat with higher byte counts.
     - Step 5: Verify `DeviceInterface` rows are updated without duplication.
     - Step 6: Analyst retrieves network stats via `GET /api/v1/agents/{agent_id}/network-stats` and confirms receipt of interface data.
2. Run full pytest suite across all test files to verify zero regressions.
3. Update `prompts/HANDOFF.md` with Phase 12 completion record.
4. Update `prompts/phase_12_network_monitoring.md` and `prompts/phase_12/master.md` status to `Done`.
5. Update `prompts/phase_12/progress.md` status to `Completed`.

## What NOT to Implement
- Do NOT begin Phase 13 in this task.
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
- [ ] `prompts/phase_12/progress.md` marked `Completed`.
- [ ] Phase 12 status marked `Done`.

## Progress Update
Update `prompts/phase_12/progress.md` with:
- Task 12.4 status set to `Completed`.
- Phase status set to `Completed`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Phase 13.
Output a short summary and wait for user instruction.
