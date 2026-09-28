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

## Phase 9 — CyberShield Agent — ⬜ Not Started

*Append completed artifact details here after Phase 9 is done.*

---

## Phase 10 — Agent ↔ Backend Integration — ⬜ Not Started

*Append completed artifact details here after Phase 10 is done.*

---

## Phase 11 — Device Discovery — ⬜ Not Started

*Append after Phase 11.*

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
