# Phase 20 — Reports

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> This prompt was written before execution. Before running it:
> (1) Run `alembic current` — confirm which migrations are applied.
> (2) Check `backend/app/api/v1/` — note which endpoints already exist.
> (3) Check `tests/` — note which test files already exist.
> (4) If reality differs from this prompt's assumptions, update this file first, then execute.
> Prompts are a living plan, not a frozen snapshot.

---

## Prompt

**Scope:**
1. **Dependencies**:
   - Add `fpdf2==2.7.9` to `backend/requirements.txt` (Verify Python 3.12 compatibility).
   - Use standard library `csv` module for CSV reports.
2. **Endpoints (in backend/app/api/v1/reports.py)**:
   - `POST /reports/`: Role: `get_current_analyst_or_admin`. 
     - Body: `{type: str, from_date: str (ISO), to_date: str (ISO)}`. Valid types: 'security_overview', 'vulnerability', 'alert'.
     - Create `Report` row (columns: `id`, `organization_id`, `created_by_user_id`, `report_type`, `period_start`, `period_end`, `file_name`, `mime_type`, `status`='READY', `created_at`, `updated_at`).
     - Write `AuditLog`: `actor_type`='user', `actor_id`=user.id, `action`='report_generated'.
   - `GET /reports/`: Role: `get_any_authenticated_user` (Viewers can view reports).
   - `GET /reports/{id}/download?format=pdf`: Role: `get_current_analyst_or_admin` (Viewers cannot download).
     - PDF Generation: Include CyberShield AI header, report title, date range, table data using `fpdf2`.
     - CSV Generation: using `csv`.
     - Save in `backend/generated_reports/`. Return `FileResponse`.
3. **Documentation**: Update `docs/api/` as needed.

**Rules & Constraints:**
- Pin dependencies explicitly.
- Use actual RBAC logic: `get_any_authenticated_user`, `get_current_analyst_or_admin`.
- Follow exact `AuditLog` format.
- Adhere to the error envelope format.

**Verification Checklist:**
- [ ] Provide output of `curl POST /reports/` triggering generation.
- [ ] Provide output verifying a PDF or CSV file is successfully returned by the download endpoint.
