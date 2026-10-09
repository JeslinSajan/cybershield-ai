# Phase 14 — Log Management

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
> **Standards:** Follow [`prompts/00_shared_standards.md`](../00_shared_standards.md) — all S1–S9 rules apply to this phase.

---

## DEPENDS ON
Phase 9/10: `require_agent_credential()`, agent running; `logs` table from migration 001 (`models/log.py`).

## PRODUCES
- `Log` rows in DB
- `POST /api/v1/agents/logs` endpoint (Agent Credential auth)
- `GET /api/v1/logs/` & `GET /api/v1/logs/{id}` endpoints (JWT, all 3 roles)
- `agent/collectors/log_collector.py` (Linux auth.log + Windows Security Event Log with safe fallback)
- Integration into `agent/main.py`
- Documentation in `docs/api/agent-api.md`, `docs/api/log-api.md`, and `agent/README.md`

**Consumed by:** Phase 15 (brute force / suspicious login rules), Phase 18 (indicator matching), Phase 21 (logs UI)

---

## Task Plan

| Task ID | Task Title | Description | Target Files |
|---|---|---|---|
| 14.1 | Backend Log Ingestion Endpoint | Implement `POST /api/v1/agents/logs` with agent credential auth, severity mapping, validation, and documentation | `backend/app/api/v1/agents.py`, `docs/api/agent-api.md`, `tests/test_logs.py` |
| 14.2 | Backend Log Query Endpoints | Implement `GET /api/v1/logs/` with filters (event_type, source, severity, date range, pagination) and `GET /api/v1/logs/{id}` | `backend/app/api/v1/logs.py`, `docs/api/log-api.md`, `tests/test_logs.py` |
| 14.3 | Agent Log Collector Module | Implement `agent/collectors/log_collector.py` (Linux auth.log, Windows Event Log with graceful fallback, state tracking), update `agent/main.py` and `agent/README.md` | `agent/collectors/log_collector.py`, `agent/main.py`, `agent/README.md`, `tests/test_agent_log_collector.py` |
| 14.4 | Log Management Integration & Verification | End-to-end integration test, full regression suite, handoff documentation, phase completion | `tests/test_logs.py`, `prompts/HANDOFF.md`, `prompts/phase_14/progress.md`, `prompts/phase_14/master.md`, `prompts/phase_14_log_management.md` |
