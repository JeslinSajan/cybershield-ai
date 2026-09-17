# Phase 10 — Agent ↔ Backend Integration

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 10: Agent ↔ Backend Integration

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
CONTEXT — WHERE WE ARE
=======================================================================

Phase 9 delivered:
  - The agent/ Python application with enrollment, heartbeat loop, 
    and psutil system collection.
  - The backend agent endpoints (POST /agents/register, 
    POST /agents/heartbeat, etc.) as stubs or basic implementations.

Phase 10 makes that connection real, reliable, and complete. The goal 
is a tested, working data pipeline from Agent → Backend → Database, 
with proper status tracking, offline detection, credential lifecycle, 
error handling on both sides, and the task dispatch loop so the 
backend can send work to the agent and receive results back.

By the end of this phase the full loop must work:

  Administrator triggers action (e.g. enrollment, task)
       ↓
  Backend creates task record, sets status PENDING
       ↓
  Agent polls GET /agents/tasks, picks up the task
       ↓
  Agent sends POST /agents/tasks/{id}/status → RUNNING
       ↓
  Agent completes work, sends POST /agents/results
       ↓
  Agent sends POST /agents/tasks/{id}/status → COMPLETED
       ↓
  Backend stores results, available for Phase 11+ processing

=======================================================================
STEP 0 — INSPECT FIRST
=======================================================================

Read these before writing any code:

1. docs/api/agent-api.md — full request/response schemas for ALL 
   agent endpoints. You must implement to these contracts exactly.

2. docs/architecture/agent-architecture.md — "Allowed Agent 
   Operations" table, "Local Failure Behavior" section.

3. docs/srs/functional-requirements.md — Section 4 in full:
   - FR-4.3: heartbeat interval + health payload
   - FR-4.4: OFFLINE detection after configurable timeout
   - FR-4.5: revocation stops further requests immediately
   - FR-4.6: credential rotation without full re-enrollment

4. docs/database/schema.md — Tables 6, 7, 8 (agents, 
   agent_credentials, agent_heartbeats). Note:
   - agents.status: PENDING → ONLINE → OFFLINE
   - agent_credentials.is_active / revoked_at / expires_at
   - agent_heartbeats stores every heartbeat as a row

5. Review the existing backend/app/api/v1/agents.py from Phase 9 
   and list what is complete vs placeholder.

After reading, confirm:
  a) Which backend endpoints are already fully implemented vs stub.
  b) Whether offline detection is currently implemented anywhere.
  c) Whether credential rotation updates the DB correctly.
  d) Whether the agent currently polls for tasks and reports status.

=======================================================================
STEP 1 — BACKEND: COMPLETE AGENT ENDPOINT IMPLEMENTATIONS
=======================================================================

Audit every agent endpoint and complete any that are stubs.
The following must all be fully functional with real DB writes:

--- Enrollment Token (POST /api/v1/agents/enrollment-token) ---
  - Administrator JWT required (use existing require_role dependency).
  - Generate a secure random token (secrets.token_urlsafe(32)).
  - Hash it with bcrypt and store in agent_credentials with:
      type = "enrollment"
      expires_at = now() + expires_in_minutes
      is_active = True
  - Return the raw token (never stored plaintext — same pattern as 
    user password hashing).
  - Do NOT create the Agent record here. The Agent creates itself 
    on registration.

--- Register (POST /api/v1/agents/register) ---
  - No JWT. Accept enrollment token in body.
  - Look up the hashed enrollment token in agent_credentials where 
    type = "enrollment" AND is_active = True AND expires_at > now().
  - If not found or expired: return 401 with code INVALID_TOKEN.
  - If found: 
      1. Create agents record (status = PENDING).
      2. Generate a new long-lived agent credential token 
         (secrets.token_urlsafe(48)).
      3. Hash it and store in agent_credentials (type = "agent_token",
         expires_at = now() + 365 days, is_active = True).
      4. Mark the enrollment token as used (is_active = False).
      5. Return the new agent_id and the RAW credential token.
  - On 409: agent name already registered for this org.

--- Heartbeat (POST /api/v1/agents/heartbeat) ---
  - Agent credential required (require_agent_credential dependency).
  - Validate agent_id in the body matches the credential's owner.
  - Write a new row to agent_heartbeats with all health fields.
  - Update agents.last_heartbeat_at = now(), agents.status = ONLINE,
    agents.version from the body.
  - Return 200 with the updated status.

--- Get Tasks (GET /api/v1/agents/tasks) ---
  - Agent credential required.
  - Return all scans rows where:
      agent_id = current agent
      status = PENDING
  - Return as task list per the API contract schema.
  - Do not return completed or cancelled tasks.

--- Update Task Status (POST /api/v1/agents/tasks/{task_id}/status) ---
  - Agent credential required.
  - Validate the task belongs to the requesting agent.
  - Update scans.status to the value in the body 
    (RUNNING, COMPLETED, FAILED).
  - If status = RUNNING: set scans.started_at.
  - If status = COMPLETED or FAILED: set scans.completed_at.
  - Return the updated task.
  - Do NOT allow an agent to set another agent's task status.

--- Upload Results (POST /api/v1/agents/results) ---
  - Agent credential required.
  - Validate the scan_id belongs to the requesting agent.
  - Create a scan_results row with the raw_payload as JSONB.
  - Associate with device_id if provided.
  - Return 201 with the created result ID and timestamp.
  - Do NOT process the payload yet — store it raw for Phase 11+.

--- Revoke (POST /api/v1/agents/{agent_id}/revoke) ---
  - Administrator JWT required.
  - Set all agent_credentials.is_active = False for this agent 
    (not just the latest — revoke all active credentials).
  - Set agents.is_active = False, agents.status = OFFLINE.
  - Write audit log entry: "Agent <name> revoked by <admin_email>".
  - Return 200 with is_active: false and revoked_at.

--- Rotate Credential (POST /api/v1/agents/{agent_id}/rotate-credential) ---
  - Administrator JWT required.
  - Revoke existing active credential (set revoked_at, is_active=False).
  - Generate a new credential token, hash it, store it.
  - Do NOT revoke the agent itself — it stays ONLINE.
  - The agent must be notified via its next request returning 401, 
    after which it must reload its credential from a secure channel.
    (For MVP: the administrator copies the new token to the agent's 
    .env file manually — document this in the README).
  - Return the new credential metadata (not the raw token in the 
    rotate response — document that this is a limitation).

=======================================================================
STEP 2 — BACKEND: require_agent_credential() DEPENDENCY
=======================================================================

This is the security boundary between human users and Agent actors.
It must be completely separate from require_role().

Implement in backend/app/core/deps.py:

def require_agent_credential():
    """
    FastAPI dependency. Validates the Authorization: Bearer header
    against agent_credentials table (not users/JWTs).
    
    Returns: the authenticated Agent ORM object.
    Raises:
      401 if header missing or malformed.
      401 if credential not found, is_active=False, or expired.
      403 if the agent is revoked (is_active=False on agents table).
    """

Steps:
  1. Extract Bearer token from Authorization header. Return 401 if 
     missing.
  2. Query agent_credentials where is_active=True, not expired.
     Hash the incoming token the same way it was stored, compare.
  3. If not found: return 401 with code AGENT_NOT_AUTHORIZED.
  4. Load the parent agents row. If agents.is_active = False: 
     return 403 with code AGENT_REVOKED.
  5. Return the Agent ORM object for use in the endpoint.

IMPORTANT: Do NOT use bcrypt for agent credential lookup — bcrypt 
is not indexable. Use HMAC-SHA256 (hashlib.sha256) to hash the 
token before storing and before comparing, so lookups are O(1).
This is different from password hashing where bcrypt is correct.

=======================================================================
STEP 3 — BACKEND: OFFLINE DETECTION (FR-4.4)
=======================================================================

FR-4.4: The system shall mark an Agent as OFFLINE if no heartbeat is 
received within a configurable timeout.

Implement as a FastAPI startup background task using asyncio:

  AGENT_OFFLINE_TIMEOUT_SECONDS (default: 90 — configurable via env).

  Background task logic (runs every 30 seconds):
    SELECT * FROM agents 
    WHERE status = 'ONLINE' 
    AND is_active = True 
    AND last_heartbeat_at < now() - AGENT_OFFLINE_TIMEOUT_SECONDS

    For each result:
      UPDATE agents SET status = 'OFFLINE', updated_at = now()
      Log: "Agent <name> marked OFFLINE (last heartbeat: <ts>)"

Wire this into app/main.py lifespan using asyncio.create_task().
The task must not crash the backend if it fails — wrap it in 
try/except and log errors.

Add AGENT_OFFLINE_TIMEOUT_SECONDS to backend/app/core/config.py.
Add it to backend/.env.example.

=======================================================================
STEP 4 — AGENT: TASK POLLING LOOP
=======================================================================

Add task_poller.py to the agent/ directory:

  def poll_tasks(api_client, agent_id) -> list:
      """Poll GET /agents/tasks and return pending tasks."""

  def handle_task(task, api_client):
      """
      Dispatch a task to the correct handler based on task.scan_type.
      Currently supported types for Phase 10:
        "health_check" — report current system metrics as a result.
        (other types reserved for Phase 11+)
      
      For unsupported types: log warning and update status to FAILED 
      with details: "Unsupported task type: <type>".
      """

  def handle_health_check_task(task, api_client):
      """
      1. POST /tasks/{id}/status → RUNNING
      2. Collect system metrics from collectors/system_collector.py
      3. POST /agents/results with result_type="health_check" 
         and raw_payload = { collected metrics }
      4. POST /tasks/{id}/status → COMPLETED
      """

Add task polling to agent/scheduler.py on a TASK_POLL_INTERVAL 
(default: 30 seconds, configurable via .env).

=======================================================================
STEP 5 — AGENT: ROBUST ERROR HANDLING
=======================================================================

The agent must not crash on transient network errors.

In api_client.py, implement these behaviors:

  Transient errors (5xx, ConnectionError, TimeoutError):
    - Retry up to 3 times with exponential backoff 
      (1s, 2s, 4s delays).
    - After 3 failures: log "Backend unreachable after 3 retries" 
      and return None (do not raise).

  401 Unauthorized:
    - Log "Credential rejected — agent may be revoked or rotated."
    - Set an internal flag: self._credential_valid = False.
    - Stop sending ALL subsequent requests (heartbeat + tasks).
    - Log "Agent stopping — manual credential update required."
    - Exit cleanly.

  404 Not Found (e.g., task no longer exists):
    - Log the 404, skip the task, continue.

  Offline mode (backend unreachable for > 3 heartbeat cycles):
    - Log "Backend appears offline. Agent will retry on next cycle."
    - Do NOT queue data locally in Phase 10 (Phase 25 adds retry 
      queuing for resilience). Simply miss the cycle.

=======================================================================
STEP 6 — AGENT: CONFIGURATION ADDITIONS
=======================================================================

Add to agent/config.py (and .env.example):

  TASK_POLL_INTERVAL      = 30    # seconds between task polls
  MAX_RETRY_ATTEMPTS      = 3
  REQUEST_TIMEOUT_SECONDS = 10

=======================================================================
STEP 7 — ADMIN AGENT LIST ENDPOINT (for dashboard, Phase 21)
=======================================================================

Implement GET /api/v1/agents/ and GET /api/v1/agents/{agent_id} 
now so the data is available for the frontend in Phase 21.

  GET /agents/
    - Administrator or Analyst JWT required.
    - Returns list of all non-deleted agents in the org with:
      id, name, hostname, status, version, last_heartbeat_at, 
      is_active, created_at.
    - Viewer: 403.

  GET /agents/{agent_id}
    - Administrator or Analyst JWT required.
    - Returns single agent detail + last 10 heartbeats from 
      agent_heartbeats table.

These use human JWT (require_role), not agent credentials.

=======================================================================
STEP 8 — TESTING REQUIREMENTS
=======================================================================

All tests go in tests/test_agents.py and tests/test_agent_lifecycle.py.

Backend unit/API tests:
  - test_enrollment_token_returns_token_for_admin
  - test_enrollment_token_fails_for_non_admin
  - test_register_with_valid_token_creates_agent_and_credential
  - test_register_with_expired_token_returns_401
  - test_register_with_already_used_token_returns_401
  - test_heartbeat_with_valid_credential_returns_200_and_updates_db
  - test_heartbeat_with_invalid_credential_returns_401
  - test_heartbeat_updates_last_heartbeat_at
  - test_offline_detection_marks_agent_offline_after_timeout
  - test_revoke_sets_agent_inactive_and_returns_403_on_next_request
  - test_rotate_credential_old_token_rejected_new_token_accepted
  - test_get_tasks_returns_pending_tasks_for_agent
  - test_get_tasks_does_not_return_other_agents_tasks
  - test_update_task_status_to_running
  - test_update_task_status_to_completed
  - test_upload_results_creates_scan_result_row

Manual end-to-end verification (document the output in PHASE10_SUMMARY.md):
  1. Start local backend.
  2. Create enrollment token via API.
  3. Run agent/main.py with the token.
  4. Confirm: "Agent enrolled. ID: <uuid>"
  5. Confirm: "Heartbeat sent" every 30 seconds.
  6. Confirm: GET /agents/{id} shows status=ONLINE and recent 
     last_heartbeat_at.
  7. Wait 90 seconds without the agent running.
  8. Confirm: GET /agents/{id} shows status=OFFLINE 
     (offline detection task ran).
  9. Call POST /agents/{id}/revoke.
  10. Restart agent — confirm: agent logs "Credential rejected" 
      and exits cleanly.
  11. Call POST /agents/{id}/rotate-credential.
  12. Update agent .env with new token, restart — confirm enrollment 
      works with new credential.

=======================================================================
STEP 9 — OUT OF SCOPE FOR PHASE 10
=======================================================================

Do NOT implement in this phase:
  - Nmap device discovery (Phase 11)
  - Vulnerability scanning (Phase 13)
  - Log file collection (Phase 14)
  - Threat detection rules (Phase 15)
  - Alert creation (Phase 16)
  - Any frontend UI (Phase 21)
  - Local offline data queueing (Phase 25)

=======================================================================
STEP 10 — DOCUMENTATION
=======================================================================

After implementation and verification, write docs/PHASE10_SUMMARY.md
following the same structure as PHASE7_SUMMARY.md and 
PHASE8_SUMMARY.md. Include:
  - What was built.
  - Architecture of the Agent ↔ Backend pipeline.
  - The offline detection mechanism.
  - The credential lifecycle (enroll → heartbeat → rotate → revoke).
  - Manual verification evidence (actual log output, API responses).
  - Test suite results (all tests must pass before declaring done).

Mark prompts/phase_10_agent_to_backend_integration.md Status as Done.

=======================================================================
COMMIT MESSAGE
=======================================================================

"feat(agent): complete Phase 10 — agent-backend integration with task 
dispatch, offline detection, credential lifecycle, and robust error 
handling"

=======================================================================
RULES
=======================================================================

- Never log credential tokens, enrollment tokens, or their hashes.
- HMAC-SHA256 for agent credential storage/lookup (not bcrypt).
- Bcrypt only for human passwords.
- Agent and human auth dependencies must remain completely separate.
- The offline detection background task must not crash the backend.
- Do not implement out-of-scope features.
- Write the implementation plan first — do not start coding until 
  it is approved.
- Run the full test suite (all 57+ existing tests + new ones) before 
  pushing. No regressions allowed.
```
