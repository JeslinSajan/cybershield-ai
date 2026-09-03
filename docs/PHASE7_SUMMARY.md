# Phase 7 — Backend Foundation: Completion Summary

**Status:** Complete with deployment issues resolved  
**Date Completed:** 2026-09-03  
**Backend URL:** https://cybershield-ai-xnn7.onrender.com  
**Commit range:** `6bcfaea` (Phase 6) → `4c0ba76` (psycopg dialect fix)

---

## 1. What Was Built

### 1.1 Backend Structure — From Smoke Test to Layered Architecture

Phase 6 left behind a minimal deployment smoke test at `backend/main.py`:
a single FastAPI file with two endpoints and a direct `psycopg` connection.

Phase 7 replaced this with a proper layered backend under `backend/app/`:

```
backend/
├── main.py                          # Smoke test (kept, used by Render dashboard)
├── app/
│   ├── main.py                      # Phase 7 FastAPI application (lifespan, CORS, routers)
│   ├── core/
│   │   ├── config.py                # Pydantic Settings v2 — env-var config management
│   │   ├── database.py              # SQLAlchemy engine, session factory, psycopg dialect fix
│   │   ├── exceptions.py            # CyberShieldException hierarchy + ErrorResponse
│   │   └── logging.py               # Centralized structured logging (console only, Render-safe)
│   ├── models/
│   │   ├── __init__.py              # Exports all 25 model classes
│   │   ├── organization.py          # Organization, Role, Permission, RolePermission
│   │   ├── user.py                  # User
│   │   ├── agent.py                 # Agent, AgentCredential, AgentHeartbeat
│   │   ├── device.py                # Device, DeviceInterface
│   │   ├── scan.py                  # Scan, ScanResult, CVE, Vulnerability
│   │   ├── log.py                   # Log, ThreatIndicator
│   │   ├── alert.py                 # Alert, AlertEvent, RiskScore
│   │   ├── report.py                # Report
│   │   ├── ai.py                    # AIConversation, AIMessage
│   │   └── system.py               # Notification, AuditLog, SystemSetting
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── base.py                  # HealthResponse, HealthDatabaseResponse, RootResponse, etc.
│   └── api/
│       └── v1/
│           ├── router.py            # Main v1 router — assembles all sub-routers
│           ├── health.py            # GET /api/v1/health, GET /api/v1/health/db (implemented)
│           ├── auth.py              # Placeholder — Phase 8
│           ├── users.py             # Placeholder — Phase 8
│           ├── agents.py            # Placeholder — Phase 9
│           ├── devices.py           # Placeholder — Phase 11
│           ├── scans.py             # Placeholder — Phase 12
│           ├── vulnerabilities.py   # Placeholder — Phase 12
│           ├── logs.py              # Placeholder — Phase 13
│           ├── alerts.py            # Placeholder — Phase 14
│           ├── threat_intelligence.py # Placeholder — Phase 14
│           ├── reports.py           # Placeholder — Phase 15
│           ├── ai.py                # Placeholder — Phase 16
│           ├── dashboard.py         # Placeholder — Phase 17
│           └── settings.py          # Placeholder — future phase
├── alembic/
│   ├── alembic.ini
│   └── versions/
│       └── 001_initial_schema.py    # Initial migration (25 tables)
├── requirements.txt
├── .env.example
└── startup_check.py                 # Diagnostic script (added during deployment troubleshooting)
```

### 1.2 SQLAlchemy Models — All 25 Tables

All 25 tables described in `docs/database/schema.md` are implemented as
SQLAlchemy ORM models. Confirmed by running:

```
Base.metadata.tables → 25 tables registered ✅
```

Table-by-table listing:

| # | Table | Model File | Model Class |
|---|-------|-----------|-------------|
| 1 | organizations | organization.py | Organization |
| 2 | roles | organization.py | Role |
| 3 | permissions | organization.py | Permission |
| 4 | role_permissions | organization.py | RolePermission |
| 5 | users | user.py | User |
| 6 | agents | agent.py | Agent |
| 7 | agent_credentials | agent.py | AgentCredential |
| 8 | agent_heartbeats | agent.py | AgentHeartbeat |
| 9 | devices | device.py | Device |
| 10 | device_interfaces | device.py | DeviceInterface |
| 11 | scans | scan.py | Scan |
| 12 | scan_results | scan.py | ScanResult |
| 13 | cves | scan.py | CVE |
| 14 | vulnerabilities | scan.py | Vulnerability |
| 15 | logs | log.py | Log |
| 16 | threat_indicators | log.py | ThreatIndicator |
| 17 | alerts | alert.py | Alert |
| 18 | alert_events | alert.py | AlertEvent |
| 19 | risk_scores | alert.py | RiskScore |
| 20 | reports | report.py | Report |
| 21 | ai_conversations | ai.py | AIConversation |
| 22 | ai_messages | ai.py | AIMessage |
| 23 | notifications | system.py | Notification |
| 24 | audit_logs | system.py | AuditLog |
| 25 | system_settings | system.py | SystemSetting |

### 1.3 API Routers Registered

All 13 API groups are registered under `/api/v1/` in `router.py`:

| Prefix | Status | Planned Phase |
|--------|--------|---------------|
| `/health` | **Implemented** — real logic | Phase 7 |
| `/auth` | Placeholder stub only | Phase 8 |
| `/users` | Placeholder stub only | Phase 8 |
| `/agents` | Placeholder stub only | Phase 9 |
| `/devices` | Placeholder stub only | Phase 11 |
| `/scans` | Placeholder stub only | Phase 12 |
| `/vulnerabilities` | Placeholder stub only | Phase 12 |
| `/logs` | Placeholder stub only | Phase 13 |
| `/alerts` | Placeholder stub only | Phase 14 |
| `/threat-intelligence` | Placeholder stub only | Phase 14 |
| `/reports` | Placeholder stub only | Phase 15 |
| `/ai` | Placeholder stub only | Phase 16 |
| `/dashboard` | Placeholder stub only | Phase 17 |
| `/settings` | Placeholder stub only | Future |

**Important:** All non-health routers return `{"message": "Not implemented yet — Phase N"}`.
They are registered so Swagger UI (`/docs`) shows the intended API surface,
but they contain no real business logic.

---

## 2. Deployment Issues Encountered and Fixed

The path from Phase 7 code completion to a working live deployment required
fixing six distinct issues. These are documented here because they represent
real engineering decisions, not just noise.

### Issue 1 — Python Version Mismatch: Render defaulting to Python 3.13/3.14

**Commits:** `ce92c29`, `8ed9422`, `045d46a`

**What happened:**  
Render's default Python version changed to 3.13.7 and eventually tried 3.14.
The pinned dependency `pydantic==2.5.0` requires `pydantic-core==2.14.1`,
which has no pre-built wheel for Python 3.13+. Pip tried to build it from
source using Rust/maturin. Render's build filesystem is read-only in the
Cargo cache path, causing the build to fail with:
```
error: failed to create directory /usr/local/cargo/registry/cache/...
Read-only file system (os error 30)
```

**Resolution:**  
Three Python version configuration files were aligned to `3.12`:
- `backend/.python-version` → `3.12`
- `runtime.txt` → `python-3.12`
- `render.yaml` `runtimeVersion` → `3.12`

Under Python 3.12, pip downloads the pre-compiled `pydantic-core` wheel
directly and the build completes in seconds without any Rust toolchain.

**Also caught:** The `render.yaml` `buildCommand` had path `backend/requirements.txt`
while Render's working directory was already set to `backend/`, causing a
path-not-found error. Corrected to `requirements.txt`.

### Issue 2 — File Log Handler Crashing on Render Startup

**Commit:** `f763be3`

**What happened:**  
`app/core/logging.py` configured a `RotatingFileHandler` writing to
`logs/cybershield.log`. On Render, the filesystem is ephemeral and the
`logs/` directory does not exist. Python raises `FileNotFoundError`
during `logging.config.dictConfig()`, which is called at module import time
in `app/main.py`. The process crashed before FastAPI even initialised,
with exit code 1, and no error appeared in Render's deploy log because
the crash happened before any output was produced.

**Resolution:**  
The file handler was removed entirely. Render streams stdout to its log
dashboard, so console-only logging is the correct and sufficient approach
for cloud deployment.

### Issue 3 — Database Password Leak in Application Logs

**Commit:** `f763be3` (same commit as Issue 2)

**What happened:**  
`app/core/database.py` contained:
```python
logger.info(f"Database engine created for {settings.DATABASE_URL}")
```
`DATABASE_URL` includes the database password in plaintext. This line
would print the full connection string — including credentials — to stdout,
which Render records in its deploy log. Anyone with Render dashboard access
could read the database password from the log viewer.

**Resolution:**  
The log line was replaced with:
```python
logger.info("Database engine created successfully")
```
The password is no longer logged anywhere. This is a genuine security fix,
not a cosmetic change.

### Issue 4 — Render Startup Timeout: Blocking DB Check in Lifespan

**Commit:** `a419ba7`

**What happened:**  
The Phase 7 lifespan context manager called `test_db_connection()` during
startup. This function uses synchronous SQLAlchemy (`engine.connect()`) inside
an `async def`, which blocks the uvicorn event loop. The Neon connection URL
also contained `channel_binding=require`, which PgBouncer (Neon's connection
pooler) does not support, causing the connection attempt to hang rather than
fail fast.

Render kills any service that does not bind to its assigned port within
approximately 15–18 seconds and sends SIGQUIT (Python exit code 3). The
deploy log showed:
```
Running 'python -m uvicorn app.main:app ...'
Exited with status 3
```
with no Python traceback visible because the crash happened inside the
event loop before any output could flush.

A diagnostic script (`startup_check.py`) was temporarily added to isolate
the failure — it confirmed all imports passed and `DATABASE_URL` was set
correctly. The blocking startup check was the only cause.

**Resolution:**  
`test_db_connection()` was removed from the lifespan entirely. Database
connectivity is verified on demand via `GET /api/v1/health/db`. This is
the standard approach for cloud deployments where the DB may not be
reachable at the instant the process starts.

### Issue 5 — SQLAlchemy psycopg2/psycopg3 Dialect Mismatch

**Commit:** `4c0ba76`

**What happened:**  
SQLAlchemy treats the URL scheme `postgresql://` as an instruction to use
`psycopg2` (the v2 driver) by default. This project installs `psycopg[binary]`
(the v3 driver, package name `psycopg`), not `psycopg2`. The correct
SQLAlchemy dialect string for psycopg v3 is `postgresql+psycopg://`.

Neon's dashboard "Connection String" copy button produces `postgresql://...`,
which is what was set in the Render environment variable. On the first request
that triggered the database engine to initialise, SQLAlchemy tried to import
`psycopg2`, found it missing, and raised:
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Resolution:**  
A `_normalize_db_url()` function was added in `app/core/database.py`:
```python
def _normalize_db_url(url: str) -> str:
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://") and not url.startswith("postgres+"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url
```

This is applied in `get_engine()` before `create_engine()`. The fix works
regardless of which form the connection string is in — Render dashboard,
`.env` file, or CI environment. `psycopg2` was not added anywhere.

`backend/.env.example` and `docs/deployment/local-development.md` were
updated to document the preferred `postgresql+psycopg://` scheme.

### Issue 6 — Render Dashboard Overriding render.yaml Start Command

**Observation during troubleshooting** (no separate commit)

Render's web service dashboard "Start Command" setting takes precedence over
`render.yaml` for existing services. Changes to `render.yaml`'s `startCommand`
are ignored for services already configured via the dashboard. Any start command
changes must be made in **Render Dashboard → Settings → Start Command** manually.
The `render.yaml` `startCommand` is only authoritative when creating a brand-new
service from scratch.

---

## 3. Current Verified State

**Verified at:** 2026-09-03T08:32 UTC  
**Evidence source:** Live HTTP responses, not assumptions.

### GET /api/v1/health
```
GET https://cybershield-ai-xnn7.onrender.com/api/v1/health
Response: {"status":"healthy"}
HTTP 200 OK ✅
```

### GET /api/v1/health/db
```
GET https://cybershield-ai-xnn7.onrender.com/api/v1/health/db
Response: {"status":"healthy","database":"connected","message":"Database connection successful"}
HTTP 200 OK ✅
```

The Neon PostgreSQL database is reachable from the Render deployment.
SQLAlchemy's `SELECT 1` query executes successfully using the psycopg v3 driver.

**Swagger UI** is available at:
```
https://cybershield-ai-xnn7.onrender.com/docs
```

---

## 4. Model vs. Schema Cross-Check: Discrepancies Found

During preparation of this document, all SQLAlchemy models were read and
compared against `docs/database/schema.md` column-by-column.

**All 25 tables and their columns are present and correctly typed with one
exception and five missing constraints noted below.**

These are not blocking for Phase 7 completion (the Phase 7 scope was to
establish the models, not to enforce every unique constraint at the ORM level
— those are enforced by the Alembic migration SQL directly). However they
should be addressed before Phase 8 inserts data that relies on uniqueness.

### Discrepancy 1 — `risk_scores.factor_breakdown`: TEXT vs JSONB

| | Schema | Model (`alert.py`) |
|-|--------|---------------------|
| `factor_breakdown` | `JSONB` | `Text` |

`schema.md` line 360 specifies `JSONB NOT NULL`. The model uses Python `Text`.
This means structured risk factor data is stored as a raw string rather than
queryable JSON. **Flagged — not silently fixed.**

### Discrepancy 2 — Missing UniqueConstraints in Models

The following unique constraints are specified in `schema.md` but are not
present in the SQLAlchemy model definitions. The Alembic migration
`001_initial_schema.py` may or may not include them — that was not verified
here and should be checked separately.

| Table | Schema constraint | Missing from model |
|-------|------------------|--------------------|
| `permissions` | `UNIQUE(resource, action)` | Yes |
| `role_permissions` | `UNIQUE(role_id, permission_id)` | Yes |
| `devices` | `UNIQUE(organization_id, ip_address)` | Yes |
| `threat_indicators` | `UNIQUE(organization_id, indicator_type, value)` | Yes |
| `system_settings` | `UNIQUE(organization_id, key)` | Yes |

These constraints prevent duplicate records at the database level (e.g., two
identical permissions, duplicate device registrations for the same IP, duplicate
threat indicators). They are important for data integrity but will not cause
a startup crash. They should be added to the models and verified in the
Alembic migration before Phase 8 begins writing data.

**Action required before Phase 8:** Confirm these constraints exist in the
Alembic migration SQL. If not, add a Phase 7.5 migration to enforce them.
Then update the SQLAlchemy models to declare the corresponding
`UniqueConstraint` entries in `__table_args__`.

---

## 5. What Is Explicitly Not Done Yet

The following are **not implemented** as of Phase 7. Phase 8 starts from this
baseline.

| Feature | State |
|---------|-------|
| JWT token generation | Not implemented |
| Login endpoint | Stub — returns "Not implemented yet" |
| Register endpoint | Stub — returns "Not implemented yet" |
| Password hashing on user creation | Not implemented |
| Role-based access control enforcement | Not implemented |
| Any middleware checking authentication | Not implemented |
| Any endpoint reading real data from the database | Not implemented (except `SELECT 1` in health/db) |
| Alembic migration applied to Neon | **Unverified** — the `_healthcheck` table used by the smoke test existed, but the 25-table Phase 7 migration has not been confirmed as applied against the live Neon database |
| Agent registration flow | Not implemented |
| Any scanner, log collector, or alert generator | Not implemented |

> **Note on Alembic migration state:** The Neon database connects and returns
> `SELECT 1` successfully, which only confirms connectivity. Whether the 25
> tables from `001_initial_schema.py` are present in the live Neon database
> has not been verified with `\dt` or `alembic current`. This should be
> confirmed before Phase 8 begins creating users or other records.

---

## 6. Commit History — Phase 6 Baseline to Phase 7 Complete

| Commit | Description |
|--------|-------------|
| `6bcfaea` | Phase 6 complete: development environment and documentation |
| `7310d87` | Smoke test: minimal FastAPI health check + React health indicator |
| `55b27e4` | Switch from asyncpg to psycopg[binary] for Python 3.12 compatibility |
| `7381699` | Fix psycopg version: use 3.2.13 |
| `ce92c29` | Render deployment: specify Python 3.13.7 and build configuration |
| `069e51c` | Add Procfile and root requirements.txt for Render build |
| `3ada459` | **Complete Phase 7 Backend Foundation** (models, schemas, routers, config) |
| `8ed9422` | Pin Python version to 3.12 for Render compatibility |
| `045d46a` | Align all Python version configs to 3.12; fix buildCommand path |
| `f763be3` | Remove file logging handler (Render crash fix); fix password leak in logs |
| `44c232e` | Add startup diagnostic script for Render troubleshooting |
| `ac9c965` | Run diagnostic before startup to capture crash reason in Render logs |
| `a419ba7` | Remove blocking DB test from lifespan (Render startup timeout fix) |
| `4c0ba76` | Normalize DATABASE_URL to use psycopg v3 dialect explicitly |
