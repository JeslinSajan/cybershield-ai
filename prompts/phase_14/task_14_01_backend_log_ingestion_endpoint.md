# Task: 14.1 — Backend Log Ingestion Endpoint

## Objective
Implement `POST /api/v1/agents/logs` in `backend/app/api/v1/agents.py` allowing authenticated agents to ingest security/auth logs with validation, severity mapping, device resolution, and database persistence into the `logs` table.

## Context
- Phase: 14 — Log Management
- Master Plan: `prompts/phase_14/master.md`
- Progress Tracker: `prompts/phase_14/progress.md`
- Standards: `prompts/00_shared_standards.md`

## Files to Inspect First
- `backend/app/models/log.py` (Log ORM model)
- `backend/app/api/v1/agents.py` (existing agent routes and auth)
- `backend/app/core/deps.py` (`require_agent_credential`)

## What to Implement
1. In `backend/app/api/v1/agents.py`:
   - Create Pydantic schemas:
     - `LogEntryItem`:
       - `source`: str (e.g. "auth.log", "windows_security")
       - `event_type`: str (`login_success` or `login_failure` or custom string)
       - `severity`: Optional[str] = None (if not provided, map: `login_failure` → `medium`, `login_success` → `low`, other → `info`)
       - `message`: str
       - `source_ip`: Optional[str] = None
       - `username`: Optional[str] = None
       - `timestamp`: Optional[datetime] = None (default to current UTC time if omitted)
     - `LogIngestRequest`:
       - `logs`: List[LogEntryItem] (at least 1 item)
   - Add endpoint `POST /agents/logs`:
     - Route placed before dynamic `/{agent_id}` routes.
     - Auth: `agent: Annotated[Agent, Depends(require_agent_credential)]`.
     - Multi-tenancy: sets `organization_id = agent.organization_id`, `agent_id = agent.id`.
     - Device linking: if a device exists in `agent.organization_id` matching `agent.id` or `source_ip`, associate `device_id`.
     - Severity auto-mapping when missing or invalid:
       - `login_failure` → `"medium"`
       - `login_success` → `"low"`
       - other → `"info"`
     - Inserts rows into `logs` table.
     - Returns 201 Created with:
       ```json
       {
         "ingested_count": int,
         "log_ids": [str]
       }
       ```
2. In `docs/api/agent-api.md`:
   - Add `POST /agents/logs` documentation under the Agent Credential endpoints section.
3. In `tests/test_logs.py`:
   - Create test suite testing `POST /api/v1/agents/logs`:
     - Successful ingestion of single and batch logs.
     - Automatic severity mapping (`login_failure` -> `medium`, `login_success` -> `low`).
     - Validation: reject invalid payload or empty list with 422.
     - Authentication: reject unauthenticated or user-JWT with 401 `AGENT_NOT_AUTHORIZED`.
     - Multi-tenant verification: logs store `organization_id` of the agent.

## What NOT to Implement
- Do NOT implement human user log query endpoints `GET /logs/` in this task (Task 14.2).
- Do NOT implement agent log collection scripts in this task (Task 14.3).

## Testing
Run pytest:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/test_logs.py -v --tb=short
```

## Completion Criteria
- [ ] `POST /api/v1/agents/logs` implemented and handles batch log ingestion.
- [ ] Severity mapping works as required (`login_failure` → `medium`, `login_success` → `low`).
- [ ] Documented in `docs/api/agent-api.md`.
- [ ] Tests pass in `tests/test_logs.py`.
- [ ] `prompts/phase_14/progress.md` updated.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Task 14.2.
Output a short summary and wait for user instruction.
