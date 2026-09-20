# Phase 9 — CyberShield Agent

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> This prompt was written before execution. Before running it:  
> (1) Run `alembic current` — confirm which migrations are applied.  
> (2) Check `backend/app/api/v1/agents.py` — it already has stub endpoints (GET /, GET /{agent_id}, POST /, DELETE /{agent_id}); do NOT recreate the router, only fill in the logic.  
> (3) Check `tests/` — note which test files already exist.  
> (4) If reality differs from this prompt's assumptions, update this file first, then execute.  
> Prompts are a living plan, not a frozen snapshot.

---

## Prompt

```text
CYBERSHIELD AI — PHASE 9: CyberShield Agent

Repo: https://github.com/JeslinSajan/cybershield-ai

The CyberShield Agent is NOT an AI agent. It is a Python script
that runs on a customer PC, collects basic system information,
and sends it to the backend over HTTPS.

=======================================================================
STEP 0 — READ FIRST (verify against current repo, update if stale)
=======================================================================

Read these files before writing any code:

  backend/app/api/v1/agents.py
    → Already has stub GET /, GET /{agent_id}, POST /, DELETE /{agent_id}.
    → The stubs use get_any_authenticated_user for GET and
      require_role("Administrator") for POST/DELETE.
    → Phase 9 fills in the full implementation.

  backend/app/core/deps.py
    → Available RBAC deps:
        get_current_admin            (Administrator only)
        get_current_analyst_or_admin (Administrator + Security Analyst)
        get_any_authenticated_user   (all 3 roles)
    → Agent auth NOT implemented yet — TODO comment already exists.

  backend/app/models/agent.py
    → Agent, AgentCredential, AgentHeartbeat models exist.
    → Actual columns (use these, not schema.md):
        Agent: id, organization_id, name, hostname, status, version,
               last_heartbeat_at, is_active, created_at, updated_at, deleted_at
        AgentCredential: id, agent_id, credential_hash, type, issued_at,
                         expires_at, revoked_at, is_active, created_at, updated_at
        AgentHeartbeat: id, agent_id, organization_id, timestamp, status,
                        version, cpu_percent, memory_percent, details (JSONB),
                        created_at

  docs/api/agent-api.md
    → GET /agents/ and GET /agents/{agent_id} were added in the pre-phase fix.
    → POST /agents/enrollment-token, POST /agents/register, POST /agents/heartbeat
      are already documented.
    → Any new endpoint you introduce must be added to this doc first.

  alembic/versions/
    → Run: alembic current
    → If agents, agent_credentials, agent_heartbeats, scans, scan_results tables
      are not yet in the applied migrations, create a new migration before coding.

=======================================================================
STEP 1 — DATABASE MIGRATIONS (do this first)
=======================================================================

Check which tables exist in Neon by running:
  alembic current

The following tables must exist before Phase 9 can run:
  agents, agent_credentials, agent_heartbeats, scans, scan_results

If any are missing:
  alembic revision --autogenerate -m "phase9_agent_tables"
  alembic upgrade head

Confirm with: alembic current → shows latest revision.

=======================================================================
STEP 2 — BACKEND: COMPLETE AGENT ENDPOINTS
=======================================================================

File: backend/app/api/v1/agents.py
The stub already exists. Fill in the implementation.

--- POST /agents/enrollment-token (Administrator only) ---
  Dependency: Depends(get_current_admin)
  FR: FR-4.1
  Body (Pydantic schema): {agent_name: str, expires_in_minutes: int = 60}
  Logic:
    1. Generate token: secrets.token_urlsafe(32)
    2. Hash with SHA-256: hashlib.sha256(token.encode()).hexdigest()
    3. Create AgentCredential row:
         agent_id = None (not yet registered)  ← NOTE: You may need a
         separate EnrollmentToken model or use a temporary approach.
         Actually the simpler approach: store it in a separate
         enrollment_tokens dict in memory (keyed by hash, value=expires_at)
         for MVP. Use Redis or DB in production. Document this limitation.
    4. Return: {token: <raw>, expires_at: <iso datetime>}
  Error envelope: {"error": {"code": "...", "message": "...", "details": []}}
  Never log the raw token.

--- POST /agents/register (no JWT, uses enrollment token) ---
  FR: FR-4.2
  Body: {enrollment_token: str, name: str, hostname: str, version: str}
  Logic:
    1. Hash the incoming token: hashlib.sha256(token.encode()).hexdigest()
    2. Look it up in the enrollment store. Return 401 if not found or expired.
       Error code: AGENT_NOT_AUTHORIZED
    3. Create Agent row: status='PENDING', organization_id=<default org>
    4. Generate agent credential: secrets.token_urlsafe(48)
    5. Hash it: hashlib.sha256(cred.encode()).hexdigest()
    6. Create AgentCredential: agent_id=<new agent id>, credential_hash=<hash>,
       type='token', expires_at=now() + 365 days, is_active=True
    7. Invalidate the enrollment token from the store.
    8. Write AuditLog:
         organization_id, actor_type='system', actor_id=None,
         action='agent_enrolled', target_type='agents', target_id=agent.id,
         details={"name": agent.name, "hostname": agent.hostname}
    9. Return: {id, organization_id, name, hostname, status, version,
                credential: {token: <raw credential>, expires_at}}
  Never log the credential token.

--- POST /agents/heartbeat (Agent credential required) ---
  FR: FR-4.3
  Auth: Depends(require_agent_credential)  ← implement this dep (see below)
  Body: {agent_id: UUID, timestamp: datetime, status: str, version: str,
         cpu_percent: float, memory_percent: float, details: dict}
  Logic:
    1. Validate agent_id in body matches the credential's agent.
    2. Create AgentHeartbeat row with all fields.
    3. Update Agent: last_heartbeat_at=timestamp, status='ONLINE', version=version.
    4. Return: {agent_id, status, last_heartbeat_at}

--- GET /agents/ (Administrator + Security Analyst) ---
  Dependency: Depends(get_current_analyst_or_admin)
  FR: FR-4.7 (added in pre-phase API doc fix)
  Filter: ?status=ONLINE&limit=50&offset=0
  Returns agents where deleted_at IS NULL and organization_id matches JWT user's org.
  Response fields: id, name, hostname, status, version, is_active,
                   last_heartbeat_at, created_at

--- GET /agents/{agent_id} (Administrator + Security Analyst) ---
  Dependency: Depends(get_current_analyst_or_admin)
  FR: FR-4.7
  Returns single agent + last 10 heartbeats:
  {id, name, hostname, status, version, is_active, last_heartbeat_at,
   created_at, updated_at,
   recent_heartbeats: [{id, timestamp, status, cpu_percent, memory_percent, details}]}
  404 if agent not found or belongs to different org.
  Error: {"error": {"code": "NOT_FOUND", "message": "Agent not found.", "details": []}}

--- POST /agents/{agent_id}/revoke (Administrator only) ---
  Dependency: Depends(get_current_admin)
  FR: FR-4.5
  Logic:
    1. Set all AgentCredential.is_active = False for this agent.
    2. Set Agent.is_active = False, Agent.status = 'OFFLINE'.
    3. Write AuditLog: action='agent_revoked', actor_type='user', actor_id=user.id
    4. Return: {id, is_active: false, revoked_at: <now>}

=======================================================================
STEP 3 — require_agent_credential() DEPENDENCY
=======================================================================

Add to backend/app/core/deps.py:

  def require_agent_credential():
      """
      FastAPI dependency. Validates Authorization: Bearer header against
      agent_credentials table using SHA-256 hash comparison.
      Returns: authenticated Agent ORM object.
      Raises:
        401 {"error": {"code": "AGENT_NOT_AUTHORIZED", "message": "...", "details": []}}
            if header missing or credential not found/expired/revoked.
        403 {"error": {"code": "AGENT_REVOKED", "message": "...", "details": []}}
            if agent is_active=False.
      """
      Steps:
        1. Extract Bearer token from Authorization header. 401 if missing.
        2. Hash it: hashlib.sha256(token.encode()).hexdigest()
        3. Query AgentCredential where credential_hash=<hash> AND is_active=True
           AND (expires_at IS NULL OR expires_at > now()). 401 if not found.
        4. Load Agent. 403 if agent.is_active = False.
        5. Return Agent ORM object.

  NOTE: SHA-256 for agent credentials (not bcrypt). Bcrypt is non-deterministic
  and cannot be used for token lookup. SHA-256 of a 48-byte random token
  (= 384 bits of entropy) is collision-safe for this use case.
  Document this choice in a comment in deps.py.

=======================================================================
STEP 4 — OFFLINE DETECTION BACKGROUND TASK
=======================================================================

Add to backend/app/main.py lifespan, after yield:
  No — add it to the startup section, BEFORE yield:

  import asyncio

  async def _mark_agents_offline():
      """Background task: marks ONLINE agents OFFLINE after timeout."""
      from app.core.database import SessionLocal
      from app.models.agent import Agent
      from datetime import timedelta
      import datetime
      while True:
          await asyncio.sleep(60)
          try:
              db = SessionLocal()
              timeout = timedelta(seconds=settings.AGENT_OFFLINE_TIMEOUT_SECONDS)
              cutoff = datetime.datetime.utcnow() - timeout
              stale = db.query(Agent).filter(
                  Agent.status == 'ONLINE',
                  Agent.is_active == True,
                  Agent.last_heartbeat_at < cutoff
              ).all()
              for agent in stale:
                  agent.status = 'OFFLINE'
                  logger.info(f"Agent {agent.name} marked OFFLINE")
              db.commit()
          except Exception as e:
              logger.error(f"Offline detection error ({type(e).__name__})")
          finally:
              db.close()

  In lifespan startup:
    asyncio.create_task(_mark_agents_offline())

Add AGENT_OFFLINE_TIMEOUT_SECONDS to backend/app/core/config.py (default: 90).
Add to backend/.env.example.

=======================================================================
STEP 5 — AGENT APPLICATION (agent/ folder)
=======================================================================

Structure:
  agent/
  ├── main.py           — entry point
  ├── config.py         — reads .env
  ├── identity.py       — saves/loads agent_id + credential to agent_identity.json
  ├── enrollment.py     — calls POST /agents/register
  ├── heartbeat.py      — calls POST /agents/heartbeat using psutil
  ├── api_client.py     — thin HTTP client using httpx with error handling
  ├── requirements.txt  — pinned: psutil==5.9.8, httpx==0.27.2, python-dotenv==1.0.1
  └── .env.example      — BACKEND_URL, ENROLLMENT_TOKEN, AGENT_NAME

agent/requirements.txt — pin all versions:
  psutil==5.9.8
  httpx==0.27.2
  python-dotenv==1.0.1

main.py flow:
  1. Load config from .env
  2. If agent_identity.json exists: load agent_id + credential, skip enrollment.
  3. Else: call enrollment.py → save result to agent_identity.json
     agent_identity.json is gitignored. Never commit it.
  4. Loop every 30 seconds:
     a. Collect cpu_percent, memory_percent, disk_percent via psutil.
     b. POST /agents/heartbeat with Authorization: Bearer <credential>
     c. Log "Heartbeat sent" on success.
     d. On 401: log "Credential rejected — contact admin." and sys.exit(1).
     e. On network error: log "Backend unreachable, retrying..." and continue.

api_client.py error handling:
  - 5xx or ConnectionError/TimeoutError: retry up to 3 times, 2s sleep between.
    After 3 failures: return None and log warning. Do NOT crash.
  - 401: set self._credential_valid = False, return None.
  - All other HTTP errors: log status code and return None.
  NEVER log: the credential token, the BACKEND_URL if it contains credentials.

=======================================================================
STEP 6 — DOCUMENTATION UPDATE
=======================================================================

Update docs/api/agent-api.md:
  - POST /agents/enrollment-token — verify documented correctly
  - POST /agents/register — verify documented correctly
  - POST /agents/heartbeat — verify documented correctly
  - POST /agents/{agent_id}/revoke — verify documented correctly
  These were added in Phase 4 and updated in the pre-phase fix. Verify
  they match the actual implementation. Update if they differ.

Create agent/INSTALL.md:
  1. Install Python 3.12+
  2. Install Nmap (https://nmap.org/download.html)
  3. pip install -r requirements.txt
  4. Copy .env.example to .env and fill in BACKEND_URL + ENROLLMENT_TOKEN
  5. Run: python main.py

=======================================================================
STEP 7 — DO NOT BUILD IN PHASE 9
=======================================================================

- Nmap scanning (Phase 11)
- Vulnerability matching (Phase 13)
- Log collection (Phase 14)
- Alert generation (Phase 15)
- Any frontend code (Phase 21)
- Task polling loop (Phase 10)

=======================================================================
VERIFICATION CHECKLIST — REQUIRED EVIDENCE BEFORE MARKING DONE
=======================================================================

Every item below requires actual output, not assumption:

[ ] alembic current — paste the output confirming latest migration is applied
[ ] pytest tests/test_agents.py -v — paste output showing all tests pass
[ ] pytest tests/ -v --tb=short — paste output showing 0 regressions
[ ] curl -s -X POST http://localhost:8000/api/v1/agents/enrollment-token \
      -H "Authorization: Bearer <admin JWT>" \
      -H "Content-Type: application/json" \
      -d '{"agent_name":"test","expires_in_minutes":60}'
    → paste the actual JSON response showing token and expires_at
[ ] python agent/main.py — paste terminal output showing:
      "Agent enrolled. ID: <uuid>"
      "Heartbeat sent" (at least 2 occurrences, 30s apart)
[ ] curl GET /api/v1/agents/<id> with Analyst JWT — paste response
      showing status=ONLINE and recent last_heartbeat_at
[ ] Wait 120s with agent stopped — confirm agent shows OFFLINE in GET /agents/<id>
    Paste the actual API response.
[ ] Test Viewer access: curl GET /api/v1/agents/ with Viewer JWT
    → paste 403 response with correct error envelope

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat(agent): Phase 9 — agent application, enrollment, heartbeat, offline detection"

Do not force-push. Pull first if remote has diverged.
```
