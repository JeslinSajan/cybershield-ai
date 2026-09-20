# Phase 15 — Threat Detection

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> This prompt was written before execution. Before running it:
> (1) Run `alembic current` — confirm which migrations are applied.
> (2) Check `backend/app/api/v1/` — note which endpoints already exist.
> (3) Check `tests/` — note which test files already exist.
> (4) If reality differs from this prompt's assumptions, update this file first, then execute.
> Prompts are a living plan, not a frozen snapshot.

---

## Prompt

**Scope:**
1. **Detection Engine (in backend/app/services/detection_service.py)**:
   - Run synchronously after log save and after scan result save.
   - Rule 1: Brute Force — 5+ `login_failure` logs from same `source_ip` within 10 minutes.
   - Rule 2: Port Scan — scan result shows 10+ open ports on one device.
   - Rule 3: Suspicious Login — `login_success` from an IP that had 3+ `login_failure` in the last hour.
2. **Alert Creation**:
   - Create rows in the `Alert` model with exact columns: `organization_id`, `agent_id`, `device_id`, `alert_type` (brute_force, port_scan, suspicious_login), `severity`, `status` (default 'Open'), `description`, `risk_score` (High=40, Medium=20, Low=10), `triggered_at` = now().
   - Deduplication: Do not create if the same `alert_type` + `agent_id` + `source_ip` already has status 'Open' or 'Acknowledged' created in the last hour.
3. **Audit Log & Notifications**:
   - Write an `AuditLog` after each alert creation: `actor_type`='system', `actor_id`=None, `action`='alert_created', `target_type`='alerts', `target_id`=alert.id.
   - High/Critical Alerts: create `Notification` rows for all users in the org (`notification_type`='alert', `channel`='dashboard', `is_read`=False).
   - `Notification` model: `organization_id`, `user_id`, `alert_id`, `notification_type`, `channel`, `title`, `body`, `is_read`.

**Rules & Constraints:**
- Use the actual `AuditLog` columns: `organization_id`, `actor_type`, `actor_id`, `action`, `target_type`, `target_id`, `details`, `created_at`.
- No new RBAC dependencies — logic operates under the hood on save.
- Test against Neon DB. No Docker Compose.

**Verification Checklist:**
- [ ] Output of a script or tests triggering Rule 1 (Brute Force) and proving the `Alert` is created.
- [ ] Provide output confirming the `AuditLog` row exists for the newly created alert.
