# Phase 11 — Device Discovery

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> This prompt was written before execution. Before running it:  
> (1) Run `alembic current` — confirm Phase 9/10 migrations are applied.  
> (2) Check `backend/app/api/v1/devices.py` — already a stub; fill it in, do not recreate.  
> (3) Check `backend/app/models/device.py` — review actual column names before coding.  
> (4) Check `backend/app/api/v1/scans.py` — already a stub; POST /scans/ goes here.  
> (5) Verify docs/api/ has device and scan endpoints documented. Add if missing.  
> Prompts are a living plan, not a frozen snapshot.

---

## Prompt

```text
CYBERSHIELD AI — PHASE 11: Device Discovery

Repo: https://github.com/JeslinSajan/cybershield-ai

The agent scans the local network using Nmap, reports discovered
devices to the backend, and the backend stores them in the devices
table. Result: a visible, live device list in the system.

=======================================================================
STEP 0 — READ FIRST (verify before executing)
=======================================================================

  backend/app/models/device.py — read actual column names.
    Likely columns: id, organization_id, agent_id, ip_address, mac_address,
    hostname, vendor, device_type, status, last_seen_at, created_at,
    updated_at, deleted_at.
    Verify against the actual file. Do NOT use schema.md as the sole source.
    If the model file is a stub or missing columns, update the model and
    create an Alembic migration before coding the endpoints.

  backend/app/models/system.py or a separate device_interfaces model:
    Check if device_interfaces table/model exists.
    If not, create it: id, organization_id, device_id, name, mac_address,
    ip_address (INET stored as String for SQLite compatibility in tests),
    bytes_sent, bytes_received, created_at, updated_at.

  docs/api/ — check if device and scan endpoints are documented.
    If not: create docs/api/devices-api.md and docs/api/scans-api.md
    following the same format as docs/api/agent-api.md.

  alembic/versions/ — run alembic current. Confirm devices and
    device_interfaces tables exist. Create migration if not.

=======================================================================
STEP 1 — DATABASE MIGRATION
=======================================================================

  Run: alembic current

  Required tables: devices, device_interfaces, scans, scan_results
  If any missing: alembic revision --autogenerate -m "phase11_device_discovery"
  Then: alembic upgrade head

=======================================================================
STEP 2 — AGENT SIDE: NETWORK SCANNER
=======================================================================

  Add agent/collectors/network_scanner.py:

    import nmap  # python-nmap

    def discover_devices(target_network: str) -> dict:
        """
        Run Nmap ping scan: nmap -sn <target_network>
        Returns:
          {
            "target_network": "192.168.1.0/24",
            "hosts": [
              {
                "ip_address": "192.168.1.10",
                "mac_address": "aa:bb:cc:dd:ee:ff",
                "hostname": "device-hostname",
                "vendor": "Intel Corporate",
                "status": "online"
              }
            ]
          }
        """
        nm = nmap.PortScanner()
        nm.scan(hosts=target_network, arguments='-sn')
        hosts = []
        for host in nm.all_hosts():
            info = {
                "ip_address": host,
                "mac_address": nm[host]["addresses"].get("mac", None),
                "hostname": nm[host].hostname() or None,
                "vendor": (list(nm[host]["vendor"].values())[0]
                           if nm[host].get("vendor") else None),
                "status": "online" if nm[host].state() == "up" else "offline"
            }
            hosts.append(info)
        return {"target_network": target_network, "hosts": hosts}

  Add to agent/task_poller.py — handle scan_type = "discovery":
    def handle_discovery(task_id: str, api_client, target_scope: str):
        api_client.post(f"/agents/tasks/{task_id}/status", {"status": "RUNNING"})
        result = discover_devices(target_scope)
        # The result needs a device_id — but we don't have one yet.
        # Use a placeholder device_id or POST results without device_id
        # and let the backend handle it.
        # Actually: POST /agents/results with device_id=None initially.
        # Backend creates device rows and associates them.
        api_client.post("/agents/results", {
            "scan_id": task_id,
            "device_id": None,
            "result_type": "discovery",
            "raw_payload": result
        })
        api_client.post(f"/agents/tasks/{task_id}/status", {"status": "COMPLETED"})

  Add python-nmap to agent/requirements.txt with pinned version:
    python-nmap==0.7.1

  NOTE: Nmap must be installed on the OS. Document in agent/INSTALL.md:
    Linux: sudo apt install nmap
    Windows: https://nmap.org/download.html
    macOS: brew install nmap

=======================================================================
STEP 3 — BACKEND: PROCESS DISCOVERY RESULTS
=======================================================================

  In backend/app/api/v1/agents.py (or a new service file),
  after saving a ScanResult with result_type='discovery':

    def process_discovery_result(db, scan_result, agent):
        """Parse discovery payload and upsert device rows."""
        payload = scan_result.raw_payload
        hosts = payload.get("hosts", [])
        for host in hosts:
            ip = host.get("ip_address")
            if not ip:
                continue
            # Upsert: unique on (organization_id, ip_address)
            existing = db.query(Device).filter(
                Device.organization_id == agent.organization_id,
                Device.ip_address == ip,
                Device.deleted_at.is_(None)
            ).first()
            if existing:
                existing.last_seen_at = datetime.utcnow()
                existing.status = host.get("status", "unknown")
                existing.hostname = host.get("hostname") or existing.hostname
                existing.mac_address = host.get("mac_address") or existing.mac_address
                existing.vendor = host.get("vendor") or existing.vendor
            else:
                device = Device(
                    organization_id=agent.organization_id,
                    agent_id=agent.id,
                    ip_address=ip,
                    mac_address=host.get("mac_address"),
                    hostname=host.get("hostname"),
                    vendor=host.get("vendor"),
                    status=host.get("status", "unknown"),
                    last_seen_at=datetime.utcnow()
                )
                db.add(device)
        db.commit()

  Call process_discovery_result() at the end of the POST /agents/results handler
  when result_type == 'discovery'.

=======================================================================
STEP 4 — BACKEND: SCAN CREATION ENDPOINT
=======================================================================

  File: backend/app/api/v1/scans.py (stub exists)
  Auth: Depends(get_current_analyst_or_admin)
  FR: FR-5.1

  POST /api/v1/scans/
    Body: {agent_id: UUID, scan_type: str, target_scope: str}
    Allowed scan_type values: "discovery", "vulnerability", "health_check"
    Logic:
      1. Verify the agent exists, is_active=True, belongs to user's org. 404/403 if not.
      2. Verify agent.status == 'ONLINE'. 400 if OFFLINE/PENDING.
         Error: {"error": {"code": "AGENT_OFFLINE", "message": "Agent is not online.", "details": []}}
      3. Create Scan row:
           organization_id (from JWT user's org),
           agent_id, created_by_user_id (from JWT user.id),
           scan_type, status='PENDING', target_scope
      4. Write AuditLog: action='scan_created', actor_type='user', actor_id=user.id,
           target_type='scans', target_id=scan.id
      5. Return scan: {id, agent_id, scan_type, status, target_scope, created_at}
    Status: 201 Created

  GET /api/v1/scans/
    Auth: Depends(get_current_analyst_or_admin)
    Returns list of scans for the org. Filter: ?status=PENDING&limit=50&offset=0.

  GET /api/v1/scans/{scan_id}
    Auth: Depends(get_current_analyst_or_admin)
    Returns single scan with status.

=======================================================================
STEP 5 — BACKEND: DEVICE ENDPOINTS
=======================================================================

  File: backend/app/api/v1/devices.py (stub exists)

  GET /api/v1/devices/
    Auth: Depends(get_any_authenticated_user)  — all 3 roles can read
    FR: FR-6.1
    Filter: ?status=online&limit=50&offset=0
    Returns devices where deleted_at IS NULL and org matches.
    Response fields: id, ip_address, mac_address, hostname, vendor,
                     device_type, status, last_seen_at, agent_id, created_at

  GET /api/v1/devices/{device_id}
    Auth: Depends(get_any_authenticated_user)
    Returns single device. 404 if not found or wrong org.

  Document both endpoints in docs/api/devices-api.md.
  Create this file if it doesn't exist.

=======================================================================
STEP 6 — AUTHORIZATION WARNING IN UI (note for Phase 21)
=======================================================================

  Add a comment to the scan creation endpoint:
  # IMPORTANT: This endpoint initiates a network scan. Only scan networks
  # for which you have explicit written authorization. Unauthorized scanning
  # is illegal in most jurisdictions. The UI (Phase 21) must display a
  # confirmation dialog before triggering this endpoint.

=======================================================================
VERIFICATION CHECKLIST — REQUIRED EVIDENCE BEFORE MARKING DONE
=======================================================================

[ ] alembic current — paste output confirming devices, device_interfaces tables exist
[ ] pytest tests/test_devices.py -v — paste output, 0 failures
[ ] pytest tests/ -v --tb=short — paste output, 0 regressions
[ ] Create a discovery scan via API:
    curl -X POST http://localhost:8000/api/v1/scans/ \
      -H "Authorization: Bearer <analyst JWT>" \
      -d '{"agent_id":"<uuid>","scan_type":"discovery","target_scope":"192.168.1.0/24"}'
    Paste the response showing scan created with status=PENDING.
[ ] Run the agent — paste terminal output showing the task was picked up.
[ ] curl GET /api/v1/devices/ — paste response showing at least 1 discovered device.
[ ] Run scan twice — confirm existing devices are updated, not duplicated.
    curl GET /api/v1/devices/ and verify count stays the same for same network.
[ ] Viewer JWT + GET /api/v1/devices/ — paste 200 response (Viewer CAN read devices).
[ ] Viewer JWT + POST /api/v1/scans/ — paste 403 response.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 11 — device discovery via Nmap, scan creation, device endpoints"

Do not force-push.
```
