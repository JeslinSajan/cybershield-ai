# Phase 12 — Network Monitoring

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> This prompt was written before execution. Before running it:  
> (1) Run `alembic current` — confirm Phase 11 migrations applied.  
> (2) Check `backend/app/models/agent.py` — AgentHeartbeat.details is JSONB. Network stats go into this field.  
> (3) Check if `device_interfaces` table exists. Create migration if not.  
> (4) Verify POST /agents/heartbeat implementation from Phase 9 — Phase 12 extends it.  
> Prompts are a living plan, not a frozen snapshot.

---

## Prompt

```text
CYBERSHIELD AI — PHASE 12: Network Monitoring

Repo: https://github.com/JeslinSajan/cybershield-ai

The agent extends its heartbeat to include network interface statistics.
The backend saves them to agent_heartbeats.details (JSONB) and upserts
them into the device_interfaces table when a device is linked.

=======================================================================
STEP 0 — READ FIRST (verify before executing)
=======================================================================

  backend/app/models/agent.py → AgentHeartbeat.details is Column(JSONB).
    Network stats will be stored here as {"interfaces": [...], "active_connections": N}.

  Check if device_interfaces table/model exists:
    Look in backend/app/models/ for a Device or DeviceInterface model.
    If device_interfaces model is missing: create it in backend/app/models/device.py:
      class DeviceInterface(Base):
          __tablename__ = "device_interfaces"
          id = Column(UUID, primary_key=True, default=uuid4)
          organization_id = Column(UUID, FK organizations.id, NOT NULL)
          device_id = Column(UUID, FK devices.id, NOT NULL)
          name = Column(String(80), NOT NULL)          # eth0, wlan0
          mac_address = Column(String(17), nullable=True)
          ip_address = Column(String(45), nullable=True)  # String, not INET, for test compat
          bytes_sent = Column(BigInteger, default=0)
          bytes_received = Column(BigInteger, default=0)
          created_at = Column(DateTime(timezone=True), server_default=func.now())
          updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    Create Alembic migration if added: alembic revision --autogenerate -m "phase12_device_interfaces"
    Then: alembic upgrade head

=======================================================================
STEP 1 — AGENT SIDE: NETWORK STATS COLLECTION
=======================================================================

  Update agent/heartbeat.py to include network stats in the heartbeat body:

    import psutil

    def collect_network_stats() -> dict:
        """
        Collect network interface stats using psutil.
        Returns:
          {
            "interfaces": [
              {
                "name": "eth0",
                "is_up": true,
                "bytes_sent": 102400,
                "bytes_received": 204800,
                "speed_mbps": 1000,
                "mac_address": "aa:bb:cc:dd:ee:ff"
              }
            ],
            "active_connections": 42
          }
        """
        counters = psutil.net_io_counters(pernic=True)
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        interfaces = []
        for name, io in counters.items():
            iface = {
                "name": name,
                "is_up": stats.get(name, {}).isup if hasattr(stats.get(name, {}), "isup") else False,
                "bytes_sent": io.bytes_sent,
                "bytes_received": io.bytes_recv,
                "speed_mbps": stats[name].speed if name in stats else 0,
                "mac_address": None
            }
            for addr in addrs.get(name, []):
                if addr.family.name == "AF_PACKET" or str(addr.family) == "AddressFamily.AF_PACKET":
                    iface["mac_address"] = addr.address
            interfaces.append(iface)
        try:
            connections = len(psutil.net_connections())
        except (psutil.AccessDenied, PermissionError):
            connections = -1  # Not available on some platforms without sudo
        return {"interfaces": interfaces, "active_connections": connections}

  Update the heartbeat payload in heartbeat.py:
    payload = {
        "agent_id": identity.agent_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ONLINE",
        "version": config.AGENT_VERSION,
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "details": {
            "disk_usage_percent": psutil.disk_usage("/").percent,
            "network": collect_network_stats()   # ← new field
        }
    }

=======================================================================
STEP 2 — BACKEND SIDE: SAVE NETWORK STATS
=======================================================================

  In the POST /agents/heartbeat handler (backend/app/api/v1/agents.py):

  The heartbeat is already saved to AgentHeartbeat with details=JSONB.
  The network stats arrive nested inside details["network"].

  Additionally, upsert into device_interfaces:
    1. Find any Device where agent_id == heartbeat agent and deleted_at IS NULL.
       If no device is linked yet: skip the upsert silently.
    2. For each interface in details["network"]["interfaces"]:
       Upsert DeviceInterface:
         WHERE organization_id = agent.org, device_id = device.id, name = iface["name"]
         ON CONFLICT: update bytes_sent, bytes_received, updated_at
         IF NOT EXISTS: insert with all fields.

  Use SQLAlchemy merge/upsert or query-then-update pattern.
  The upsert should NOT fail if device_interfaces doesn't exist yet — wrap in try/except.

=======================================================================
STEP 3 — BACKEND ENDPOINT: GET /agents/{agent_id}/network-stats
=======================================================================

  (Already specified in Phase 10 Step 5. Verify it's implemented.)
  If not implemented: add it now.

  Auth: Depends(get_current_analyst_or_admin)
  Returns: last 10 AgentHeartbeat rows ordered by timestamp DESC
  Only include rows where details is not None.
  Response: [{id, timestamp, cpu_percent, memory_percent, details}]

=======================================================================
STEP 4 — DEPENDENCY VERSIONS
=======================================================================

  psutil is already in agent/requirements.txt from Phase 9.
  Confirm the pinned version: psutil==5.9.8
  No new backend dependencies needed for this phase.

=======================================================================
VERIFICATION CHECKLIST — REQUIRED EVIDENCE BEFORE MARKING DONE
=======================================================================

[ ] alembic current — paste output confirming device_interfaces table exists
[ ] pytest tests/ -v --tb=short — paste output, 0 regressions
[ ] Run agent — paste a heartbeat log entry showing network stats are included.
    The log line should show cpu_percent and the word "network" in the payload.
[ ] curl GET /api/v1/agents/<id>/network-stats with Analyst JWT:
    Paste the response showing at least 1 heartbeat with interface data in details.
[ ] Viewer JWT + GET /api/v1/agents/<id>/network-stats — paste 403 response.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 12 — network interface stats in heartbeat, device_interfaces upsert"

Do not force-push.
```
