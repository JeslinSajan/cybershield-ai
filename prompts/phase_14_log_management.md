# Phase 14 — Log Management

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
1. **Agent Implementation**: 
   - Collect auth logs: `auth.log` on Linux or Windows Security Event Log.
   - Windows fallback: if `pywin32` is not installed, log a warning and return an empty list. Do NOT crash, and do not make `pywin32` mandatory in requirements. Add a note to `agent/README.md`.
   - Send logs to `POST /api/v1/agents/logs` using agent credentials (NOT a user JWT).
   - Track `last_sent_timestamp` locally on the agent to avoid re-sending logs.
2. **Backend Endpoints (in backend/app/api/v1/logs.py and agents.py)**:
   - `POST /api/v1/agents/logs`: An AGENT endpoint. Document in `docs/api/agent-api.md`.
   - `GET /api/v1/logs/`: `get_any_authenticated_user`, filters: `event_type`, `source`, `from_date`, `to_date`, `limit`/`offset`.
   - `GET /api/v1/logs/{id}`: `get_any_authenticated_user`.
3. **Database**:
   - `Log` model columns: `id`, `organization_id`, `agent_id`, `device_id` (nullable), `source`, `event_type`, `severity`, `message`, `source_ip` (INET), `username`, `timestamp`, `created_at`, `updated_at`.
   - Detect if the model exists in `models/`; if not, create it and run a migration. `source_ip` is stored as INET in Postgres but passed as a string (SQLAlchemy handles this).
   - Mapping: `login_failure` → `medium`, `login_success` → `low`, unknown → `info`.
   - `event_type` must be exact: `'login_success'`, `'login_failure'`.

**Rules & Constraints:**
- Use the actual error envelope shape for all exceptions.
- Rely only on exact RBAC: `get_any_authenticated_user` for user endpoints.
- Update `docs/api/` as needed. No external AI.
- Never log secrets.
- Test against Neon DB.

**Verification Checklist:**
- [ ] Provide output of `pytest` testing the log endpoints.
- [ ] Provide `curl` output of a test `POST` to `/api/v1/agents/logs`.
- [ ] Ensure `pywin32` is explicitly mentioned as optional in `agent/README.md`.
