# Phase 25 — Performance & Reliability

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 25: Performance & Reliability

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

Make the system more reliable for the demo. Fix the most obvious 
performance issues. Keep changes minimal and safe.

Your development machine has 8GB RAM — keep everything lightweight.

=======================================================================
BACKEND FIXES
=======================================================================

1. DATABASE QUERIES — add missing indexes.
   Check these common queries and confirm indexes exist:
   - alerts filtered by organization_id + status
   - logs filtered by organization_id + timestamp
   - agent_heartbeats filtered by agent_id + timestamp
   - devices filtered by organization_id
   - vulnerabilities filtered by device_id
   
   Run EXPLAIN ANALYZE on slow queries in Neon's SQL editor to 
   identify any that do a full table scan. Add indexes where needed 
   via a new Alembic migration.

2. PAGINATION — add to all list endpoints.
   Every GET list endpoint must support:
     ?limit=50&offset=0  (default limit=50, max=200)
   This prevents the API from returning thousands of rows at once.
   Update any endpoints missing this.

3. HEARTBEAT CLEANUP — keep the agent_heartbeats table manageable.
   Add a background task that runs once daily and deletes 
   heartbeats older than 7 days.
   (agent_heartbeats can grow very fast — 30s × 60 × 24 = 2880 
   rows per agent per day)

4. AGENT RETRY ON STARTUP
   If the backend is not reachable when the agent starts, 
   the agent should retry connecting every 30 seconds instead 
   of crashing. Log: "Backend not reachable. Retrying in 30s..."

=======================================================================
FRONTEND FIXES
=======================================================================

1. Add loading spinners on all pages that fetch data.
2. Add error messages when API calls fail 
   (e.g. "Could not load devices. Check your connection.").
3. Auto-refresh the Dashboard every 60 seconds.
4. Auto-refresh the Agents page every 30 seconds 
   (so ONLINE/OFFLINE status updates without manual refresh).

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Start the agent before the backend — confirm it retries cleanly.
2. GET /api/v1/logs/?limit=10 — confirm only 10 rows returned.
3. Leave the system running for 10 minutes — confirm no memory 
   spikes or crashes.
4. pytest tests/ — no regressions.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 25 — performance improvements, pagination, heartbeat cleanup"
```
