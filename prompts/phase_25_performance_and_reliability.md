---START HEADER---
# Phase 25 — Performance & Reliability

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> This prompt was written before execution. Before running it:  
> (1) Run `alembic current` — confirm which migrations are applied.  
> (2) Check `backend/app/api/v1/` — note which endpoints already exist (stubs).  
> (3) Check `tests/` — note which test files already exist.  
> (4) If reality differs from this prompt's assumptions, update this file first.  
> Prompts are a living plan, not a frozen snapshot.

---

## Prompt
---END HEADER---

### Scope
Targeted, minimal changes to ensure demo stability. No premature optimization.

#### 1. MISSING INDEXES
Check these queries via EXPLAIN ANALYZE in Neon's SQL editor:
- alerts filtered by organization_id + status
- logs filtered by organization_id + timestamp
- agent_heartbeats filtered by agent_id + timestamp
If doing a full table scan: create an Alembic migration adding the index.
Do not add indexes speculatively — only for confirmed slow queries.

#### 2. PAGINATION on all list endpoints
Every GET list endpoint must support: `?limit=50&offset=0` (default limit=50, max=200)
Check these endpoints and add limit/offset if missing:
`GET /devices/, GET /alerts/, GET /logs/, GET /vulnerabilities/, GET /agents/, GET /threat-intelligence/, GET /reports/`

#### 3. HEARTBEAT CLEANUP (prevent agent_heartbeats table from growing unbounded)
Add a background task to main.py lifespan that runs once daily:
`DELETE FROM agent_heartbeats WHERE created_at < now() - interval '7 days'`
Wrap in try/except — failure must not crash the backend.
Log: "Heartbeat cleanup: deleted N rows older than 7 days."
math: 2880 heartbeats/agent/day x 7 days = ~20k rows per agent max.

#### 4. AGENT STARTUP RETRY
If backend unreachable at agent startup:
Retry every 30 seconds up to 10 times before giving up.
Log: "Backend not reachable. Retry N/10 in 30s..."
After 10 failures: log "Backend unreachable after 10 retries. Exiting." and `exit(1)`.

#### 5. FRONTEND AUTO-REFRESH
Verify from Phase 21:
Dashboard auto-refreshes every 60s (setInterval).
Agents page auto-refreshes every 30s.
If not implemented: add it now.
Add loading spinner on every data fetch (check all pages).
Add error message on API failure (e.g., "Could not load devices. Check your connection.").

### Required Verification Checklist:
- [ ] Start agent BEFORE backend → paste agent logs showing retry behavior.
- [ ] GET /api/v1/logs/?limit=10 → confirm only 10 rows returned.
- [ ] pytest tests/ -v — 0 regressions.

### System Standing Rules Reminders:
- Local-first: LocalRuleAI only, no external AI API ever.
- Vercel + Render + Neon. No Docker Compose.
- Never log secrets at any log level (DATABASE_URL, JWT_SECRET, agent credentials, passwords).
- Pin every new dependency version explicitly.
- Every endpoint traces to a FR in docs/srs/functional-requirements.md.
- Check docs/api/*.md — new endpoints must be documented first.
- Run alembic current before assuming tables exist.
- Never force-push.
- Verification checklist requires actual evidence (pytest output, curl).
- Error Envelope: `{"error": {"code": "...", "message": "...", "details": []}}`
- RBAC dependencies: `get_current_admin`, `get_current_analyst_or_admin`, `get_any_authenticated_user`
