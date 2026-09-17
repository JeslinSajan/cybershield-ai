# Phase 10 — Agent ↔ Backend Integration

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 10: Agent ↔ Backend Integration

Repo: https://github.com/JeslinSajan/cybershield-ai

Phase 9 built the basic agent with enrollment and heartbeat.
Phase 10 makes the connection complete and reliable.

=======================================================================
WHAT TO BUILD
=======================================================================

1. OFFLINE DETECTION
   The backend must automatically mark an agent as OFFLINE if it 
   has not sent a heartbeat in the last 90 seconds.
   
   How: A background task that runs every 60 seconds and updates 
   any agent where last_heartbeat_at < now() - 90 seconds 
   from ONLINE to OFFLINE.

2. AGENT REVOCATION
   Admin can deactivate an agent from the dashboard/API.
   POST /api/v1/agents/{agent_id}/revoke (Admin JWT required)
   Sets agent is_active = False. The agent's credential stops working.
   The agent should detect the 401 response and exit cleanly 
   with a message: "Agent credential rejected — contact admin."

3. TASK DISPATCH (basic version)
   The backend can send a task to the agent.
   GET /api/v1/agents/tasks — agent polls this every 30 seconds.
   POST /api/v1/agents/tasks/{id}/status — agent reports progress.
   
   For now tasks are simple — only support "health_check" type.
   When the agent gets a health_check task:
     - Reports RUNNING status
     - Collects system metrics
     - Posts results to POST /api/v1/agents/results
     - Reports COMPLETED status

4. RESULT UPLOAD
   POST /api/v1/agents/results — agent sends collected data.
   Backend stores it in scan_results table as raw JSON.
   No processing yet — just store it.

=======================================================================
AGENT IMPROVEMENTS
=======================================================================

- If backend is unreachable: log a warning, skip the cycle, try again.
- If the agent gets a 401 response: log "Credential rejected" and stop.
- Add task polling to the main loop (every 30 seconds).

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Start the backend and agent.
2. Stop the agent — wait 90 seconds — confirm backend marks it OFFLINE.
3. Restart the agent — confirm it goes back to ONLINE.
4. Call POST /agents/{id}/revoke — confirm agent exits with clear message.
5. Create a health_check task — confirm agent picks it up and posts result.
6. Run: pytest tests/ — all tests must pass, no regressions.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat(agent): Phase 10 — offline detection, revocation, task dispatch"
```
