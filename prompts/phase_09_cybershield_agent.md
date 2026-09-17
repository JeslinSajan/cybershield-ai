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
system information, and sends it to the backend.

=======================================================================
WHAT TO BUILD
=======================================================================

A standalone Python application in the agent/ folder that:
  1. Enrolls itself with the backend using an enrollment token.
  2. Sends a heartbeat every 30 seconds (CPU%, RAM%, disk%).
  3. Saves its identity locally so it does not re-enroll on restart.

That is all for Phase 9. Nothing else.

=======================================================================
BACKEND WORK NEEDED FIRST
=======================================================================

The following backend endpoints must be implemented in 
backend/app/api/v1/agents.py before the agent can work:

  POST /api/v1/agents/enrollment-token
    - Admin only (JWT required)
    - Generates a one-time token the agent uses to register
    - Returns: { "token": "...", "expires_at": "..." }

  POST /api/v1/agents/register
    - No JWT — uses the enrollment token in the request body
    - Creates the agent record in the database
    - Returns: { "agent_id": "...", "credential": "..." }

  POST /api/v1/agents/heartbeat
    - Uses agent credential (Bearer token) for auth
    - Saves heartbeat to database, updates agent status to ONLINE
    - Returns: { "status": "ONLINE" }

Also implement:
  GET /api/v1/agents/         (Admin/Analyst only — list all agents)
  GET /api/v1/agents/{id}     (Admin/Analyst only — single agent)

=======================================================================
AGENT FOLDER STRUCTURE
=======================================================================

agent/
├── main.py            # Start here — loads config, enrolls, runs loop
├── config.py          # Reads .env: BACKEND_URL, ENROLLMENT_TOKEN, etc.
├── identity.py        # Saves/loads agent_id and credential to a file
├── enrollment.py      # Calls POST /agents/register
├── heartbeat.py       # Calls POST /agents/heartbeat with system stats
├── requirements.txt   # psutil, httpx, python-dotenv
└── .env.example       # BACKEND_URL, ENROLLMENT_TOKEN, AGENT_NAME

=======================================================================
HOW IT WORKS
=======================================================================

1. Admin generates enrollment token from the backend (API or script).
2. Admin puts the token in agent/.env as ENROLLMENT_TOKEN.
3. Run: python agent/main.py
4. Agent calls POST /agents/register → gets agent_id + credential.
5. Agent saves agent_id + credential to agent_identity.json.
6. Agent starts sending heartbeat every 30 seconds with:
     { cpu_percent, memory_percent, disk_percent }
7. On restart, agent reads agent_identity.json and skips enrollment.

=======================================================================
WHAT NOT TO BUILD IN THIS PHASE
=======================================================================

Do NOT build: Nmap scanning, vulnerability detection, log collection,
threat detection, alerts, or any frontend changes.
Those are later phases.

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Start the local backend.
2. Generate an enrollment token (via API or seed script).
3. Set ENROLLMENT_TOKEN in agent/.env.
4. Run: python agent/main.py
5. Confirm in terminal: "Agent enrolled. ID: <uuid>"
6. Confirm: "Heartbeat sent" appears every 30 seconds.
7. Call GET /api/v1/agents/{id} and confirm last_heartbeat_at updates.
8. Run: pytest tests/test_agents.py — all tests must pass.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat(agent): Phase 9 — basic agent with enrollment and heartbeat"
```
