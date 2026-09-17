# Phase 9 — CyberShield Agent

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 9: CyberShield Agent (Python Application)

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
CRITICAL DISTINCTION — READ BEFORE STARTING
=======================================================================

The CyberShield Agent is NOT an AI agent, NOT a chatbot, and NOT an 
LLM wrapper. It is a standalone Python security-monitoring application 
that runs as a background service on an authorized customer PC or 
server. Its only job is:

    Collect → Monitor → Scan → Report

It has no UI. It communicates exclusively with the FastAPI backend over 
HTTPS. It never connects directly to PostgreSQL. It never accesses user 
management, roles, or system settings.

This is a Python application, not a cloud service. It will be installed 
on a machine that belongs to the customer.

=======================================================================
STEP 0 — INSPECT FIRST (do this before planning anything)
=======================================================================

Read these documents in full before writing a single line of code:

1. docs/architecture/agent-architecture.md  
   — Internal modules, allowed operations, boundary rules.

2. docs/api/agent-api.md  
   — Exact request/response schemas for every agent endpoint.
   — FR traceability (FR-4.1 through FR-4.6, FR-5.1, FR-7.1, 
     FR-7.2, FR-8.1).

3. docs/database/schema.md — Tables 6, 7, 8:
   — agents (id, organization_id, name, hostname, status, version, 
     last_heartbeat_at, is_active)
   — agent_credentials (credential_hash, type, issued_at, expires_at, 
     revoked_at, is_active)
   — agent_heartbeats (agent_id, organization_id, timestamp, status, 
     version, cpu_percent, memory_percent, details JSONB)

4. docs/srs/functional-requirements.md — Section 4 (Agent Management):
   — FR-4.1: Administrator generates enrollment token via dashboard.
   — FR-4.2: Agent registers using that token, receives credential.
   — FR-4.3: Agent sends heartbeat on a configurable interval.
   — FR-4.4: Backend marks Agent OFFLINE after heartbeat timeout.
   — FR-4.5: Administrator can revoke an Agent credential.
   — FR-4.6: Administrator can rotate an Agent credential without 
     forcing full re-enrollment.

After reading those four documents, confirm:
   a) What the enrollment flow looks like end-to-end.
   b) Which fields the heartbeat POST body must include.
   c) What "Agent credential" means vs "user JWT" — they are 
      completely separate; do not mix them.
   d) Whether the backend agent endpoints are currently implemented 
      (they will be placeholders from Phase 8) — list what needs to 
      be built in the backend to support this agent.

=======================================================================
STEP 1 — BACKEND PREREQUISITE: Agent Endpoints
=======================================================================

The agent directory code cannot run until the backend can receive it.
The following backend endpoints are required and MUST be implemented 
before the agent can be tested end-to-end:

   POST /api/v1/agents/enrollment-token   (Administrator JWT required)
   POST /api/v1/agents/register           (enrollment token in body)
   POST /api/v1/agents/heartbeat          (agent credential required)
   GET  /api/v1/agents/tasks              (agent credential required)
   POST /api/v1/agents/tasks/{id}/status  (agent credential required)
   POST /api/v1/agents/results            (agent credential required)
   POST /api/v1/agents/{id}/revoke        (Administrator JWT required)
   POST /api/v1/agents/{id}/rotate-credential (Administrator JWT 
                                               required)

Agent credential authentication is separate from user JWT auth.
Implement a new FastAPI dependency — require_agent_credential() —
that validates the agent's credential token from the Authorization 
header. This must be different from require_role() used for humans.

Implement all endpoints in backend/app/api/v1/agents.py. All 
responses must match the exact schemas in docs/api/agent-api.md.
Write tests for the new backend endpoints in tests/test_agents.py 
before moving to the agent application itself.

=======================================================================
STEP 2 — AGENT PROJECT STRUCTURE
=======================================================================

Create the agent application in the agent/ directory at the repo root.
The structure must be:

agent/
├── main.py                  # Entry point — loads config, starts agent
├── config.py                # Configuration: backend URL, agent ID, 
│                            #   credential, intervals, log level
├── identity.py              # Reads/stores agent_id + credential from 
│                            #   local file (agent_identity.json)
├── enrollment.py            # Enrollment flow: POST /agents/register 
│                            #   using the enrollment token
├── api_client.py            # httpx-based client; handles auth header, 
│                            #   retry logic, error handling
├── collectors/
│   ├── __init__.py
│   ├── system_collector.py  # psutil: CPU %, RAM %, disk %, uptime
│   └── network_collector.py # psutil: network interfaces, bytes 
│                            #   sent/recv, connection count
├── heartbeat.py             # Sends POST /agents/heartbeat on interval
├── scheduler.py             # Runs heartbeat + collectors on timers
├── requirements.txt         # psutil, httpx, python-dotenv, schedule
├── .env.example             # BACKEND_URL, ENROLLMENT_TOKEN, LOG_LEVEL
└── README.md                # How to install, enroll, and run

Do NOT put agent code inside backend/. It is a separate application.
The agent/requirements.txt is independent from backend/requirements.txt.

=======================================================================
STEP 3 — CONFIGURATION AND IDENTITY
=======================================================================

Configuration (config.py):
   BACKEND_URL         — e.g. https://cybershield-ai-xnn7.onrender.com
   ENROLLMENT_TOKEN    — provided by Administrator from the dashboard
   AGENT_NAME          — friendly label for this machine
   HEARTBEAT_INTERVAL  — seconds between heartbeats (default: 30)
   COLLECTION_INTERVAL — seconds between system metric collection 
                         (default: 60)
   LOG_LEVEL           — INFO / DEBUG

Load from environment variables or a .env file using python-dotenv.
Never hard-code secrets. Never log the credential value.

Identity (identity.py):
   After successful enrollment, persist:
      {
        "agent_id": "<uuid>",
        "credential": "<raw_token>",
        "enrolled_at": "<iso_timestamp>"
      }
   to agent_identity.json (gitignored).
   
   On startup, if agent_identity.json exists, load it and skip 
   enrollment. If it does not exist, run enrollment.py first.
   
   The credential is the raw token returned by POST /agents/register.
   It is sent as: Authorization: Bearer <credential> on every 
   subsequent request.

=======================================================================
STEP 4 — ENROLLMENT FLOW
=======================================================================

enrollment.py must implement this exact flow:

1. Read ENROLLMENT_TOKEN and AGENT_NAME from config.
2. Send POST /api/v1/agents/register with body:
      {
        "enrollment_token": "<ENROLLMENT_TOKEN>",
        "name": "<AGENT_NAME>",
        "hostname": "<socket.gethostname()>",
        "version": "1.0.0",
        "status": "PENDING"
      }
3. On 201 Created: extract agent_id and credential token from response.
4. Write agent_identity.json with agent_id and credential.
5. Log "Agent enrolled successfully. ID: <agent_id>"
6. On any error (400, 401, 403, 409): log the error code and message, 
   raise an exception, and exit cleanly — do not retry enrollment 
   automatically as it may indicate a token already used or revoked.

=======================================================================
STEP 5 — API CLIENT
=======================================================================

api_client.py wraps httpx and must:

- Send Authorization: Bearer <credential> on every request.
- Handle transient failures (5xx, network timeout) with exponential 
  backoff, max 3 retries, before raising.
- On 401 Unauthorized: log "Credential rejected — agent may be revoked"
  and stop sending requests (do not retry 401s).
- Never log the credential value itself — log "<credential_present>" 
  as a placeholder if you need to confirm it is set.
- Use a configurable timeout (default: 10 seconds).

=======================================================================
STEP 6 — SYSTEM COLLECTOR
=======================================================================

collectors/system_collector.py using psutil:

def collect() -> dict:
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage_percent": psutil.disk_usage('/').percent,
        "uptime_seconds": int(time.time() - psutil.boot_time()),
        "network_status": "ok"     # elevated to "degraded" if any 
                                   # interface is down
    }

This dict is the "details" field in the heartbeat payload.

=======================================================================
STEP 7 — HEARTBEAT
=======================================================================

heartbeat.py must send POST /api/v1/agents/heartbeat with:

{
  "agent_id": "<from identity>",
  "timestamp": "<UTC ISO8601>",
  "status": "ONLINE",
  "version": "1.0.0",
  "cpu_percent": <from collector>,
  "memory_percent": <from collector>,
  "details": {
    "disk_usage_percent": <from collector>,
    "network_status": "ok"
  }
}

On success (200 OK): log "Heartbeat sent. Agent status: ONLINE"
On failure: log the error, do NOT crash the agent — just miss 
this heartbeat cycle and retry on the next interval.

=======================================================================
STEP 8 — SCHEDULER
=======================================================================

scheduler.py uses the schedule library to:
- Run heartbeat.send() every HEARTBEAT_INTERVAL seconds.
- Run system_collector.collect() every COLLECTION_INTERVAL seconds.

main.py ties it all together:
1. Load config.
2. Check for agent_identity.json — if missing, run enrollment.
3. Start scheduler loop.
4. Handle SIGINT / KeyboardInterrupt gracefully (log "Agent stopping").

=======================================================================
STEP 9 — WHAT IS OUT OF SCOPE FOR PHASE 9
=======================================================================

Do NOT implement any of the following in this phase. They are 
explicitly reserved for later phases:

- Nmap / device discovery (Phase 11)
- Vulnerability scanning (Phase 13)
- Log collection from auth.log / syslog (Phase 14)
- Threat detection rules (Phase 15)
- Any frontend UI changes (Phase 21)

The only collection in Phase 9 is CPU %, RAM %, disk %, and uptime 
from psutil. Nothing more.

=======================================================================
STEP 10 — TESTING REQUIREMENTS
=======================================================================

Before declaring Phase 9 complete:

1. tests/test_agents.py — backend endpoint tests:
   - POST enrollment-token returns token for Administrator.
   - POST register with valid token creates agent and returns credential.
   - POST register with expired/invalid token returns 401.
   - POST heartbeat with valid credential updates last_heartbeat_at.
   - POST heartbeat with invalid credential returns 401.
   - POST revoke by Administrator sets is_active=False.

2. Manual end-to-end test (document the output):
   a. Run: python -m uvicorn app.main:app (local backend).
   b. Get enrollment token via the API (or seed script).
   c. Set ENROLLMENT_TOKEN in agent/.env.
   d. Run: python agent/main.py
   e. Confirm in logs: "Agent enrolled successfully. ID: <uuid>"
   f. Confirm in logs: "Heartbeat sent. Agent status: ONLINE" 
      every 30 seconds.
   g. Hit GET /api/v1/agents/{agent_id} and confirm 
      last_heartbeat_at is recent.

=======================================================================
COMMIT MESSAGE
=======================================================================

"feat(agent): implement Phase 9 CyberShield Agent — enrollment, 
credential management, system collection, and heartbeat loop; 
implement agent backend endpoints and credential auth dependency"

=======================================================================
RULES
=======================================================================

- Never log credential values, enrollment tokens, or secrets.
- Agent credential (Bearer token) and user JWT are separate auth 
  systems — do not mix them up in the backend dependency chain.
- The agent/ directory is a standalone Python application — not part 
  of the FastAPI package.
- Do not implement future-phase features early.
- If any backend test fails, stop and report before proceeding.
- Write an implementation plan first — do not start coding until the 
  plan is approved.
```
