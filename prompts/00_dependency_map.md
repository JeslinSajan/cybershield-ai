# CyberShield AI — Phase Dependency Map (Phases 9–27)

> **Living document.** Update the "Status" column when a phase is completed.  
> Read `prompts/HANDOFF.md` for the actual produced artifacts — this map
> shows the *planned* dependencies; HANDOFF.md shows the *real* ones.

---

## Dependency Table

| Phase | Title | Depends On | Produces | Consumed By | Verified By |
|---|---|---|---|---|---|
| **9** | CyberShield Agent | Phase 7/8: `get_current_admin`, `get_current_analyst_or_admin`, `get_any_authenticated_user` deps; `agents`, `agent_credentials`, `agent_heartbeats` tables from migration 001; `AuditLog` model | `require_agent_credential()` in `deps.py`; `Agent`/`AgentCredential`/`AgentHeartbeat` rows in DB; `agent/` Python app (enrollment, heartbeat); `POST /agents/register`, `POST /agents/heartbeat`, `GET /agents/`, `GET /agents/{id}`, `POST /agents/enrollment-token` endpoints; DB pool resilience in `database.py` | 10, 21 | `tests/test_agents.py`; live `GET /agents/{id}` showing ONLINE |
| **10** | Agent ↔ Backend Integration | Phase 9: `require_agent_credential()`, Agent rows in DB, `agent/api_client.py` | `GET /agents/tasks`, `POST /agents/tasks/{id}/status`, `POST /agents/results`, `POST /agents/{id}/rotate-credential` endpoints; `agent/task_poller.py`; `agent/offline_queue.py`; idempotent result upload (`upload_id` column on `scan_results`) | 11, 13, 14 | `tests/test_agents.py` (task dispatch tests); live task end-to-end |
| **11** | Device Discovery | Phase 9/10: agent running, `POST /agents/results` working, `Scan` + `ScanResult` models; `devices` table migration | Device rows in DB after discovery scan; `GET /devices/`, `GET /devices/{id}`, `POST /scans/` endpoints; `device_interfaces` table; `process_discovery_result()` service function | 12, 13, 17, 21 | `tests/test_devices.py`; `GET /devices/` returning ≥1 device |
| **12** | Network Monitoring | Phase 9: `AgentHeartbeat.details` JSONB; Phase 11: `device_interfaces` table and model | Network stats in `agent_heartbeats.details["network"]`; updated `device_interfaces` rows on each heartbeat; `GET /agents/{id}/network-stats` endpoint | 21 | Heartbeat log showing "network" key; `GET /agents/{id}/network-stats` response |
| **13** | Vulnerability Scanning | Phase 10: `POST /agents/results` working; Phase 11: `Device` rows exist; `CVE` + `Vulnerability` models from migration 001; `upload_id` column on `scan_results` (Phase 10) | `Vulnerability` rows in DB; CVE seed data in `backend/data/cve_seed.json` (15 entries); `GET /vulnerabilities/`, `GET /vulnerabilities/{id}`, `GET /devices/{id}/vulnerabilities` endpoints | 15, 16, 17, 19, 21 | `tests/test_vulnerabilities.py`; `GET /vulnerabilities/` with ≥1 CVE match |
| **14** | Log Management | Phase 9/10: `require_agent_credential()`, agent running; `logs` table migration; Phase 11 (optional): `Device` rows for device_id linking | `Log` rows in DB; `POST /agents/logs` endpoint (agent auth); `GET /logs/`, `GET /logs/{id}` endpoints (JWT auth); agent `collectors/log_collector.py` | 15, 18, 21 | `tests/test_logs.py`; `GET /logs/` with login_failure events |
| **15** | Threat Detection | Phase 13: `Vulnerability` rows; Phase 14: `Log` rows with `source_ip`; `Alert` + `AlertEvent` + `Notification` models | `Alert` rows in DB (types: `brute_force`, `port_scan`, `suspicious_login`); `Notification` rows for High/Critical alerts; `detection_service.py` module with 3 rules | 16, 17, 19, 21 | `tests/test_detection.py`; brute force alert created after 5 login_failure logs |
| **16** | Alert Management | Phase 15: `Alert` rows in DB; `AlertEvent` model from migration 001 | `PATCH /alerts/{id}` status transitions; `AlertEvent` rows in DB; `GET /alerts/summary` endpoint; `GET /alerts/{id}/history` endpoint | 17, 19, 21 | `tests/test_alerts.py`; PATCH alert → Acknowledged; 403 for Viewer |
| **17** | Risk Scoring | Phase 13: `Vulnerability` rows; Phase 15/16: `Alert` rows; Phase 11: `ScanResult` rows for open-port count; `RiskScore` model from migration 001 | `RiskScore` rows in DB (`entity_type='device'`, `factor_breakdown` as JSON string); `risk_service.calculate_device_risk()` function; `GET /devices/{id}/risk`, `GET /risk-scores/` endpoints | 19, 21 | `tests/test_risk_scores.py`; `GET /devices/{id}/risk` returning score + band |
| **18** | Threat Intelligence | Phase 14: log save handler (to add indicator check); `ThreatIndicator` model (migration needed if not in 001) | `ThreatIndicator` rows (seed + user-created); `POST /threat-intelligence/`, `GET /threat-intelligence/`, `DELETE /threat-intelligence/{id}` endpoints; `malware_indicator` alert type on match | 21 | `tests/test_threat_intelligence.py`; alert created when log matches indicator |
| **19** | AI Assistant | Phase 15: `Alert` rows; Phase 13: `Vulnerability` + `CVE` rows; Phase 17: `RiskScore` rows with `factor_breakdown`; `AIConversation` + `AIMessage` models (verify in `models/ai.py`) | `POST /ai/explain-alert`, `/explain-vulnerability`, `/explain-risk`, `/ai/chat` endpoints; `LocalRuleAI` class; `AIConversation` + `AIMessage` rows saved after each call | 21, 27 | `tests/test_ai.py`; explanation text contains actual data values |
| **20** | Reports | Phase 13–17: data for reports; `Report` model from migration 001; `fpdf2==2.7.9` added to `requirements.txt` | `Report` rows in DB; PDF and CSV file generation; `POST /reports/`, `GET /reports/`, `GET /reports/{id}/download` endpoints; `backend/generated_reports/` directory | 21, 27 | `tests/test_reports.py`; PDF opens correctly; 403 for Viewer download |
| **21** | Frontend Integration | All Phase 9–20 endpoints live; JWT auth working | Full React app deployed to Vercel; all 13 pages connected to real API; notifications bell; RBAC-enforced UI | 24, 27 | Login with real JWT; Dashboard shows live counts; Viewer sees no AI/Settings |
| **22** | Security Hardening | Phase 21: all endpoints live; `slowapi==0.1.9` added | Rate limiting on `POST /auth/login`; secure response headers; org isolation confirmed on all list endpoints; audit log completeness confirmed | 23, 24 | 429 on 11th login attempt; `X-Content-Type-Options` header present; 2-org isolation test |
| **23** | Testing | All Phase 9–22 work complete | Complete test suite (16 test files); `docs/PHASE23_TEST_RESULTS.md` with pytest output | 24 | `pytest tests/ -v` — 0 failures (paste actual output) |
| **24** | Deployment | Phase 23: all tests passing; `backend/.python-version = 3.12.7`; all env vars set | Live Vercel URL; live Render backend; Neon migrations applied; agent running against production; `docs/PHASE24_DEPLOYMENT.md` | 25, 26, 27 | Live `/health` and `/health/db` returning healthy |
| **25** | Performance | Phase 24: live system; Phase 9/10 resilience baseline already done | Pagination on all list endpoints (if missing); heartbeat cleanup task; agent startup retry; frontend auto-refresh | 26, 27 | `GET /logs/?limit=10` returns 10 rows; agent retries on startup; 0 regressions |
| **26** | Documentation | Phase 24/25: live system; `docs/screenshots/` with real screenshots | `docs/INSTALLATION.md`, `docs/USER_MANUAL.md`, `docs/ARCHITECTURE.md`, `docs/API_REFERENCE.md`, updated `README.md` | 27 | All docs render correctly on GitHub |
| **27** | Demo & Submission | All phases done; `v1.0.0` tag | Demo rehearsed; viva Q&A prepared; `v1.0.0` git tag pushed | — | Pre-demo checklist all ✅ |

---

## Known Ordering Conflicts

### Conflict: Alert risk_score vs Phase 17

**Problem:** The `alerts.risk_score` column is `NOT NULL` in the `Alert` model
(confirmed in `models/alert.py`). Phase 15 creates alerts before Phase 17
implements the risk scoring formula.

**Resolution chosen:** Phase 15 sets an **initial provisional score**:
- `High` severity alert → `risk_score = 40.0`
- `Medium` severity alert → `risk_score = 20.0`
- `Low` severity alert → `risk_score = 10.0`

Phase 17 recalculates device risk scores using `RiskScore` rows (separate
table), and also backfills `alerts.risk_score` for Open alerts on the device
using the formula. The Phase 17 prompt explicitly includes this backfill step.

Both Phase 15 and Phase 17 prompts document this resolution.

### Conflict: device_interfaces vs Phase 11/12

**Problem:** Phase 12 needs `device_interfaces` table but it may not be
created until Phase 11 or Phase 12 itself.

**Resolution chosen:** Phase 11 creates the `DeviceInterface` model and
Alembic migration. Phase 12 uses it. Phase 12 Step 0 explicitly checks
that the table exists before proceeding.

---

## Resilience Baseline Location

Connection resilience work (S1–S3 from `00_shared_standards.md`) is
**required in Phase 9 and Phase 10**. It is NOT deferred to Phase 25.

Phase 25 covers: load/soak testing, pagination completeness, heartbeat
cleanup, frontend auto-refresh — improvements on top of a working system,
not the first-time resilience baseline.

---

## Status Tracking

| Phase | Status | Completed |
|---|---|---|
| 7 | ✅ Done | — |
| 8 | ✅ Done | — |
| 9 | ⬜ Not Started | — |
| 10 | ⬜ Not Started | — |
| 11 | ⬜ Not Started | — |
| 12 | ⬜ Not Started | — |
| 13 | ⬜ Not Started | — |
| 14 | ⬜ Not Started | — |
| 15 | ⬜ Not Started | — |
| 16 | ⬜ Not Started | — |
| 17 | ⬜ Not Started | — |
| 18 | ⬜ Not Started | — |
| 19 | ⬜ Not Started | — |
| 20 | ⬜ Not Started | — |
| 21 | ⬜ Not Started | — |
| 22 | ⬜ Not Started | — |
| 23 | ⬜ Not Started | — |
| 24 | ⬜ Not Started | — |
| 25 | ⬜ Not Started | — |
| 26 | ⬜ Not Started | — |
| 27 | ⬜ Not Started | — |
