# CyberShield AI — Phase Handoff Log

> **This file is the source of truth for what is actually built.**  
> The next phase's Step 0 reads this file, not the phase prompt's assumptions.  
> After completing a phase, append a new section here with real artifacts.

---

## Phases 1–8 — Reality Baseline (verified from codebase, commit 912c6d6)

### Authentication & RBAC — COMPLETED (Phase 7/8)

**RBAC dependency names** (from `backend/app/core/deps.py`):
```python
get_current_admin                # Depends(require_role("Administrator"))
get_current_analyst_or_admin     # Depends(require_role("Administrator", "Security Analyst"))
get_any_authenticated_user       # Depends(require_role("Administrator", "Security Analyst", "Viewer"))
require_role(*roles)             # factory — returns a FastAPI dependency
```

Agent credential dependency: **NOT YET IMPLEMENTED** — TODO comment
exists in `deps.py`. Phase 9 must add `require_agent_credential()`.

**Error envelope** (all errors use this exact shape):
```json
{"error": {"code": "NOT_FOUND", "message": "...", "details": []}}
```
Codes in use: `NOT_AUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`,
`VALIDATION_ERROR`, `INTERNAL_SERVER_ERROR`, `AGENT_NOT_AUTHORIZED`.

**JWT**: `python-jose[cryptography]==3.3.0`. Token lifetime: 30 min.
User ID stored in `sub` claim. Role loaded from DB (not from JWT claim).

### Database — COMPLETED (Phase 7/8)

**Alembic migrations applied** (as of commit 912c6d6):
- `001_initial_schema.py` — all 25 tables created
- `002_add_last_failed_at.py` — added `last_failed_at` column (table unknown — verify)

**Connection** (`backend/app/core/database.py`):
- Driver: `psycopg[binary]==3.2.13` (psycopg v3)
- URL normalization: `postgresql://` → `postgresql+psycopg://` (auto in `_normalize_db_url()`)
- Current settings: `pool_pre_ping=True` only
- **MISSING** (Phase 9 must add): `pool_recycle`, `pool_size`, `max_overflow`,
  `connect_args` (keepalive + timeout), `prepare_threshold=None` for PgBouncer
- `DATABASE_URL_DIRECT` env var: **not yet added** (Phase 9 adds it for Alembic)

**Session**: `autocommit=False`, `autoflush=False`. Yielded by `get_db()` dep.

### Models confirmed in `backend/app/models/`

**Agent models** (`models/agent.py`):
```
Agent:           id, organization_id, name, hostname, status, version,
                 last_heartbeat_at, is_active, created_at, updated_at, deleted_at
AgentCredential: id, agent_id, credential_hash, type, issued_at,
                 expires_at, revoked_at, is_active, created_at, updated_at
AgentHeartbeat:  id, agent_id, organization_id, timestamp, status,
                 version, cpu_percent, memory_percent, details(JSONB), created_at
```

**Scan models** (`models/scan.py`):
```
Scan:           id, organization_id, agent_id, created_by_user_id, scan_type,
                status, target_scope, started_at, completed_at, created_at, updated_at
ScanResult:     id, organization_id, scan_id, device_id, result_type,
                raw_payload(JSONB), created_at, updated_at
CVE:            id, organization_id, cve_id, severity, cvss_score,
                affected_service, affected_version, summary, recommendation,
                source, is_demo_data, created_at, updated_at
Vulnerability:  id, organization_id, device_id, scan_id, cve_id(FK→cves.id),
                severity, score, description, recommendation,
                status(default='open'), created_at, updated_at
```

**Alert models** (`models/alert.py`):
```
Alert:      id, organization_id, agent_id, device_id, alert_type,
            severity, status(default='Open'), description,
            risk_score(Numeric NOT NULL), triggered_at, created_at, updated_at
AlertEvent: id, organization_id, alert_id, actor_user_id,
            from_status, to_status, reason, changed_at
RiskScore:  id, organization_id, entity_type, entity_id, score,
            risk_band, factor_breakdown(Text — store as json.dumps()),
            formula_version(default='v1'), created_at, updated_at
```

**System models** (`models/system.py`):
```
Notification:  id, organization_id, user_id, alert_id, notification_type,
               channel(default='dashboard'), title, body,
               is_read(bool default=False), created_at, updated_at
AuditLog:      id, organization_id, actor_type, actor_id, action,
               target_type, target_id, details(JSONB), created_at
SystemSetting: id, organization_id, key, value(JSONB),
               created_by_user_id, created_at, updated_at
```

**AI models** (`models/ai.py` — verify actual columns before Phase 19):
```
AIConversation: id, organization_id, user_id, subject_type, subject_id,
                provider_type(default='local_rule_ai'), created_at, updated_at
AIMessage:      id, conversation_id, role, content, created_at
```

### Existing API stub files (`backend/app/api/v1/`)

All files exist as stubs. Stubs return `{"message": "Not implemented yet"}`.
Phase 9 onwards fills in the real logic.

```
agents.py            — GET /, GET /{id}, POST /, DELETE /{id} (stub)
auth.py              — POST /login, POST /refresh — IMPLEMENTED (Phase 8)
users.py             — user management — IMPLEMENTED (Phase 8)
health.py            — GET /health, GET /health/db — IMPLEMENTED (Phase 7)
ai.py, alerts.py, dashboard.py, devices.py, logs.py, reports.py,
scans.py, settings.py, threat_intelligence.py, vulnerabilities.py — all stubs
```

### Pinned backend dependencies (`backend/requirements.txt`)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
psycopg[binary]==3.2.13
python-dotenv==1.0.0
sqlalchemy==2.0.36
alembic==1.14.0
pydantic==2.5.0
pydantic-settings==2.1.0
pydantic[email]
bcrypt==4.1.1
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
```

### Environment variables (`.env.example` as of commit 912c6d6)

```
DATABASE_URL=postgresql+psycopg://...
# DATABASE_URL_DIRECT — NOT YET ADDED (Phase 9 adds it)
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SEED_ADMIN_EMAIL=...
SEED_ADMIN_PASSWORD=...
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,...
# AGENT_OFFLINE_TIMEOUT_SECONDS — NOT YET ADDED (Phase 9 adds it)
# HEARTBEAT_INTERVAL_SECONDS — NOT YET ADDED (Phase 9 adds it)
```

### Key architectural decisions (carry forward)

- **SHA-256** for agent credential hashing, **not bcrypt** (non-deterministic).
  Document this in `deps.py` comment: "SHA-256 of a 48-byte random token
  (384 bits entropy) is collision-safe. Bcrypt cannot be used for token
  lookup because it is intentionally non-deterministic."

- **RBAC loaded from DB**, not JWT claim. `require_role()` queries the
  `roles` table on every request. This is intentional (prevents stale JWT
  claims bypassing role changes).

- **Organization isolation**: every list endpoint must filter by
  `organization_id` from the authenticated user's record. Phase 22 audits
  all endpoints for this.

- **Alembic for Neon**: use `DATABASE_URL_DIRECT` (non-pooler URL) in
  `alembic/env.py`. Phase 9 adds this requirement.

---

## Phase 9 — CyberShield Agent — ✅ Done (commit 8b08955)

**Database & Alembic:**
- Added `DATABASE_URL_DIRECT` pattern in `alembic/env.py` for direct migrations against Neon.
- Migration `003_add_agent_enrollment_tokens.py` applied: created `agent_enrollment_tokens` table.
- Database pool resilience baseline established in `database.py`: `pool_recycle=300`, `pool_size=2`, `max_overflow=3`, TCP keepalives, and bounded retry.

**Backend Implementation:**
- `require_agent_credential()` dependency added in `deps.py` (SHA-256 hash lookup).
- `POST /api/v1/agents/enrollment-token` (Admin JWT).
- `POST /api/v1/agents/register` (uses enrollment token, returns agent credential).
- `POST /api/v1/agents/heartbeat` (agent credential auth, idempotent).
- `GET /api/v1/agents/` and `GET /api/v1/agents/{id}` (Admin/Analyst JWT).
- `POST /api/v1/agents/{id}/revoke` (Admin JWT).
- Offline detection background task in `main.py` lifespan (checks every 60s).

**Agent Application (`agent/`):**
- Python module structure created under `agent/` with pinned deps (`psutil==5.9.8`, `httpx==0.27.2`, `python-dotenv==1.0.1`).
- `api_client.py`: resilient client with backoff and 90s first timeout.
- Self-registration flow saving `agent_identity.json` with chmod 600.
- Heartbeat loop collecting system metrics.

---

## Phase 10 — Agent ↔ Backend Integration — ✅ Done

**Database & Alembic:**
- Migration `004_make_device_id_nullable.py`: made `scan_results.device_id` nullable (supports system health checks).
- Migration `005_add_upload_id_to_scan_results.py`: added `upload_id` VARCHAR(36) column with unique constraint to `scan_results` for idempotent uploads.

**Backend Implementation (`backend/app/api/v1/agents.py`):**
- `GET /api/v1/agents/tasks` (agent credential auth): fetches PENDING scans assigned to the agent. Placed before dynamic `/{agent_id}` to prevent route collision.
- `POST /api/v1/agents/tasks/{task_id}/status` (agent credential auth): updates task status (`RUNNING`, `COMPLETED`, `FAILED`), sets `started_at` and `completed_at`.
- `POST /api/v1/agents/results` (agent credential auth): stores task results with idempotency check on `upload_id`. Transitions task status to `COMPLETED`.
- `POST /api/v1/agents/{agent_id}/rotate-credential` (Admin JWT): revokes active credentials, issues new token, writes AuditLog.
- `GET /api/v1/agents/{agent_id}/network-stats` (Analyst+Admin JWT): returns last 10 heartbeat snapshots with network data.
- Periodic offline detection sweep inside heartbeat handler excludes the calling agent.

**Agent Integration (`agent/`):**
- `agent/task_poller.py`: polls `GET /agents/tasks` every `TASK_POLL_INTERVAL` (default 30s) and dispatches `health_check` tasks.
- `agent/offline_queue.py`: bounded in-memory queue (`MAX_QUEUE_SIZE=100`) with automatic queue draining on reconnection.
- `agent/main.py`: dual-interval loop running both heartbeat and task polling with credential validity checks.

**Verification:**
- Full test suite passing in `tests/test_agents.py` (38/38 tests passed).
- Overall suite: 93 passed, 0 regressions.


---

## Phase 11 — Device Discovery — COMPLETED 2026-10-07

### Database & Schema Verification:
- `devices` table: id (UUID PK), organization_id (UUID FK), ip_address (String), mac_address (String nullable), hostname (String nullable), vendor (String nullable), os (String nullable), status (String default 'online'), first_seen (DateTime), last_seen (DateTime), created_at, updated_at.
- `device_interfaces` table: id (UUID PK), organization_id (UUID FK), device_id (UUID FK), interface_name (String), ip_address (String nullable), mac_address (String nullable), is_primary (Boolean default False), created_at, updated_at.
- Verified existing tables from Alembic migration `001_initial_schema.py`. No new migrations required.

### Endpoints Created / Implemented:
- `POST /api/v1/scans/` (Analyst+Admin JWT): creates scan task with `scan_type="discovery"`, records `AuditLog` action `scan_created`.
- `GET /api/v1/scans/` (Admin+Analyst JWT): lists scans for organization with limit/offset.
- `GET /api/v1/scans/{scan_id}` (Admin+Analyst JWT): retrieves scan detail by ID.
- `GET /api/v1/devices/` (All 3 roles JWT): lists discovered devices for organization with status filter and pagination.
- `GET /api/v1/devices/{device_id}` (All 3 roles JWT): retrieves single device with 404 error envelope.
- Reused Phase 10 agent polling (`GET /api/v1/agents/tasks`) and result upload (`POST /api/v1/agents/results`).

### Services & Agent Modules:
- `backend/app/services/discovery_service.py`: `process_discovery_result(db, scan, payload)` parses host entries, upserts `Device` records by `(organization_id, ip_address)` to prevent duplicates, updates `first_seen`/`last_seen`, and records `AuditLog`.
- `agent/collectors/network_scanner.py`: `discover_devices(subnet)` executes `nmap -sn` ping sweeps with automatic fallback to ARP table parsing (`arp -a`) and local network interface inspection when Nmap CLI is not installed.
- `agent/task_poller.py`: integrated `handle_discovery()` task dispatcher to run device discovery and upload results via `POST /api/v1/agents/results`.

### Test Evidence:
- New tests:
  - `tests/test_scans.py` (5 passed)
  - `tests/test_network_scanner.py` (4 passed)
  - `tests/test_discovery_service.py` (2 passed)
  - `tests/test_devices.py` (6 passed including end-to-end integration loop)
- Test suite total: 110 passed, 2 pre-existing failures from Phase 8. Zero regressions.

---

## Phase 12 — Network Monitoring — ⬜ Not Started

*Append after Phase 12.*

---

## Phase 13 — Vulnerability Scanning — ⬜ Not Started

*Append after Phase 13.*

---

## Phase 14 — Log Management — ⬜ Not Started

*Append after Phase 14.*

---

## Phase 15 — Threat Detection — ⬜ Not Started

*Append after Phase 15.*

---

## Phase 16 — Alert Management — ⬜ Not Started

*Append after Phase 16.*

---

## Phase 17 — Risk Scoring — ⬜ Not Started

*Append after Phase 17.*

---

## Phase 18 — Threat Intelligence — ⬜ Not Started

*Append after Phase 18.*

---

## Phase 19 — AI Security Assistant — ⬜ Not Started

*Append after Phase 19.*

---

## Phase 20 — Reports — ⬜ Not Started

*Append after Phase 20.*

---

## Phase 21 — Frontend Integration — ⬜ Not Started

*Append after Phase 21.*

---

## Phase 22 — Security Hardening — ⬜ Not Started

*Append after Phase 22.*

---

## Phase 23 — Testing — ⬜ Not Started

*Append after Phase 23.*

---

## Phase 24 — Deployment — ⬜ Not Started

*Append after Phase 24.*

---

## Phase 25 — Performance — ⬜ Not Started

*Append after Phase 25.*

---

## Phase 26 — Documentation — ⬜ Not Started

*Append after Phase 26.*

---

## Phase 27 — Demo & Submission — ⬜ Not Started

*Append after Phase 27.*

