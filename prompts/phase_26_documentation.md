# Phase 26 — Documentation

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
CYBERSHIELD AI — PHASE 26: Documentation

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

Write the documentation needed for your college final year project 
submission. Document what is ACTUALLY built, not what was planned.

=======================================================================
DOCUMENTS TO CREATE / UPDATE
=======================================================================

1. docs/INSTALLATION.md
   Step-by-step guide for setting up the project locally:
   - Clone the repo
   - Backend setup (Python, venv, pip install, .env, alembic migrate)
   - Agent setup (pip install, .env, enroll)
   - Frontend setup (npm install, .env, npm run dev)
   - First login instructions

2. docs/USER_MANUAL.md
   How to use the system from an end-user perspective:
   - How to log in
   - How to register an agent
   - How to run a discovery scan (with authorization warning)
   - How to run a vulnerability scan
   - How to investigate an alert
   - How to use the AI explanation feature
   - How to generate a report
   - How to manage users (Admin only)

3. docs/ARCHITECTURE.md (update the existing one)
   Update to reflect what was actually built:
   - Final system architecture diagram (use Mermaid)
   - Backend module structure
   - Agent module structure
   - Database tables (the 25 tables)
   - How data flows: Agent → Backend → DB → Frontend

4. docs/API_REFERENCE.md
   A simple summary of all live API endpoints grouped by category.
   For each endpoint: method, path, auth required, who can access it,
   brief description.

5. docs/TEST_RESULTS.md
   From Phase 23: paste the final pytest output and the integration 
   test checklist results.

6. Update README.md (root level)
   - Project description (1 paragraph)
   - Tech stack
   - Live demo URL (Vercel frontend)
   - Quick start (how to run locally in 5 steps)
   - Screenshots (take real screenshots of the working system)

=======================================================================
SCREENSHOTS TO TAKE
=======================================================================

Take real screenshots from the live system and save to docs/screenshots/:
  - Login page
  - Dashboard with real data
  - Agents page (agent showing ONLINE)
  - Devices page (discovered devices)
  - Vulnerabilities page (CVEs listed)
  - Alerts page (with a BruteForce alert)
  - AI explanation window
  - A downloaded PDF report

These screenshots go in your college report and in the README.

=======================================================================
DO NOT DO
=======================================================================

Do not document features that were not implemented.
Do not copy-paste from the SRS as if it were the implementation.
Write what actually works.

=======================================================================
COMMIT MESSAGE
=======================================================================
"docs: Phase 26 — complete project documentation and screenshots"
```
