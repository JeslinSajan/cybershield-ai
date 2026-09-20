---START HEADER---
# Phase 23 — Testing

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
Complete the test suite so all features have test coverage.

### Existing test files (from Phase 7/8 — DO NOT DELETE OR MODIFY):
- `tests/test_backend_foundation.py`
- `tests/test_auth.py`
- `tests/test_rbac.py`

### Create these test files if missing:
- `tests/test_agents.py`        (Phase 9/10)
- `tests/test_devices.py`       (Phase 11)
- `tests/test_vulnerabilities.py` (Phase 13)
- `tests/test_logs.py`          (Phase 14)
- `tests/test_detection.py`     (Phase 15)
- `tests/test_alerts.py`        (Phase 16)
- `tests/test_risk_scores.py`   (Phase 17)
- `tests/test_threat_intelligence.py` (Phase 18)
- `tests/test_ai.py`            (Phase 19)
- `tests/test_reports.py`       (Phase 20)
- `tests/test_notifications.py` (Phase 21)
- `tests/test_audit_logs.py`    (Phase 21)
- `tests/test_settings.py`      (Phase 21/22)

### For EACH test file, at minimum cover:
- Happy path: valid request → expected response + DB side-effect
- Missing auth: no token → 401 with correct error envelope
- Wrong role: valid token, wrong role → 403 with FORBIDDEN code
- Not found: invalid ID → 404 with NOT_FOUND code

### Manual Integration Test
Also run manual integration test and document results in `docs/PHASE23_TEST_RESULTS.md`:
- Step 1: Login as Admin → JWT received
- Step 2: Generate enrollment token → token returned  
- Step 3: Start agent → "Agent enrolled" in logs
- Step 4: Wait 30s → heartbeat appears in agent_heartbeats
- Step 5: GET /agents/ → agent shows ONLINE
- Step 6: Create discovery scan → agent picks it up
- Step 7: GET /devices/ → discovered devices listed
- Step 8: Create vulnerability scan → agent runs nmap -sV
- Step 9: GET /vulnerabilities/ → CVE matches shown
- Step 10: Send 6 login_failure logs from same IP → brute force alert created
- Step 11: PATCH /alerts/{id} → status=Acknowledged
- Step 12: GET /devices/{id}/risk → risk score returned
- Step 13: POST /ai/explain-alert → explanation returned
- Step 14: POST /reports/ → PDF downloadable

### Required Verification Checklist:
- [ ] Final command to paste in `docs/PHASE23_TEST_RESULTS.md`: `pytest tests/ -v --tb=short`
- [ ] Paste the full output. Target: 0 failures.

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
