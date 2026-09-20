---START HEADER---
# Phase 24 — Deployment

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
Hosting: Vercel (frontend) + Render (backend) + Neon (Postgres). NOT Docker Compose.

#### Step 1: Verify ALL database migrations
Run locally with Neon DATABASE_URL:
`alembic upgrade head`
Confirm all tables exist. If any are missing from phases 9-22: add migrations now.
DO NOT deploy to Render until this is confirmed locally against Neon.

#### Step 2: Backend environment variables on Render
- `DATABASE_URL` (Neon connection string)
- `JWT_SECRET_KEY` (strong random key, min 32 chars)
- `ENVIRONMENT = production`
- `DEBUG = False`
- `CORS_ORIGINS = https://<your-vercel-url>.vercel.app`
- `AGENT_OFFLINE_TIMEOUT_SECONDS = 90`
- `LOG_LEVEL = INFO`
- `SEED_ADMIN_EMAIL` (first admin account)
- `SEED_ADMIN_PASSWORD` (strong password, never logged)
NEVER log these values. Confirm backend logs do not print them.

#### Step 3: Render deploy
`render.yaml` must have `runtimeVersion` field.
`backend/.python-version` file must exist and contain `3.12.7`.
(This was the fix from Phase 7 that resolved the pydantic-core build failure. Do not remove this file. Do not change the version.)
Verify live: GET https://cybershield-ai-xnn7.onrender.com/api/v1/health
Must return: `{"status": "healthy"}`
Also verify: GET /api/v1/health/db → `{"status": "healthy", "database": "connected"}`

#### Step 4: Frontend on Vercel
Set `VITE_API_BASE_URL = https://cybershield-ai-xnn7.onrender.com` in Vercel env vars.
Build: Framework=Vite, Root=frontend, Build command=npm run build, Output=dist.
Verify: login page loads, real JWT returned, Dashboard shows live data.

#### Step 5: Agent (runs locally, not deployed)
Update `agent/.env`: `BACKEND_URL = https://cybershield-ai-xnn7.onrender.com`
Generate enrollment token via production API.
Start agent → confirm ONLINE in production dashboard.

Document live URLs in `docs/PHASE24_DEPLOYMENT.md`.

### Required Verification Checklist:
- [ ] Live health endpoints return 200 (paste actual responses).
- [ ] Login with production admin account works.
- [ ] Agent enrolls and sends heartbeat to production backend.
- [ ] Discovery scan runs end-to-end in production.
- [ ] PDF report downloads successfully from live URL.

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
