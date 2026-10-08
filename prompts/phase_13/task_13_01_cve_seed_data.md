# Task: 13.1 — CVE Seed Data and Startup Loader

## Objective
Create `backend/data/cve_seed.json` with 12-15 realistic CVE records and implement idempotent CVE seeding in `backend/app/core/seed.py` invoked during startup.

## Context
- Phase: 13 — Vulnerability Scanning
- Master Plan: prompts/phase_13/master.md
- Progress Tracker: prompts/phase_13/progress.md
- Standards: prompts/00_shared_standards.md

## Files to Inspect First
- `backend/app/models/scan.py` (CVE class)
- `backend/app/core/seed.py`
- `backend/app/main.py`

## What to Implement
1. Create `backend/data/cve_seed.json` containing 12-15 realistic CVE objects:
   - Fields: `cve_id`, `severity` (Critical, High, Medium, Low), `cvss_score`, `affected_service`, `affected_version`, `summary`, `recommendation`, `source`, `is_demo_data`.
2. In `backend/app/core/seed.py`:
   - Implement `seed_cves(db: Session, organization_id: uuid.UUID) -> int`:
     - Reads `backend/data/cve_seed.json`.
     - Checks if `CVE` table already has entries for the given `organization_id`.
     - If empty, inserts the seed CVEs and commits.
     - Returns number of seeded records.
3. In `backend/app/main.py`:
   - Invoke `seed_cves` during lifespan startup using the default seeded organization.
4. In `tests/test_vulnerabilities.py`:
   - Add unit tests verifying `seed_cves` creates records and is idempotent on repeat execution.

## What NOT to Implement
- Do NOT implement vulnerability scanning or agent code in this task.
- Do NOT implement vulnerability HTTP routes yet.

## Constraints
- Safe startup: Seeding failure must be logged as warning/error without preventing backend startup.
- Never hardcode database credentials.

## Testing
Run pytest:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/test_vulnerabilities.py -v --tb=short
```

## Completion Criteria
- [ ] `backend/data/cve_seed.json` created with 12-15 CVEs.
- [ ] `seed_cves()` inserts CVE records when table is empty.
- [ ] Repeat calls to `seed_cves()` do not duplicate rows.
- [ ] Tests pass in `tests/test_vulnerabilities.py`.
- [ ] `prompts/phase_13/progress.md` updated.

## Progress Update
Update `prompts/phase_13/progress.md` with:
- Task 13.1 status set to `Completed`.
- Files changed.
- Test outcome.
- Next task set to `13.2`.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Task 13.2.
Output a short summary and wait for user instruction.
