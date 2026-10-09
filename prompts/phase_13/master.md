# Phase 13 — Vulnerability Scanning

**Status:** Done  

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
Phase 10: `POST /agents/results` working, `upload_id` idempotency; Phase 11: `Device` rows in DB; `CVE`, `Vulnerability` models from migration 001

## PRODUCES
`Vulnerability` rows in DB; `backend/data/cve_seed.json` (15 CVEs); `GET /vulnerabilities/`, `GET /vulnerabilities/{id}`, `GET /devices/{id}/vulnerabilities` endpoints

**Consumed by:** Phase 15 (detection rules use severity), Phase 16/17 (risk), Phase 19 (AI explanation), Phase 21 (vuln UI)

## HANDOFF REQUIREMENT
On completing this phase, append an entry to `prompts/HANDOFF.md`.
Append CVE matching logic (column names `affected_service`/`affected_version`), Vulnerability insert payload, and scan result `result_type='services'` to `prompts/HANDOFF.md`.

---
## Prompt

```text
CYBERSHIELD AI — PHASE 13: Vulnerability Scanning

Scope:
1. Agent Updates: The agent runs nmap -sV on target IP to detect open ports and service versions.
   Picks up tasks via GET /agents/tasks and posts results to POST /agents/results with result_type="services".
2. Backend Processing:
   - When result is uploaded, store scan_results row (result_type='services').
   - Extract service names and versions, matching them against the cves table using affected_service and affected_version (substring match).
   - If matched, create rows in the Vulnerability table (cve_id FK points to cves.id UUID).
   - Deduplication: Skip creating Vulnerability row if same device_id + cve_id already has status='open'.
3. Endpoints:
   - GET /api/v1/vulnerabilities/ (Role: get_any_authenticated_user)
   - GET /api/v1/vulnerabilities/{id} (Role: get_any_authenticated_user)
   - GET /api/v1/devices/{device_id}/vulnerabilities (Role: get_any_authenticated_user)
4. Seed Data:
   - backend/data/cve_seed.json with 10-15 realistic entries (is_demo_data=True). Seed on startup if cves table is empty.
```
