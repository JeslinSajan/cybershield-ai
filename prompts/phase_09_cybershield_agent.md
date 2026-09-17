# Phase 9 — CyberShield Agent

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 9: CyberShield Agent

Repo: https://github.com/JeslinSajan/cybershield-ai

IMPORTANT: The CyberShield Agent is NOT an AI agent.
It is a Python script that runs on a customer PC, collects basic 
system information, and sends it to the backend over HTTPS.

=======================================================================
WHAT TO BUILD
=======================================================================

A standalone Python application in the agent/ folder that:
  1. Enrolls itself with the backend using an enrollment token.
  2. Sends a heartbeat every 30 seconds (CPU%, RAM%, disk%).
  3. Saves its identity locally so it does not re-enroll on restart.

=======================================================================
STEP 1 — DATABASE MIGRATION (do this first)
=======================================================================

Check if Alembic migrations already cover these tables:
  - agents (table 6 in schema.md)
  - agent_credentials (table 7)
  - agent_heartbeats (table 8)
  - scans (table 11) ← needed in Phase 10 for task dispatch
  - scan_results (table 12) ← needed in Phase 10 for results upload

If any are missing: create a new Alembic migration that adds them.
Run: alembic upgrade head — confirm no errors.

=======================================================================
STEP 2 — BACKEND ENDPOINTS (build before the agent)
=======================================================================

Implement in backend/app/api/v1/agents.py:

POST /api/v1/agents/enrollment-token
  - Administrator JWT required (403 for Analyst/Viewer).
  - Generates a secure random one-time token.
  - Returns: { "token": "...", "expires_at": "..." }

POST /api/v1/agents/register
  - No JWT — uses the enrollment token in the request body.
  - Body: { enrollment_token, name, hostname, version, status }
  - Creates an agents row (status=PENDING) + agent_credentials row.
  - Returns: { agent_id, name, hostname, status, credential: { token } }
  - Write audit_log entry: action="agent_enrolled", actor_type="system"

POST /api/v1/agents/heartbeat
  - Agent credential (Bearer token) required — NOT a user JWT.
  - Body: { agent_id, timestamp, status, version, 
            cpu_percent, memory_percent, details:{disk_percent} }
  - Writes a row to agent_heartbeats table.
  - Updates agents.last_heartbeat_at and agents.status = ONLINE.
  - Returns: { agent_id, status, last_heartbeat_at }

GET /api/v1/agents/
  - Administrator or Analyst JWT required. Viewer: 403.
  - Returns all agents in the org with status and last_heartbeat_at.

GET /api/v1/agents/{agent_id}
  - Administrator or Analyst JWT required. Viewer: 403.
  - Returns single agent detail.

NOTE ON AUTH: The agent sends:  Authorization: Bearer <credential_token>
This is different from human JWTs. Create a separate FastAPI 
dependency called require_agent_credential() in app/core/deps.py that 
looks up the token in agent_credentials table.

=======================================================================
STEP 3 — FIRST ADMIN ENROLLMENT TOKEN (seed for demo)
=======================================================================

Add a management command or note in the README:
  To get the first enrollment token for a new agent, call:
  POST /api/v1/agents/enrollment-token
  with a valid Admin JWT (obtained from POST /api/v1/auth/login).

=======================================================================
STEP 4 — AGENT FOLDER STRUCTURE
=======================================================================

agent/
├── main.py            # Entry point — loads config, enrolls, runs loop
├── config.py          # Reads .env: BACKEND_URL, ENROLLMENT_TOKEN, etc.
├── identity.py        # Saves/loads agent_id and credential to a file
├── enrollment.py      # Calls POST /agents/register with the token
├── heartbeat.py       # Calls POST /agents/heartbeat with system stats
├── requirements.txt   # psutil, httpx, python-dotenv
└── .env.example       # BACKEND_URL, ENROLLMENT_TOKEN, AGENT_NAME

agent/ is a separate Python application. NOT part of the backend.

=======================================================================
STEP 5 — HOW THE AGENT WORKS
=======================================================================

1. Admin generates enrollment token via POST /agents/enrollment-token.
2. Admin puts the token in agent/.env as ENROLLMENT_TOKEN.
3. Run: python agent/main.py
4. Agent calls POST /agents/register → receives agent_id + credential.
5. Agent saves { agent_id, credential } to agent_identity.json 
   (this file is gitignored — never commit it).
6. Agent loops: every 30 seconds, POST /agents/heartbeat with 
   { cpu_percent, memory_percent, disk_percent } from psutil.
7. On restart: agent reads agent_identity.json and skips enrollment.

=======================================================================
STEP 6 — ERROR HANDLING IN AGENT
=======================================================================

- If backend is unreachable: log "Backend not reachable, retrying..." 
  and retry every 30 seconds. Do not crash.
- If 401 received: log "Credential rejected — contact admin." 
  and exit cleanly.
- Never log the credential token value itself.

=======================================================================
STEP 7 — NOT IN SCOPE FOR THIS PHASE
=======================================================================

Do NOT build: Nmap scanning, vulnerability detection, log collection,
threat detection, alerts, or any frontend changes.
Those are later phases.

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Start the local backend (uvicorn).
2. Login as Admin, call POST /agents/enrollment-token.
3. Copy the token to agent/.env.
4. Run: python agent/main.py
5. Confirm in terminal: "Agent enrolled. ID: <uuid>"
6. Confirm: "Heartbeat sent" appears every 30 seconds.
7. Call GET /api/v1/agents/{id} — confirm status=ONLINE and 
   last_heartbeat_at is recent.
8. Run: pytest tests/test_agents.py — all tests must pass.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat(agent): Phase 9 — agent application with enrollment and heartbeat"
```
