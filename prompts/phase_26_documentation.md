---START HEADER---
# Phase 26 — Documentation

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
Write documentation that reflects what is ACTUALLY built, not what was planned.
Do not copy from the SRS as if it were implementation truth.

Create/update these documents:

#### 1. docs/INSTALLATION.md
Backend: Python 3.12, venv, pip install -r requirements.txt, alembic upgrade head, uvicorn.
Agent: pip install -r agent/requirements.txt, .env setup, python main.py.
Frontend: npm install, .env setup, npm run dev.
First login: how to get admin credentials.

#### 2. docs/USER_MANUAL.md
How to: login, register an agent, run discovery scan (with authorization warning), run vulnerability scan, investigate an alert, use AI explanation, generate a report, manage users (Admin only).

#### 3. docs/ARCHITECTURE.md
Update existing file to reflect what was actually built.
Include a Mermaid architecture diagram:
- Agent → Backend (HTTPS) → Neon Postgres
- User Browser → Vercel Frontend → Backend (HTTPS)
List: backend module structure, agent module structure, 25 DB tables summary.

#### 4. docs/API_REFERENCE.md
Summary of all live endpoints grouped by category (Agents, Devices, Scans, Vulnerabilities, Logs, Alerts, Threat Intelligence, Reports, AI, Settings, Auth).
For each: method, path, auth required, who can access, brief description.
This is a human-readable summary, NOT a replacement for docs/api/*.md files.

#### 5. docs/TEST_RESULTS.md
Copy from Phase 23 `PHASE23_TEST_RESULTS.md`.

#### 6. README.md (root level)
1-paragraph project description.
Tech stack table.
Live demo URL (Vercel).
Quick start: 5 steps to run locally.
Screenshots: embed real screenshots from docs/screenshots/.
Badge for build status (optional).

### Screenshots to take (save to docs/screenshots/):
- `login_page.png`
- `dashboard.png`
- `agents_page.png`
- `devices_page.png`
- `vulnerabilities_page.png`
- `alerts_page.png`
- `ai_explanation.png`
- `report_pdf.png`

### Required Verification Checklist:
- [ ] All specified markdown files are updated and reviewed.
- [ ] Screenshots are placed in `docs/screenshots/`.
- [ ] README.md has correct links to live demo and screenshots embedded.

### System Standing Rules Reminders:
- Local-first: LocalRuleAI only, no external AI API ever.
- Vercel + Render + Neon. No Docker Compose.
- Never log secrets at any log level.
- Pin every new dependency version explicitly.
- Every endpoint traces to a FR in docs/srs/functional-requirements.md.
- Check docs/api/*.md — new endpoints must be documented first.
- Run alembic current before assuming tables exist.
- Never force-push.
- Verification checklist requires actual evidence (pytest output, curl).
