# Phase 20 — Reports

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

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
  - Admin/Analyst only.
  - Body: { "type": "security_overview", "from_date": "...", 
            "to_date": "..." }
  - Generates the report, saves it to the reports table 
    with status = "ready".
  - Returns: { "report_id": "uuid", "status": "ready" }

GET /api/v1/reports/
  - Admin/Analyst only.
  - Returns list of generated reports.

GET /api/v1/reports/{id}/download
  - Admin/Analyst only.
  - Returns the report as a file download.
  - Support both PDF (using reportlab or fpdf2) and CSV.
  - Use query param: ?format=pdf or ?format=csv
  - Default format: PDF.

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
