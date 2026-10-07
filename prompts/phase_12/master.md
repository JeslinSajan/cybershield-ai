# Phase 12 — Network Monitoring

**Status:** In Progress  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> This prompt was written before execution. Before running it:  
> (1) Run `alembic current` — confirm Phase 11 migrations applied.  
> (2) Check `backend/app/models/agent.py` — AgentHeartbeat.details is JSONB. Network stats go into this field.  
> (3) Check if `device_interfaces` table exists in schema/model.  
> (4) Verify POST /agents/heartbeat implementation from Phase 9/10 — Phase 12 extends it.  
> Prompts are a living plan, not a frozen snapshot.
> **Standards:** Follow [`prompts/00_shared_standards.md`](../00_shared_standards.md) — all S1–S9 rules apply to this phase.

---

## DEPENDS ON
Phase 9: `AgentHeartbeat.details` is JSONB; Phase 11: `DeviceInterface` model and table confirmed

## PRODUCES
Network stats in `agent_heartbeats.details["network"]`; upserted `device_interfaces` rows; `GET /agents/{id}/network-stats` endpoint

**Consumed by:** Phase 21 (network stats display)

## HANDOFF REQUIREMENT
On completing this phase, append an entry to `prompts/HANDOFF.md`.
Append network stats payload shape (`{interfaces: [...], active_connections: N}`) and interface columns used in upsert to `prompts/HANDOFF.md`.

---
## Prompt

```text
CYBERSHIELD AI — PHASE 12: Network Monitoring

Repo: https://github.com/JeslinSajan/cybershield-ai

The agent extends its heartbeat to include network interface statistics.
The backend saves them to agent_heartbeats.details (JSONB) and upserts
them into the device_interfaces table when a device is linked.
```
