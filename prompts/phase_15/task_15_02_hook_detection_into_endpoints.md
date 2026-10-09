# Task: 15.2 — Hook Detection Engine into Ingestion Endpoints

## Objective
Hook `detection_service.process_log_detections` and `detection_service.process_scan_detections` synchronously into `POST /api/v1/agents/logs` and `POST /api/v1/agents/results` in `backend/app/api/v1/agents.py`.

## Context
- Phase: 15 — Threat Detection
- Master Plan: `prompts/phase_15/master.md`
- Progress Tracker: `prompts/phase_15/progress.md`
- Standards: `prompts/00_shared_standards.md`

## Files to Inspect First
- `backend/app/api/v1/agents.py`
- `backend/app/services/detection_service.py`

## What to Implement
1. In `backend/app/api/v1/agents.py`:
   - In `POST /agents/logs`:
     - After logs are created and flushed/committed to database, call:
       `process_log_detections(db, org_id=agent.organization_id, agent_id=agent.id, logs=created_log_objects)`
   - In `POST /agents/results`:
     - When `result_type == "services"`:
       - After vulnerabilities are processed, call:
         `process_scan_detections(db, org_id=agent.organization_id, agent_id=agent.id, scan_result=result_row)`
2. Ensure all exceptions during detection are handled gracefully so log and scan ingestion never fail due to alert processing issues.

## Completion Criteria
- [ ] Log ingestion triggers log detection rules synchronously.
- [ ] Scan result ingestion triggers scan detection rules synchronously.
- [ ] Tests in `tests/test_logs.py` and `tests/test_vulnerabilities.py` pass without regression.
- [ ] `prompts/phase_15/progress.md` updated.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Task 15.3.
Output a short summary and wait for user instruction.
