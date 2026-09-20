# Phase 10 — Agent ↔ Backend Integration

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> This prompt was written before execution. Before running it:  
> (1) Run `alembic current` — confirm Phase 9 migrations are applied.  
> (2) Check `backend/app/api/v1/agents.py` — confirm enrollment, register, heartbeat are implemented from Phase 9.  
> (3) Check `backend/app/core/deps.py` — confirm `require_agent_credential()` exists from Phase 9.  
> (4) If Phase 9 is incomplete, finish it before starting Phase 10.  
> Prompts are a living plan, not a frozen snapshot.

---

## Prompt

```text
CYBERSHIELD AI — PHASE 10: Agent ↔ Backend Integration

Repo: https://github.com/JeslinSajan/cybershield-ai

Phase 9 built enrollment, heartbeat, and the agent application.
Phase 10 completes the connection: task dispatch, result upload,
credential revocation handling, and offline recovery.

=======================================================================
STEP 0 — READ FIRST (verify before executing)
=======================================================================

  backend/app/api/v1/agents.py — confirm Phase 9 work is complete:
    [ ] POST /enrollment-token implemented
    [ ] POST /register implemented
    [ ] POST /heartbeat implemented
    [ ] GET / implemented
    [ ] GET /{agent_id} implemented
    [ ] POST /{agent_id}/revoke implemented
    [ ] require_agent_credential() dep exists in deps.py

  If any are missing, finish Phase 9 first.

  docs/api/agent-api.md — confirm GET /agents/tasks, POST /agents/tasks/{id}/status,
    POST /agents/results are documented. They were added in Phase 4.
    If not, add them before implementing.

=======================================================================
STEP 1 — BACKEND: GET /agents/tasks
=======================================================================

  Auth: Depends(require_agent_credential)  — agent credential, not JWT
  FR: FR-5.1
  Logic:
    - Agent identified from the credential dep.
    - Query scans table: agent_id = agent.id AND status = 'PENDING'
      AND organization_id = agent.organization_id
    - Return list of matching Scan rows.
  Response shape (matches docs/api/agent-api.md):
    [{id, organization_id, agent_id, scan_type, status, target_scope, created_at}]
  Returns empty list [] if no pending tasks — not 404.

=======================================================================
STEP 2 — BACKEND: POST /agents/tasks/{task_id}/status
=======================================================================

  Auth: Depends(require_agent_credential)
  FR: FR-5.1
  Body: {status: str, started_at: datetime (optional), details: dict (optional)}
  Allowed status values: RUNNING, COMPLETED, FAILED
  Logic:
    - Look up scan by task_id. 404 if not found.
    - Verify scan.agent_id == credential agent.id. 403 if mismatch.
      Error: {"error": {"code": "FORBIDDEN", "message": "Task does not belong to this agent.", "details": []}}
    - Update scan.status to new value.
    - If status = RUNNING: set scan.started_at = started_at or now()
    - If status = COMPLETED or FAILED: set scan.completed_at = now()
    - Return updated scan: {id, status, updated_at}

=======================================================================
STEP 3 — BACKEND: POST /agents/results
=======================================================================

  Auth: Depends(require_agent_credential)
  FR: FR-5.2
  Body: {scan_id: UUID, device_id: UUID, result_type: str, raw_payload: dict}
  Logic:
    - Look up Scan. 404 if not found.
    - Verify scan.agent_id == credential agent.id. 403 if mismatch.
    - Create ScanResult:
        organization_id = agent.organization_id,
        scan_id, device_id, result_type, raw_payload (JSONB)
    - Return: {id, scan_id, device_id, result_type, created_at}
  Status: 201 Created
  NOTE: Do NOT process the payload in Phase 10. Just store it.
  Processing happens in Phase 11 (discovery) and Phase 13 (vulnerability).

=======================================================================
STEP 4 — BACKEND: POST /agents/{agent_id}/rotate-credential
=======================================================================

  Auth: Depends(get_current_admin)  — human JWT, Administrator only
  FR: FR-4.6
  Logic:
    1. Find agent. 404 if not found or wrong org.
    2. Set all active AgentCredentials for this agent:
         is_active = False, revoked_at = now()
    3. Generate new credential: secrets.token_urlsafe(48)
    4. Hash it: hashlib.sha256(cred.encode()).hexdigest()
    5. Create new AgentCredential: agent_id, credential_hash, type='token',
         expires_at = now() + 365 days, is_active = True
    6. Write AuditLog: actor_type='user', actor_id=user.id,
         action='agent_credential_rotated', target_type='agents', target_id=agent.id
    7. Return: {agent_id, credential_id: <new cred id>, expires_at, is_active: true}
  NOTE: The new raw token is NOT returned. The administrator must use a
  secure out-of-band channel (e.g., manually setting .env on the agent).
  Document this limitation in agent/INSTALL.md.
  Never log the raw token.

=======================================================================
STEP 5 — BACKEND: GET /agents/{agent_id}/network-stats
=======================================================================

  Auth: Depends(get_current_analyst_or_admin)
  FR: FR-7.1
  Logic:
    - Return last 10 AgentHeartbeat rows for the agent, ordered by timestamp DESC.
    - Filter where details JSONB key 'interfaces' exists (i.e., has network data).
    - Return: [{id, timestamp, cpu_percent, memory_percent, details}]
  If agent doesn't belong to user's org: 403.

=======================================================================
STEP 6 — AGENT: TASK POLLING LOOP
=======================================================================

Add to agent/ folder:

  agent/task_poller.py:

    import httpx, json

    def poll_tasks(api_client, agent_id: str) -> list:
        """GET /agents/tasks and return pending task list."""
        resp = api_client.get("/agents/tasks")
        if resp is None:
            return []
        return resp.get("tasks", resp) if isinstance(resp, dict) else resp

    def handle_task(task: dict, api_client, collectors: dict):
        """Dispatch task to correct handler based on scan_type."""
        scan_type = task.get("scan_type")
        task_id = task.get("id")

        if scan_type == "health_check":
            handle_health_check(task_id, api_client, collectors)
        else:
            # Unsupported type — mark FAILED, log warning
            api_client.post(f"/agents/tasks/{task_id}/status",
                            {"status": "FAILED",
                             "details": {"error": f"Unsupported scan_type: {scan_type}"}})
            logger.warning(f"Unsupported task type: {scan_type}")

    def handle_health_check(task_id: str, api_client, collectors: dict):
        """Collect system metrics and upload as a health_check result."""
        api_client.post(f"/agents/tasks/{task_id}/status", {"status": "RUNNING"})
        metrics = collectors["system"].collect()
        # POST result — device_id is None for health checks
        api_client.post("/agents/results", {
            "scan_id": task_id,
            "device_id": None,
            "result_type": "system",
            "raw_payload": metrics
        })
        api_client.post(f"/agents/tasks/{task_id}/status", {"status": "COMPLETED"})

  Add task polling to agent/main.py:
    - Every TASK_POLL_INTERVAL seconds (default 30, from .env)
    - Call poll_tasks() then handle_task() for each returned task.
    - Import task_poller in main.py.

  Add TASK_POLL_INTERVAL to agent/config.py and agent/.env.example.

=======================================================================
STEP 7 — AGENT: ROBUST ERROR HANDLING IN api_client.py
=======================================================================

  These behaviors must be implemented (Phase 9 may have already done some):

  5xx / ConnectionError / TimeoutError:
    - Retry up to 3 times with 2 second sleep between attempts.
    - After 3 failures: log "Backend unreachable after 3 retries." and return None.
    - Do NOT raise an exception.

  401 Unauthorized:
    - Log "Credential rejected — agent may be revoked or rotated."
    - Set self._credential_valid = False
    - Return None. The main loop should check this flag and exit cleanly:
        if not api_client._credential_valid:
            logger.error("Stopping — manual credential update required.")
            sys.exit(1)

  404 Not Found (e.g., task already cancelled):
    - Log the 404 and return None. Do not crash.

  Offline mode (3+ consecutive heartbeat failures):
    - Log "Backend appears offline. Skipping cycle."
    - Continue loop. Do not queue locally (Phase 25 adds resilience).

=======================================================================
VERIFICATION CHECKLIST — REQUIRED EVIDENCE BEFORE MARKING DONE
=======================================================================

[ ] alembic current — paste output confirming scans, scan_results tables exist
[ ] pytest tests/test_agents.py -v — paste full output, 0 failures
[ ] pytest tests/ -v --tb=short — paste output, 0 regressions from Phase 9
[ ] Create a health_check scan task via the API:
    curl -X POST http://localhost:8000/api/v1/scans/ \
      -H "Authorization: Bearer <admin JWT>" \
      -d '{"agent_id":"<uuid>","scan_type":"health_check","target_scope":"local"}'
    Paste the response.
[ ] Run agent — confirm it picks up the task and posts results:
    Paste agent terminal output showing "Task completed: health_check"
[ ] curl GET /agents/<id> — paste response showing status=ONLINE
[ ] Stop agent for 120s — paste GET /agents/<id> showing status=OFFLINE
[ ] Test revocation: POST /agents/<id>/revoke, then restart agent.
    Paste agent log showing "Credential rejected" and clean exit.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat(agent): Phase 10 — task dispatch, result upload, credential rotation"

Do not force-push.
```
