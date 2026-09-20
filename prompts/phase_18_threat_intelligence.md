# Phase 18 — Threat Intelligence

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
CYBERSHIELD AI — PHASE 18: Threat Intelligence

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

A simple local database of known bad IPs, domains, and file hashes.
When the agent sends logs or results, the backend checks them against 
this list and creates alerts if a match is found.

=======================================================================
INDICATOR TYPES
=======================================================================

  ip      — A known malicious IP address (e.g. "185.234.219.33")
  domain  — A known malicious domain (e.g. "evil-malware.ru")
  hash    — A known malicious file hash (MD5/SHA256)

=======================================================================
BACKEND ENDPOINTS
=======================================================================

POST /api/v1/threat-intelligence/
  - Administrator and Analyst only (Viewer gets 403).
  - Add a new indicator.
  - Use EXACT column names from schema (table 16):
      organization_id (from JWT), indicator_type, value, 
      description, source (default: "local")
  - Valid indicator_type values: "ip", "domain", "hash"
  - Returns the created indicator.

GET /api/v1/threat-intelligence/
  - Admin, Analyst, AND Viewer (all roles can read — per user-roles.md).
  - Returns all indicators with: id, indicator_type, value, 
    description, source, created_at.
  - Filter by: ?indicator_type=ip

GET /api/v1/threat-intelligence/{id}
  - All roles.

DELETE /api/v1/threat-intelligence/{id}
  - Administrator only.

=======================================================================
INDICATOR MATCHING
=======================================================================

Add a check in the log save handler:
  - When a log entry has a source_ip: check if it matches any 
    threat_indicators row where indicator_type = "ip" 
    AND value = source_ip (exact match).
  - If matched: create a "malware_indicator" alert 
    (use exact alert_type value from schema) with:
      severity = "High",
      description = "Log entry received from known malicious IP: <ip>. 
                     Indicator description: <indicator.description>",
      risk_score = 40 (Phase 17 will refine)
      triggered_at = now()

=======================================================================
SEED DATA
=======================================================================

On backend startup (only if threat_indicators table is empty), 
seed 5–10 example indicators for the demo:
  - A few fake malicious IPs.
  - A couple of known bad domains.
  - One or two example hashes.

This gives the demo something to show without needing real threat feeds.

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Add a test indicator via POST /threat-intelligence/.
2. Submit a log entry with that indicator's IP as source_ip.
3. Confirm a "Malware Indicator" alert is created.
4. GET /threat-intelligence/ — confirm indicator list is returned.
5. pytest tests/ — no regressions.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 18 — local threat intelligence with indicator matching"
```
