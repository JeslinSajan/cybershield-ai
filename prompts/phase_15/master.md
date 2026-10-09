# Phase 15 — Threat Detection — Master Plan

**Status:** Done  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> (1) Run `alembic current` — confirm which migrations are applied.  
> (2) Check `backend/app/api/v1/` — note which endpoints already exist.  
> (3) Check `tests/` — note which test files already exist.  
> (4) If reality differs from this prompt's assumptions, update this file first, then execute.  
> **Standards:** Follow `prompts/00_shared_standards.md` — all S1–S9 rules apply to this phase.

---

## DEPENDS ON
- Phase 13: `Vulnerability` rows, `ScanResult` rows (`result_type="services"`).
- Phase 14: `Log` rows with `source_ip` and `event_type` (`login_failure`, `login_success`).
- Database models: `Alert`, `AlertEvent`, `Notification`, `AuditLog`.

## PRODUCES
- `Alert` rows (types: `brute_force`, `port_scan`, `suspicious_login`).
- `Notification` rows for High/Critical alerts for all active organization users.
- `AuditLog` rows (`action="alert_created"`).
- Detection engine in `backend/app/services/detection_service.py`.
- Synchronous invocation on log save (`POST /api/v1/agents/logs`) and scan result save (`POST /api/v1/agents/results`).

---

## Task Decomposition

| Task ID | Task Title | Description | Target Files |
|---|---|---|---|
| 15.1 | Detection Service & Core Rules | Implement `detection_service.py` with 3 detection rules, alert deduplication, audit logs, and notifications. | `backend/app/services/detection_service.py` |
| 15.2 | Ingestion Endpoint Integration | Hook detection service into `POST /api/v1/agents/logs` and `POST /api/v1/agents/results` in `agents.py`. | `backend/app/api/v1/agents.py` |
| 15.3 | Threat Detection Tests & Handoff | Implement comprehensive test suite in `tests/test_detection.py`, update `HANDOFF.md`, and complete Phase 15. | `tests/test_detection.py`, `prompts/HANDOFF.md`, `prompts/phase_15/progress.md` |

---

## Rule Definitions & Severities
- **Rule 1: Brute Force**
  - Trigger: 5+ `login_failure` logs from same `source_ip` within 10 minutes.
  - Alert: `alert_type="brute_force"`, `severity="High"`, `risk_score=40`.
- **Rule 2: Port Scan**
  - Trigger: Scan result shows 10+ open ports on one device.
  - Alert: `alert_type="port_scan"`, `severity="Medium"`, `risk_score=20`.
- **Rule 3: Suspicious Login**
  - Trigger: `login_success` from an IP that had 3+ `login_failure` in the last hour.
  - Alert: `alert_type="suspicious_login"`, `severity="High"`, `risk_score=40`.
- **Deduplication:**
  - Do not create duplicate alert if an alert with same `alert_type` and `agent_id`/`device_id`/`source_ip` has status in `('Open', 'Acknowledged')` created in the last 1 hour.
- **Side-Effects on Alert Creation:**
  - `AuditLog`: `actor_type="system"`, `actor_id=None`, `action="alert_created"`, `target_type="alerts"`, `target_id=alert.id`.
  - High/Critical Alerts: `Notification` created for all active users in the organization (`notification_type="alert"`, `channel="dashboard"`).
