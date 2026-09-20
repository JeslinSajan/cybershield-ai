# Phase 17 — Risk Scoring

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> This prompt was written before execution. Before running it:
> (1) Run `alembic current` — confirm which migrations are applied.
> (2) Check `backend/app/api/v1/` — note which endpoints already exist.
> (3) Check `tests/` — note which test files already exist.
> (4) If reality differs from this prompt's assumptions, update this file first, then execute.
> Prompts are a living plan, not a frozen snapshot.

---

## Prompt

**Scope:**
1. **Risk Scoring Logic (backend/app/services/risk_service.py)**:
   - Implement `calculate_device_risk(db, device_id, org_id)`.
   - Formula:
     - `vulnerability_score`: Critical +30 (max 30), High +15 (max 30), Medium +5 (max 15), Low +2 (max 5).
     - `alert_score`: Open brute_force +20, Open suspicious_login +15, Open port_scan +10.
     - `exposure_score`: 10+ open ports in latest scan result for device = +10.
     - Total score is capped at 100.
     - Bands: 0-24=Low, 25-49=Medium, 50-74=High, 75-100=Critical.
   - **Crucial**: `RiskScore.factor_breakdown` is `Column(Text)`. Store it using `json.dumps(dict)`. Do NOT pass a dictionary directly to SQLAlchemy.
   - `RiskScore` columns: `organization_id`, `entity_type`='device', `entity_id`=device_id, `score`, `risk_band`, `factor_breakdown`, `formula_version`='v1'.
2. **Triggers**: Recalculate when:
   - New `Vulnerability` added for a device.
   - `Alert` created for a device.
   - `Alert` status changes to Resolved/False Positive.
3. **Endpoints**:
   - `GET /api/v1/devices/{id}/risk`: Role: `get_any_authenticated_user`. Returns the latest `RiskScore` row.
   - `GET /api/v1/risk-scores/`: Role: `get_any_authenticated_user`. Returns all device risk scores, sorted by score descending. Document this new endpoint in `docs/api/`.

**Rules & Constraints:**
- Adhere to the error envelope.
- Use `get_any_authenticated_user`.
- Test against Neon DB.

**Verification Checklist:**
- [ ] Show output from a script triggering a recalculation and proving the breakdown is stored as JSON string.
- [ ] Provide `curl` output for `GET /api/v1/devices/{id}/risk`.
