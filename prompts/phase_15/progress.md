# Phase 15 Progress Tracker — Threat Detection

**Phase Status:** In Progress  
**Current Task:** 15.2 Ingestion Endpoint Integration

---

## Task Summary Table

| Task ID | Task Title | Status | Files Changed | Tests |
|---|---|---|---|---|
| 15.1 | Detection Service & Core Rules | Completed | backend/app/services/detection_service.py | full suite PASSED (181/181) |
| 15.2 | Ingestion Endpoint Integration | Pending | — | — |
| 15.3 | Threat Detection Tests & Handoff | Pending | — | — |

---

## Last Completed Task Details

### Task 15.1: Detection Service & Core Rules
- **Completed at:** 2026-10-09
- **Files Modified / Created:**
  - `backend/app/services/detection_service.py`: implemented core threat detection engine with 3 rules:
    - Rule 1 (Brute Force): triggers when 5+ `login_failure` events occur from the same source IP in 10 minutes (`severity="High"`, `risk_score=40`).
    - Rule 2 (Port Scan): triggers when a scan result indicates 10+ open ports on a device (`severity="Medium"`, `risk_score=20`).
    - Rule 3 (Suspicious Login): triggers when a `login_success` occurs from an IP with 3+ prior failures in the last hour (`severity="High"`, `risk_score=40`).
    - Alert deduplication: suppresses duplicate alerts if an active alert (status in `Open`, `Acknowledged`) with the same type and IP/agent exists within the last hour.
    - System AuditLog generation: writes `action="alert_created"` with `actor_type="system"`.
    - Notification dispatch: creates `Notification` rows for all active organization users for High and Critical alerts.
    - Batch helpers `process_log_detections` and `process_scan_detections`.
- **Tests Passed:**
  - Full suite (`pytest tests/`): 181 passed, 0 failed. Zero regressions.
- **Known Issues:** None.

---

## Next Task
- **ID:** 15.2
- **File:** `prompts/phase_15/task_15_02_hook_detection_into_endpoints.md`
