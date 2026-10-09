# Task: 15.1 — Detection Service & Core Rules

## Objective
Implement `backend/app/services/detection_service.py` with three core detection rules (Brute Force, Port Scan, Suspicious Login), alert deduplication (1-hour window for Open/Acknowledged alerts), audit log generation, and user notifications for High/Critical alerts.

## Context
- Phase: 15 — Threat Detection
- Master Plan: `prompts/phase_15/master.md`
- Progress Tracker: `prompts/phase_15/progress.md`
- Standards: `prompts/00_shared_standards.md`

## Files to Inspect First
- `backend/app/models/alert.py` (`Alert`, `AlertEvent`)
- `backend/app/models/system.py` (`Notification`, `AuditLog`)
- `backend/app/models/log.py` (`Log`)
- `backend/app/models/scan.py` (`ScanResult`)
- `backend/app/models/user.py` (`User`)

## What to Implement
1. In `backend/app/services/detection_service.py`:
   - Function `create_alert(db, org_id, alert_type, severity, description, risk_score, agent_id=None, device_id=None, source_ip=None) -> Optional[Alert]`:
     - Checks deduplication: if an alert in same `organization_id` with same `alert_type`, `agent_id`, and `source_ip` (embedded in description) with `status` in `['Open', 'Acknowledged']` was created in the last 1 hour, return None.
     - Creates `Alert` record with: `organization_id`, `agent_id`, `device_id`, `alert_type`, `severity`, `status='Open'`, `description`, `risk_score`, `triggered_at=datetime.now(timezone.utc)`.
     - Writes `AuditLog`: `actor_type='system'`, `actor_id=None`, `action='alert_created'`, `target_type='alerts'`, `target_id=alert.id`.
     - For High or Critical severity: finds all active users in `organization_id` and creates `Notification` rows (`notification_type='alert'`, `channel='dashboard'`, `is_read=False`).
     - Flushes or commits as appropriate and returns the created `Alert`.
   - Rule 1: `check_brute_force(db, org_id, agent_id, source_ip, device_id=None) -> Optional[Alert]`:
     - Counts `login_failure` logs from `source_ip` within the last 10 minutes for `org_id`.
     - If count >= 5: calls `create_alert` with `alert_type="brute_force"`, `severity="High"`, `risk_score=40`.
   - Rule 2: `check_port_scan(db, org_id, agent_id, scan_result) -> Optional[Alert]`:
     - Inspects `scan_result.raw_payload`: checks if `services` has 10 or more open ports on one device/target.
     - If >= 10 open ports: calls `create_alert` with `alert_type="port_scan"`, `severity="Medium"`, `risk_score=20`.
   - Rule 3: `check_suspicious_login(db, org_id, agent_id, source_ip, username, device_id=None) -> Optional[Alert]`:
     - When a `login_success` occurs: checks if `source_ip` had 3 or more `login_failure` logs in the last 1 hour for `org_id`.
     - If >= 3 failures: calls `create_alert` with `alert_type="suspicious_login"`, `severity="High"`, `risk_score=40`.
   - Dispatch helper functions:
     - `process_log_detections(db, org_id, agent_id, logs: List[Log]) -> List[Alert]`
     - `process_scan_detections(db, org_id, agent_id, scan_result: ScanResult) -> List[Alert]`

## What NOT to Implement
- Do NOT modify user endpoints or agent models.
- Do NOT implement AI assistant explanations (Phase 19).

## Testing
Run pytest:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/ -q --tb=short
```

## Completion Criteria
- [ ] `detection_service.py` implemented with all 3 rules, deduplication, audit log, and notification dispatch.
- [ ] Tests pass without regressions.
- [ ] `prompts/phase_15/progress.md` updated.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Task 15.2.
Output a short summary and wait for user instruction.
