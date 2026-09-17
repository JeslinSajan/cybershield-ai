# Phase 14 — Log Management

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 14: Log Management

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

The agent reads system log files (auth.log on Linux, Windows Event 
Log on Windows), parses them, and sends them to the backend.
The backend stores the logs in a normalized format.

=======================================================================
AGENT SIDE
=======================================================================

Add agent/collectors/log_collector.py:

For Linux:
  def collect_auth_logs(max_lines=100) -> list:
      """
      Read the last max_lines lines from /var/log/auth.log.
      Parse each line and return:
        [
          {
            "timestamp": "2026-09-17T10:00:00",
            "source": "auth.log",
            "event_type": "login_success" or "login_failure",
            "username": "root",
            "source_ip": "192.168.1.5",
            "message": "<raw log line>"
          }
        ]
      Detect login_failure for lines containing "Failed password".
      Detect login_success for lines containing "Accepted password".
      """

For Windows (if running on Windows):
  Use the pywin32 library to read Windows Security Event Log.
  Event ID 4624 = login success.
  Event ID 4625 = login failure.
  Fall back gracefully if pywin32 is not installed (log a warning).

Run log collection every 60 seconds.
POST collected logs to /agents/logs (new endpoint, see below).
Only send new logs — track the last sent timestamp in a local file.

=======================================================================
BACKEND SIDE
=======================================================================

New endpoint:
  POST /api/v1/agents/logs
    - Agent credential required.
    - Accepts a list of log entries.
    - For each entry, create a row in the logs table with:
        agent_id, organization_id, source, event_type, severity,
        message, source_ip, username, timestamp.
    - Set severity based on event_type:
        login_failure → "medium"
        login_success → "low"
        unknown → "info"

Read endpoints:
  GET /api/v1/logs/
    - Admin/Analyst only.
    - Supports query params: ?source=auth.log&event_type=login_failure
      &from=<date>&to=<date>&limit=100
  
  GET /api/v1/logs/{id}
    - Admin/Analyst only.

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Run the agent on a Linux machine (or dev machine with mock data).
2. Confirm log entries appear in GET /api/v1/logs/.
3. Filter by event_type=login_failure — confirm it works.
4. pytest tests/ — no regressions.

Note: If testing on Windows without auth.log, create a 
mock log file at a configurable path for testing purposes.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 14 — log collection and normalized log storage"
```
