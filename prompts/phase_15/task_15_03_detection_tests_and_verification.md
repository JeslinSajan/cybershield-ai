# Task: 15.3 — Threat Detection Tests & Handoff

## Objective
Implement comprehensive unit and integration tests in `tests/test_detection.py` verifying all three threat detection rules, alert deduplication, audit logging, and notification creation. Verify zero regressions across the entire test suite, update `prompts/HANDOFF.md`, and complete Phase 15.

## Context
- Phase: 15 — Threat Detection
- Master Plan: `prompts/phase_15/master.md`
- Progress Tracker: `prompts/phase_15/progress.md`
- Standards: `prompts/00_shared_standards.md`

## Files to Inspect First
- `backend/app/services/detection_service.py`
- `tests/test_detection.py`
- `prompts/HANDOFF.md`

## What to Implement
1. In `tests/test_detection.py`:
   - Test Rule 1: Brute Force — 5+ `login_failure` logs from same IP in 10 minutes creates `brute_force` Alert with `severity="High"`, `risk_score=40`, and `AuditLog` row.
   - Test Rule 2: Port Scan — scan result with 10+ open ports creates `port_scan` Alert with `severity="Medium"`, `risk_score=20`.
   - Test Rule 3: Suspicious Login — `login_success` from an IP with 3+ prior failures in 1 hour creates `suspicious_login` Alert with `severity="High"`, `risk_score=40`.
   - Test Deduplication: Subsequent matching events within 1 hour do not duplicate open alerts.
   - Test Notifications: High severity alerts generate `Notification` rows for active users in the organization.
   - Test Multi-tenant Isolation: Logs and scans in Org A never trigger alerts in Org B.
2. Run full pytest suite across all test files to verify zero regressions.
3. Update `prompts/HANDOFF.md` with Phase 15 completion details.
4. Mark Phase 15 complete in `prompts/phase_15_threat_detection.md`, `prompts/phase_15/master.md`, and `prompts/phase_15/progress.md`.

## Completion Criteria
- [ ] All tests in `tests/test_detection.py` pass.
- [ ] Full regression suite passes with 0 failures.
- [ ] `prompts/HANDOFF.md` updated.
- [ ] Phase 15 marked complete.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Phase 16.
Output a short summary and wait for user instruction.
