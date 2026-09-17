# Phase 18 — Threat Intelligence

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

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
  - Admin/Analyst only.
  - Add a new indicator: { type, value, description, severity }

GET /api/v1/threat-intelligence/
  - All roles (read).
  - Returns all indicators with: id, type, value, description, 
    severity, created_at.
  - Filter by: ?type=ip&severity=High

GET /api/v1/threat-intelligence/{id}
  - All roles.

DELETE /api/v1/threat-intelligence/{id}
  - Admin only.

=======================================================================
INDICATOR MATCHING
=======================================================================

Add a check in the log save handler:
  - When a log entry has a source_ip: check if it matches any 
    threat_indicators row with type = "ip".
  - If matched: create a "Malware Indicator" alert with:
      severity = indicator.severity,
      description = "Log from known malicious IP: <ip>. 
                     Indicator: <indicator.description>",
      source_ip = the matched IP.

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
