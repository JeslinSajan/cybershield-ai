---START HEADER---
# Phase 21 — Complete Frontend Integration

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
Full React + TypeScript + Vite + Tailwind CSS frontend, connected to the real backend.
Tech: React 18, TypeScript, Vite, Tailwind CSS. Use axios for API calls. JWT in localStorage.
Base URL: read from env var VITE_API_BASE_URL.

### Pages to build (13 pages):
1. Login — POST /auth/login, store JWT
2. Dashboard — GET /alerts/summary + GET /agents/ + recent alerts. Auto-refresh 60s.
3. Agents — GET /agents/, agent status badge (ONLINE=green/OFFLINE=red/PENDING=yellow).
   Click agent → detail with last heartbeat + health. "Generate Token" (Admin only).
   "Revoke" button (Admin only).
4. Devices — GET /devices/. Click device → detail + vulnerabilities + risk score.
   "Run Discovery Scan" button (Analyst+Admin). Show auth warning dialog before triggering.
5. Vulnerabilities — GET /vulnerabilities/. Filter by severity/device/CVE. Click → full detail + AI explain button.
6. Alerts — GET /alerts/. Filter tabs: All/Open/Acknowledged/Investigating/Resolved.
   Click → detail with status buttons (PATCH /alerts/{id}), history timeline, "Explain with AI".
7. Logs — GET /logs/. Filter by event_type, source, date range.
8. Threat Intelligence — GET /threat-intelligence/. Add indicator form (Analyst+Admin). Delete (Admin only).
9. Reports — GET /reports/. "Generate Report" button (Analyst+Admin). Download PDF/CSV.
10. AI Assistant — Admin+Analyst ONLY (do not show to Viewer). POST /ai/chat.
    Label: "Local Security Explanation Engine".
11. Settings — Admin only. User management + GET/PUT /api/v1/settings/ for system_settings keys.
12. Audit Logs — Admin only. GET /audit-logs/. Filter by action, date range.
13. Notifications bell — all roles. GET /notifications/ (unread count badge). Mark read.

### RBAC in UI:
Get role from GET /auth/me after login. Store in context.
Hide menus/buttons that the user's role cannot access.
Viewer: read-only, no AI Assistant, no Settings, no Audit Logs.

### Error Handling & Loading States:
Error handling: show toast or inline message on every API failure.
Loading states: spinner on every data fetch.
Auto-refresh: Dashboard 60s, Agents page 30s.
Responsive: designed for 1280px+ laptop screens.

### Documentation Update:
Verify frontend API calls match docs/api/*.md contracts.
If a frontend call uses an endpoint not yet in docs/api, add it.

### Required Verification Checklist:
- [ ] Real login with a real JWT (not mock).
- [ ] Dashboard shows real agent + alert counts.
- [ ] Run a scan from the UI — confirm agent picks it up.
- [ ] Change alert status from UI — confirm DB update.
- [ ] Download PDF report from UI — confirm file opens.
- [ ] Viewer role: confirm AI Assistant menu is hidden, Settings is hidden.

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
