# Phase 16 — Alert Management

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 16: Alert Management

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

Full CRUD API for security alerts so Analysts and Admins can view, 
investigate, and resolve them from the dashboard.

=======================================================================
ALERT STATUSES
=======================================================================

An alert moves through these statuses:
  Open → Acknowledged → Investigating → Resolved
  or
  Open → False Positive

=======================================================================
BACKEND ENDPOINTS
=======================================================================

GET /api/v1/alerts/
  - Admin, Analyst, Viewer (all can read).
  - Returns list of alerts with: id, type, severity, status, 
    description, source_ip, device_id, agent_id, created_at.
  - Supports filters: ?status=Open&severity=High&type=BruteForce

GET /api/v1/alerts/{id}
  - All roles. Single alert detail with full history.

PATCH /api/v1/alerts/{id}
  - Administrator and Analyst only (Viewer gets 403).
  - Allowed fields to update: { "status": "Acknowledged", "reason": "..." }
  - Valid status transitions only:
      Open → Acknowledged, Investigating, False Positive
      Acknowledged → Investigating, Resolved, False Positive
      Investigating → Resolved, False Positive
  - Invalid transitions return 400 with a clear error message.
  - When status changes, create a row in alert_events table.
    Use EXACT column names from schema (table 18):
      organization_id, alert_id,
      actor_user_id (user id from JWT),
      from_status (previous status),
      to_status (new status),
      reason (optional note from the request body),
      changed_at = now()
  - Also write an audit_log entry:
      action = "alert_status_changed",
      actor_type = "user", actor_id = <user_id from JWT>,
      target_type = "alerts", target_id = <alert_id>

GET /api/v1/alerts/{id}/history
  - All roles. Returns all status changes from alert_events.

=======================================================================
ALERT COUNTS FOR DASHBOARD
=======================================================================

GET /api/v1/alerts/summary
  - All roles.
  - Returns:
      {
        "open": 5,
        "acknowledged": 2,
        "investigating": 1,
        "critical": 3,
        "high": 4
      }
  - Used by the dashboard summary cards.

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Create a test alert via the detection service.
2. PATCH it to Acknowledged — confirm alert_events row is created.
3. Try an invalid transition (e.g. Resolved → Open) — confirm 400.
4. A Viewer trying to PATCH — confirm 403.
5. GET /alerts/summary — confirm counts are correct.
6. pytest tests/ — no regressions.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 16 — alert management with status transitions and history"
```
