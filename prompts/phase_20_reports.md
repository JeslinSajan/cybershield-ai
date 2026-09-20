# Phase 20 — Reports

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
CYBERSHIELD AI — PHASE 20: Reports

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

Allow Admins and Analysts to generate a security report and 
download it as a PDF or CSV. This is a key demo feature for 
your final year presentation.

=======================================================================
REPORT TYPES (build all 3 for a good demo)
=======================================================================

1. Security Overview Report
   Contains: Online agents, total devices, open vulnerabilities 
   count by severity, open alerts count by severity, average 
   risk score across all devices, time period.

2. Vulnerability Report
   Contains: List of all vulnerabilities with device, CVE ID, 
   severity, description, and recommendation.

3. Alert Report
   Contains: List of all alerts with type, severity, device, 
   source IP, status, and created date.

=======================================================================
BACKEND ENDPOINTS
=======================================================================

POST /api/v1/reports/
  - Administrator and Analyst only (Viewer gets 403 to generate).
  - Body: { 
      "type": "security_overview",   ← valid: security_overview, vulnerability, alert
      "from_date": "2026-09-01T00:00:00Z",
      "to_date": "2026-09-17T23:59:59Z"
    }
  - Map to schema columns (table 20):
      organization_id (from JWT),
      created_by_user_id (from JWT),
      report_type = type from body,
      period_start = from_date,
      period_end = to_date,
      status = "READY"
  - After saving, write audit_log entry:
      action = "report_generated", actor_type = "user",
      target_type = "reports", target_id = <report id>
  - Returns: { "report_id": "uuid", "status": "READY" }

GET /api/v1/reports/
  - Administrator, Analyst, AND Viewer (Viewer can VIEW reports).
  - Returns list of generated reports with type, period, status.

GET /api/v1/reports/{id}/download
  - Administrator and Analyst only (Viewer gets 403 to download).
  - Returns the report as a file download.
  - Support: ?format=pdf or ?format=csv. Default: pdf.

=======================================================================
PDF GENERATION
=======================================================================

Use the fpdf2 library (pip install fpdf2) — it is simple, 
lightweight, and has no external dependencies.

The PDF should include:
  - CyberShield AI logo/header (text is fine if no image)
  - Report title and generated date
  - Time period covered
  - Data in a clean table format
  - Summary totals at the top

Add fpdf2 to backend/requirements.txt.

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. POST /reports/ with type=security_overview.
2. GET /reports/{id}/download?format=pdf — open the PDF and confirm 
   it contains real data.
3. GET /reports/{id}/download?format=csv — open in Excel/Sheets 
   and confirm data is correct.
4. A Viewer trying POST /reports/ — confirm 403.
5. pytest tests/ — no regressions.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 20 — security report generation with PDF and CSV download"
```
