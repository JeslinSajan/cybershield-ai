---START HEADER---
# Phase 27 — Final Demonstration & Submission

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
Pre-demo checklist, demo script, viva Q&A prep, git tag.

### PRE-DEMO CHECKS (do the day before):
- [ ] Open live Vercel URL — click every page, fix any broken ones.
- [ ] Start agent against production backend — confirm ONLINE in dashboard.
- [ ] `pytest tests/ -v` — 0 failures. Paste output.
- [ ] `GET /api/v1/health` and `/health/db` — both return healthy.
- [ ] `git status` — clean working tree, no uncommitted changes.

### DEMO SCRIPT (practice until smooth, ~10 minutes):
1. Open live web app — show login page.
2. Login as Administrator — show Dashboard with real counts.
3. Agents page — point to the agent running on your laptop (status=ONLINE).
4. Devices page — show discovered devices from the Nmap scan.
5. Click a device — show device detail.
6. Vulnerabilities page — show CVE matches with severity badges.
7. Alerts page — show the BruteForce alert.
8. Click the alert — change status to Acknowledged. Show the status history timeline below the alert.
9. Click "Explain with AI" — show the local explanation (label: Local Security Explanation Engine).
10. Reports page — generate a report, download as PDF, open it.
11. Threat Intelligence page — show the malicious IP indicators.
12. Logs page — show collected login events.

### GITHUB CLEANUP:
- README.md: add screenshots, live demo link, quick start.
- .gitignore: verify agent_identity.json, *.db, .env, __pycache__, node_modules are excluded.
- Tag the final version:
  ```bash
  git tag v1.0.0
  git push origin v1.0.0
  ```
  Do NOT force-push the tag if it already exists.

### VIVA Q&A PREPARATION:

**Q: Why FastAPI over Django or Flask?**
A: FastAPI has built-in async support, Pydantic validation, and auto-generates OpenAPI docs. Better for API-only backends without the overhead of Django's ORM magic.

**Q: Is this real AI? What is the "Local Security Explanation Engine"?**
A: It is rule-based text generation using actual alert/vulnerability data from the DB. Not an LLM. No external API calls. This is deliberate — it works offline, costs nothing, and is fully explainable. The architecture allows swapping in an LLM later.

**Q: Why a standalone agent instead of scanning from the backend?**
A: The agent runs inside the customer's network. The backend (on Render) cannot reach private IPs inside a local network. The agent bridges this gap.

**Q: How is the system secured?**
A: JWT + bcrypt for users, separate SHA-256 token auth for agents, RBAC on every endpoint, organization isolation, audit logging, no secrets ever logged.

**Q: What would you add with more time?**
A: Real-time WebSocket alerts, email notifications, ML-based anomaly detection, support for more log sources (syslog, Windows Event Log), mobile app.

### FINAL COMMIT:
```bash
git commit -m "chore: Phase 27 — demo prep, final cleanup, v1.0.0 tag"
git push && git push origin v1.0.0
```

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
