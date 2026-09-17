# Phase 12 — Network Monitoring

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 12: Network Monitoring

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

The agent collects network interface statistics using psutil and 
sends them to the backend. The backend stores them. The dashboard 
will show basic network health info for each online agent.

=======================================================================
AGENT SIDE
=======================================================================

Update agent/collectors/network_collector.py to collect:

  def collect_network_stats() -> dict:
      """
      Using psutil.net_io_counters(pernic=True) and 
      psutil.net_if_stats():
      Return:
        {
          "interfaces": [
            {
              "name": "eth0",
              "is_up": true,
              "bytes_sent": 102400,
              "bytes_recv": 204800,
              "packets_sent": 500,
              "packets_recv": 1000,
              "speed_mbps": 1000
            }
          ],
          "active_connections": <count from psutil.net_connections()>
        }
      """

Include this in the heartbeat payload under a "network" key.
Update POST /agents/heartbeat body to include the network stats.

=======================================================================
BACKEND SIDE
=======================================================================

Update the heartbeat handler to save the network stats from the 
heartbeat into two places:

1. agent_heartbeats.details JSONB column 
   (for quick health display on the agents page)

2. device_interfaces table (schema table 10)
   When a heartbeat arrives with interface stats:
   - Look up the device linked to this agent (if any).
   - For each interface in the payload:
       Upsert a device_interfaces row:
         organization_id, device_id, name, mac_address,
         bytes_sent, bytes_received (updated each heartbeat).
   - If no device is linked yet: skip this step silently.

Add a new endpoint:
  GET /api/v1/agents/{agent_id}/network-stats
    - Returns last 10 heartbeats with network details.
    - Administrator and Analyst only (Viewer gets 403).

=======================================================================
WHAT THIS ENABLES
=======================================================================

The dashboard (Phase 21) will use this data to show:
  - Which network interfaces are up/down per agent.
  - Bytes sent/received over time.
  - Number of active network connections.

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Run the agent and confirm network stats appear in heartbeat logs.
2. Call GET /agents/{id}/network-stats and confirm data is returned.
3. pytest tests/ — no regressions.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 12 — network monitoring stats in agent heartbeat"
```
