# Phase 16 — Alert Management

**Status:** Done  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> This prompt was written before execution. Before running it:
> (1) Run `alembic current` — confirm which migrations are applied.
> (2) Check `backend/app/api/v1/` — note which endpoints already exist.
> (3) Check `tests/` — note which test files already exist.
> (4) If reality differs from this prompt's assumptions, update this file first, then execute.
> Prompts are a living plan, not a frozen snapshot.
> **Standards:** Follow [`prompts/00_shared_standards.md`](prompts/00_shared_standards.md) — all S1–S9 rules apply to this phase.


---


---

## DEPENDS ON
Phase 15: `Alert` rows in DB; `AlertEvent` model from migration 001

## PRODUCES
`PATCH /alerts/{id}` (status transitions); `AlertEvent` rows; `GET /alerts/summary`; `GET /alerts/{id}/history`; `GET /alerts/` endpoint

**Consumed by:** Phase 17 (recalculate risk on Resolved/False Positive), Phase 19 (AI explanation), Phase 21 (alert UI)

## HANDOFF REQUIREMENT
On completing this phase, append an entry to `prompts/HANDOFF.md`.
Append valid status transitions list, `AlertEvent` column usage, and `/alerts/summary` response shape to `prompts/HANDOFF.md`.

---
## Prompt

**Scope:**
1. **CRUD Endpoints (in backend/app/api/v1/alerts.py)**:
   - `GET /alerts/summary`: Role: `get_any_authenticated_user`. Must return counts for `{open, acknowledged, investigating, resolved, false_positive, critical, high, medium, low}`. **Register this route BEFORE `/{id}` in the router.**
   - `GET /alerts/`: Role: `get_any_authenticated_user`. Filters: `status`, `severity`, `alert_type`, `limit`, `offset`.
   - `GET /alerts/{id}`: Role: `get_any_authenticated_user`. Returns alert + `alert_events` history.
   - `GET /alerts/{id}/history`: Role: `get_any_authenticated_user`. Returns `alert_events` ordered by `changed_at`.
   - `PATCH /alerts/{id}`: Role: `get_current_analyst_or_admin` (Viewers get 403).
2. **Patch Logic**:
   - Body: `{status: string, reason: string (optional)}`.
   - Valid Transitions: 
     - Open → Acknowledged / Investigating / False Positive
     - Acknowledged → Investigating / Resolved / False Positive
     - Investigating → Resolved / False Positive
   - Invalid Transitions: Returns 400 with `VALIDATION_ERROR` code in the exact error envelope format.
   - Success: Create `AlertEvent` row (columns: `organization_id`, `alert_id`, `actor_user_id` [from JWT], `from_status`, `to_status`, `reason`, `changed_at`=now()).
   - Write `AuditLog`: `actor_type`='user', `actor_id`=user.id, `action`='alert_status_changed', `target_type`='alerts', `target_id`=alert.id.

**Rules & Constraints:**
- Return actual error envelope on 400s or 403s.
- Use actual dependency `get_current_analyst_or_admin`.
- Update API docs.

**Verification Checklist:**
- [ ] Provide output of `curl` hitting `PATCH /alerts/{id}` and successfully transitioning an alert.
- [ ] Provide output of `curl GET /alerts/summary`.
