# Phase 15 — Threat Detection

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 15: Threat Detection

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

The backend analyzes the collected logs and automatically creates 
alerts when it detects suspicious patterns. No ML required — 
use simple rules and thresholds.

=======================================================================
DETECTION RULES TO IMPLEMENT
=======================================================================

Implement these 3 rules in backend/app/services/detection_service.py:

RULE 1 — Brute Force Detection:
  If the same source_ip has 5+ login_failure events within 
  the last 10 minutes for the same device/agent → create a 
  "Brute Force" alert.

RULE 2 — Port Scan Detection:
  If a scan result shows 10+ open ports on a single device → 
  create a "Port Scan Detected" alert.

RULE 3 — Suspicious Login:
  If a login_success event comes from a source_ip that has 
  also had 3+ login_failure events in the last hour → 
  create a "Suspicious Login" alert (possible successful 
  brute force).

=======================================================================
WHEN DO RULES RUN
=======================================================================

Run detection automatically:
  - After new logs are saved (trigger from POST /agents/logs handler).
  - After new scan results are saved (trigger from POST /agents/results).

Do NOT run detection as a separate background task — keep it simple.
Just call detection_service.run_detection(agent_id, org_id) at the 
end of the log/result save handlers.

=======================================================================
BACKEND — DETECTION SERVICE
=======================================================================

backend/app/services/detection_service.py:

  def run_detection(db, agent_id, organization_id):
      check_brute_force(db, agent_id, organization_id)
      check_port_scan(db, agent_id, organization_id)
      check_suspicious_login(db, agent_id, organization_id)

  def check_brute_force(db, agent_id, organization_id):
      # Query logs table: group by source_ip where event_type = 
      # "login_failure" and timestamp > now() - 10 minutes.
      # If count >= 5 for any source_ip: create alert.
      # Avoid duplicate alerts: check if a Brute Force alert 
      # for this source_ip already exists in the last hour.

  # Similar logic for check_port_scan and check_suspicious_login.

=======================================================================
ALERT CREATION
=======================================================================

Create a new alert row in the alerts table with:
  organization_id (from agent's org),
  agent_id,
  device_id (if known),
  alert_type — use EXACT values from schema:
    "brute_force"       for Rule 1
    "port_scan"         for Rule 2
    "suspicious_login"  for Rule 3
  severity:
    "High" for brute_force,
    "Medium" for port_scan,
    "High" for suspicious_login,
  status = "Open",
  description (a clear human-readable explanation with actual numbers),
  risk_score — set an initial value using this simple formula:
    High severity alert   = 40
    Medium severity alert = 20
    Low severity alert    = 10
    (Risk Scoring in Phase 17 will recalculate this properly)
  triggered_at = now()

After creating the alert, write an audit_log entry:
  action = "alert_created",
  actor_type = "system",
  target_type = "alerts",
  target_id = <new alert id>

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Insert 6 fake login_failure log entries from the same IP 
   via the API.
2. Trigger detection — confirm a Brute Force alert is created.
3. Insert a scan result with 15 open ports — confirm Port Scan 
   alert is created.
4. Confirm duplicate alerts are not created if the rule fires twice.
5. pytest tests/ — no regressions.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 15 — threat detection rules (brute force, port scan, suspicious login)"
```
