---START HEADER---
# Phase 22 — Security Hardening

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
Fix 6 specific security issues. No enterprise overkill.

#### 1. RATE LIMITING on POST /auth/login only
Use slowapi==0.1.9. Add to backend/requirements.txt with this exact pin.
Limit: 10 requests per minute per IP.
On exceed: 429 Too Many Requests with error envelope:
`{"error": {"code": "RATE_LIMITED", "message": "Too many requests. Try again later.", "details": []}}`
Add the slowapi Limiter to main.py and add SlowAPIMiddleware.

#### 2. SECURE RESPONSE HEADERS via FastAPI middleware
Add to main.py:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

#### 3. CORS
Review CORS_ORIGINS in production .env.
In production: CORS_ORIGINS must be the Vercel URL only, never "*".
Confirm main.py already handles this (it does via settings.CORS_ORIGINS).
Add a note in backend/.env.example: `# PRODUCTION: set to https://your-vercel-url.vercel.app`

#### 4. ORGANIZATION ISOLATION AUDIT
Check EVERY list endpoint (GET /devices/, GET /alerts/, GET /logs/, etc.).
Every query must filter by organization_id from the JWT user's organization.
How to get org_id: user.organization_id (loaded from DB in get_current_user).
If any endpoint is missing the org filter: add it now.
Test: create 2 organizations with separate users. Confirm user A cannot see user B's data.

#### 5. ERROR MESSAGES in production
In the general exception handler in main.py (already exists):
Confirm it returns INTERNAL_SERVER_ERROR code with no stack trace.
Add check: if settings.DEBUG is True, include exc details in response (dev only).
In production (ENVIRONMENT=production), never expose exception details.

#### 6. AUDIT LOG COMPLETENESS
Confirm these actions write to audit_logs (AuditLog model: organization_id, actor_type, actor_id, action, target_type, target_id, details (JSONB), created_at):
- User login: action='user_login'
- Failed login: action='user_login_failed'
- Agent enrolled: action='agent_enrolled'
- Agent revoked: action='agent_revoked'
- Scan created: action='scan_created'
- Alert status changed: action='alert_status_changed'
- Report generated: action='report_generated'
For any missing: add the AuditLog write now.

### Required Verification Checklist:
- [ ] POST /auth/login 11x rapidly → paste 429 response.
- [ ] GET any response → confirm X-Content-Type-Options header present.
- [ ] Create 2 orgs, confirm data isolation.
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
