# Phase 11 — Device Discovery

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 11: Device Discovery

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

The agent scans the local network using Nmap and reports discovered 
devices to the backend. The backend stores them. The result is a 
visible device list.

=======================================================================
AGENT SIDE
=======================================================================

Add agent/collectors/network_scanner.py using python-nmap:

  def discover_devices(target_network: str) -> list:
      """
      Run: nmap -sn <target_network>   (ping scan, no port scan yet)
      For each host found, return:
        { ip_address, mac_address, hostname, vendor, status: "online" }
      """

- target_network comes from a task sent by the backend 
  (e.g. "192.168.1.0/24").
- When the agent receives a task with scan_type = "discovery":
    1. Run discover_devices(task.target_scope)
    2. POST results to /agents/results with result_type = "discovery"
    3. Mark task COMPLETED.

Add python-nmap to agent/requirements.txt.
Nmap must be installed on the machine running the agent.

=======================================================================
BACKEND SIDE
=======================================================================

When a discovery result arrives at POST /agents/results:
  - Parse the raw_payload (list of discovered devices).
  - For each device in the list:
      - Check if device with same ip_address already exists in this org.
      - If exists: update last_seen_at, status = "online".
      - If new: create a new devices row with all available fields.

Implement GET /api/v1/devices/ and GET /api/v1/devices/{id}:
  - Admin, Analyst, AND Viewer: all three roles can read devices.
  - Returns: ip_address, mac_address, hostname, vendor, status, 
    last_seen_at, agent_id.

Also implement POST /api/v1/scans/ so Admin/Analyst can create a 
discovery scan task that gets dispatched to an online agent:
  - Administrator and Security Analyst only (Viewer gets 403).
  - Body: { agent_id, scan_type: "discovery", target_scope: "192.168.1.0/24",
            created_by_user_id: <from JWT> }
  - All fields: organization_id (from JWT), agent_id, created_by_user_id,
    scan_type, status=PENDING, target_scope.
  - Creates a scans row. Agent picks it up via GET /agents/tasks.

Also create device_interfaces rows when device has network interfaces:
  - Table: device_interfaces (schema table 10)
  - Columns: organization_id, device_id, name (e.g. eth0), mac_address,
    ip_address, bytes_sent=0, bytes_received=0
  - Create one device_interfaces row per interface Nmap reports.

=======================================================================
HOW IT FLOWS
=======================================================================

Admin → POST /scans/ (scan_type=discovery, target=192.168.1.0/24)
     → Backend creates scan record, status=PENDING
     → Agent polls GET /agents/tasks, picks it up
     → Agent runs Nmap ping scan
     → Agent POSTs results to /agents/results
     → Backend parses results, creates/updates device rows
     → Admin/Analyst sees device list at GET /devices/

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Create a discovery scan task via the API.
2. Confirm the agent picks it up and runs Nmap.
3. Confirm devices appear in GET /api/v1/devices/.
4. Run the scan again — confirm existing devices are updated, 
   not duplicated.
5. pytest tests/ — no regressions.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 11 — device discovery via Nmap agent scan"
```
