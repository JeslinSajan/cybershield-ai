# Phase 24 — Deployment

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*
---

> **STANDING RULE — VERIFY BEFORE EXECUTING**
> Before running this prompt, re-read the actual current state of the repo:
> (1) Check which backend endpoints already exist in backend/app/api/v1/.
> (2) Check which Alembic migrations have already been run (alembic current).
> (3) Check which tests already exist in tests/.
> (4) If the real repo state differs from what this prompt assumes — update
>     this prompt file FIRST, then execute it. Prompts are a living plan,
>     not a frozen snapshot.

---

## Prompt

```text
CYBERSHIELD AI — PHASE 24: Deployment

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

Deploy the complete system so it is accessible live.

Hosting:
  Frontend  → Vercel
  Backend   → Render
  Database  → Neon PostgreSQL

The agent runs locally on the demo machine (your laptop/PC).

=======================================================================
STEP 1 — BACKEND (Render)
=======================================================================

The backend is already deployed to Render. In this phase:

1. Confirm ALL 25 tables exist in Neon by running Alembic migrations.
   In Render's Shell tab (or local with Neon DATABASE_URL):
     alembic upgrade head
   Confirm output shows "Running upgrade ... -> <latest>".
   If any migrations are missing (new tables from Phases 9-22): 
   create them now and push before deploying.

2. Run the seed script to create initial roles + admin user:
     python -m app.core.seed
   (Only needed on first deploy or if database is wiped)

3. Make sure all Render environment variables are set:
     DATABASE_URL
     JWT_SECRET_KEY      (strong random key — not the dev default)
     ENVIRONMENT         = production
     DEBUG               = False
     CORS_ORIGINS        = https://<your-vercel-url>
     AGENT_OFFLINE_TIMEOUT_SECONDS = 90
     LOG_LEVEL           = INFO

4. Verify: GET https://cybershield-ai-xnn7.onrender.com/api/v1/health
   Must return: {"status": "healthy"}

5. Verify: GET /api/v1/health/db
   Must return: {"status": "healthy", "database": "connected"}

=======================================================================
STEP 2 — FRONTEND (Vercel)
=======================================================================

1. Connect the GitHub repo to Vercel if not already done.

2. Set environment variable in Vercel:
     VITE_API_BASE_URL = https://cybershield-ai-xnn7.onrender.com

3. Set build settings:
     Framework: Vite
     Root directory: frontend
     Build command: npm run build
     Output directory: dist

4. Deploy. Verify the login page loads and you can log in with 
   the seeded admin account.

=======================================================================
STEP 3 — AGENT (Local)
=======================================================================

The agent does not need cloud deployment — it runs on the customer's 
machine. For the demo, it runs on your laptop.

Create agent/INSTALL.md explaining:
  1. Install Python 3.12+
  2. Install Nmap (https://nmap.org/download.html)
  3. pip install -r requirements.txt
  4. Copy .env.example to .env
  5. Fill in BACKEND_URL and ENROLLMENT_TOKEN
  6. Run: python main.py

=======================================================================
STEP 4 — NEON DATABASE
=======================================================================

Confirm all 25 tables exist in Neon:
  Run: alembic current
  Should show the latest migration is applied.

If not: run alembic upgrade head against Neon.

=======================================================================
VERIFY EVERYTHING IS LIVE
=======================================================================

1. Open the Vercel URL in a browser.
2. Login with the seeded admin account.
3. Open a second terminal — start the agent pointing to 
   the PRODUCTION backend URL.
4. In the dashboard — confirm the agent appears as ONLINE.
5. Run a discovery scan from the UI.
6. Confirm devices appear in the Devices page.
7. Download a report as PDF.

Document the live URLs in docs/PHASE24_DEPLOYMENT.md.

=======================================================================
COMMIT MESSAGE
=======================================================================
"docs: Phase 24 — deployment verification and live system URLs"
```
