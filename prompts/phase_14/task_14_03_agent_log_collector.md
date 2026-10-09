# Task: 14.3 — Agent Log Collector Module

## Objective
Implement `agent/collectors/log_collector.py` to collect auth/security event logs on Linux (`auth.log`) or Windows (Security Event Log) with safe fallback if `pywin32` is not installed, deduplicate using `last_sent_timestamp`, update `agent/main.py`, and document optional Windows dependencies in `agent/README.md`.

## Context
- Phase: 14 — Log Management
- Master Plan: `prompts/phase_14/master.md`
- Progress Tracker: `prompts/phase_14/progress.md`
- Standards: `prompts/00_shared_standards.md`

## Files to Inspect First
- `agent/api_client.py`
- `agent/main.py`
- `agent/config.py`

## What to Implement
1. In `agent/collectors/log_collector.py`:
   - Implement log collector:
     - Detects OS:
       - Linux: reads `/var/log/auth.log` or `/var/log/secure` using regex for ssh/login events (`Failed password` -> `login_failure`, `Accepted password/publickey` -> `login_success`).
       - Windows: checks if `win32evtlog` from `pywin32` is available:
         - If available: reads Security Event Log (Event ID 4624 -> `login_success`, Event ID 4625 -> `login_failure`).
         - If not available: logs warning `"pywin32 not installed; Windows Event Log collection disabled."` and returns empty list `[]`. Do NOT crash.
     - State tracking:
       - Stores `last_sent_timestamp` (in-memory or file `agent_log_state.json`) to only read newer log entries and prevent re-sending.
     - Function `collect_logs(since_timestamp: Optional[datetime]) -> List[dict]`:
       - Returns normalized log list:
         ```python
         {
             "source": "auth.log" | "windows_security",
             "event_type": "login_success" | "login_failure",
             "severity": "low" | "medium",
             "message": str,
             "source_ip": str,
             "username": str,
             "timestamp": iso_str
         }
         ```
     - Function `collect_and_send_logs(api_client, agent_id) -> int`:
       - Collects new logs and posts to `POST /agents/logs` using `api_client`.
       - Updates `last_sent_timestamp` on success.
2. In `agent/config.py`:
   - Add `LOG_COLLECT_INTERVAL: int = int(os.getenv("LOG_COLLECT_INTERVAL", "30"))`.
3. In `agent/main.py`:
   - Add periodic log collection loop (every `config.LOG_COLLECT_INTERVAL` seconds).
4. In `agent/README.md` (or `agent/INSTALL.md`):
   - Add documentation explaining optional Windows Event Log support via `pip install pywin32` and clarifying it is optional.
5. In `tests/test_agent_log_collector.py`:
   - Add unit tests for:
     - Linux log line regex parser (failed password -> `login_failure`, accepted -> `login_success`).
     - Windows fallback when `pywin32` is absent (returns empty list without error).
     - State tracking prevents duplicate log delivery.
     - Sending logs via mock API client.

## What NOT to Implement
- Do NOT make `pywin32` a mandatory requirement in `agent/requirements.txt`.
- Do NOT begin Phase 15.

## Testing
Run pytest:
```bash
$env:PYTHONPATH="backend"; $env:DATABASE_URL="sqlite:///./test_cybershield.db"; & "C:\Users\jesli\CascadeProjects\cybershield-ai\.venv312\Scripts\python.exe" -m pytest tests/test_agent_log_collector.py -v --tb=short
```

## Completion Criteria
- [ ] `agent/collectors/log_collector.py` implemented with safe Windows fallback.
- [ ] `last_sent_timestamp` prevents re-sending duplicate logs.
- [ ] `agent/main.py` runs log collection loop.
- [ ] `agent/README.md` / `INSTALL.md` documents optional `pywin32`.
- [ ] Tests pass in `tests/test_agent_log_collector.py`.
- [ ] `prompts/phase_14/progress.md` updated.

## Stop Condition
Stop immediately after you complete this task and update the progress file.
Do not start Task 14.4.
Output a short summary and wait for user instruction.
