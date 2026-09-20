# Phase 18 — Threat Intelligence

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
1. **CRUD Endpoints (in backend/app/api/v1/threat_intelligence.py)**:
   - `POST /threat-intelligence/`: Role: `get_current_analyst_or_admin`. Body: `{indicator_type, value, description, source}`. Unique constraint on `(organization_id, indicator_type, value)`. Return 409 `CONFLICT` on duplicate.
   - `GET /threat-intelligence/`: Role: `get_any_authenticated_user`. Filter: `?indicator_type=ip`, `limit`, `offset`.
   - `GET /threat-intelligence/{id}`: Role: `get_any_authenticated_user`.
   - `DELETE /threat-intelligence/{id}`: Role: `get_current_admin` ONLY.
2. **Database Models**:
   - `ThreatIndicator` columns: `id`, `organization_id`, `indicator_type` ('ip'/'domain'/'hash'), `value`, `description`, `source` (default 'local'), `created_at`, `updated_at`.
   - Create model in `models/threat_intelligence.py` or `models/system.py` if not existing, and migrate.
3. **Detection Integration**:
   - In the log save handler: If `source_ip` is present, check `ThreatIndicator` for `indicator_type='ip'` and `value=source_ip`.
   - If match: Create `Alert` with `alert_type`='malware_indicator', `severity`='High', `risk_score`=40, `triggered_at`=now().
   - Create a Notification for all org users on match.
4. **Seed Data**:
   - Provide `backend/data/threat_seed.json` with 10 entries. Seed on startup if the table is empty.

**Rules & Constraints:**
- Use the actual RBAC dependencies exactly as named.
- Follow error envelopes.

**Verification Checklist:**
- [ ] Provide output of `pytest` for threat intelligence endpoints.
- [ ] Show output confirming that inserting a known threat IP log creates an alert.
