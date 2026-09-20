# Phase 17 — Risk Scoring

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*
---

> **STANDING RULE — VERIFY BEFORE EXECUTING**
> Before running this prompt, re-read the actual current state of the repo:
> (1) Check which backend endpoints already exist in backend/app/api/v1/.
> (2) Check which Alembic migrations have already been run (alembic current).
> (3) Check which tests already exist in tests/.
> (4) If the real repo state differs from what this prompt assumes — update
>     this prompt file FIRST, then execute it. Prompts are a living plan,
>     not a frozen snapshot.

---

## Prompt

```text
CYBERSHIELD AI — PHASE 17: Risk Scoring

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

Calculate a risk score (0–100) for each device. The formula must be 
simple, documented, and explainable — important for your college demo.

=======================================================================
RISK FORMULA (document this exactly as shown)
=======================================================================

Risk Score = (Vulnerability Score + Alert Score + Exposure Score)
             capped at 100.

Vulnerability Score:
  Critical vulnerability: +30 points each (max 30)
  High vulnerability:     +15 points each (max 30)
  Medium vulnerability:   +5 points each  (max 15)
  Low vulnerability:      +2 points each  (max 5)

Alert Score:
  Open BruteForce alert:       +20 points
  Open PortScan alert:         +10 points
  Open SuspiciousLogin alert:  +15 points

Exposure Score:
  More than 10 open ports on device: +10 points
  Device has no firewall detected:   +5 points

Score Bands:
  0–24:  Low
  25–49: Medium
  50–74: High
  75–100: Critical

=======================================================================
WHEN TO CALCULATE
=======================================================================

Recalculate a device's risk score:
  - When new vulnerabilities are added for that device.
  - When a new alert is created for that device.
  - When an alert is resolved (score may go down).

Store the result in the risk_scores table (schema table 19).
IMPORTANT: use the exact column names from the schema:
  organization_id,
  entity_type = "device",
  entity_id = <device UUID>,
  score = <calculated value>,
  risk_band = "Low" / "Medium" / "High" / "Critical",
  factor_breakdown (JSONB) = {
    "vulnerability_score": 30,
    "alert_score": 20,
    "exposure_score": 10,
    "total": 60,
    "details": {
      "critical_vulns": 1,
      "open_brute_force_alerts": 1,
      "open_ports": 12
    }
  },
  formula_version = "v1"   ← REQUIRED field, do not omit

factor_breakdown must store the individual components so the 
AI assistant (Phase 19) can explain them:
  {
    "vulnerability_score": 30,
    "alert_score": 20,
    "exposure_score": 10,
    "total": 60,
    "band": "High",
    "details": {
      "critical_vulns": 1,
      "open_brute_force_alerts": 1,
      "open_ports": 12
    }
  }

=======================================================================
BACKEND ENDPOINTS
=======================================================================

GET /api/v1/devices/{id}/risk
  - Returns the latest risk score for the device.
  - All roles (read).

GET /api/v1/risk-scores/
  - Returns risk scores for all devices in the org.
  - Sorted by score descending (highest risk first).
  - All roles (read).

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Create a device with 1 Critical vulnerability and 1 open 
   BruteForce alert.
2. Trigger risk recalculation.
3. GET /devices/{id}/risk — confirm score = 50 (30+20) band = "High".
4. Resolve the alert — confirm score drops to 30, band = "Medium".
5. pytest tests/ — no regressions.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 17 — transparent risk scoring with factor breakdown"
```
