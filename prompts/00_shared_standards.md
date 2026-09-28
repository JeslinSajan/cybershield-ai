# CyberShield AI — Shared Engineering Standards

> **Every phase prompt (09–27) references this file.**  
> Rules here apply to all phases without exception.  
> When this file is updated, re-read it before executing any pending phase.

---

## S1 — Database Connection Resilience (backend/app/core/database.py)

### Current state (commit 912c6d6)
`database.py` has `pool_pre_ping=True` but is **missing** pool_recycle,
explicit pool sizing, TCP keepalive, and Neon PgBouncer compatibility.

### Required changes (implement in Phase 9, keep in all later phases)

**S1.1 — Pool settings for Neon free tier**

```python
create_engine(
    db_url,
    pool_pre_ping=True,
    pool_recycle=300,        # recycle before Neon idle-timeout (~5 min)
    pool_size=2,             # Neon free tier: max 4 connections total
    max_overflow=3,          # burst headroom
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)
```

Verify the exact `connect_args` key names against the current
[psycopg3 docs](https://www.psycopg.org/psycopg3/docs/) before
implementing — do not trust these parameter names as final.

**S1.2 — Neon PgBouncer (transaction-mode) compatibility**

Neon's pooled connection URL uses PgBouncer in transaction mode.
Prepared statements are incompatible with this mode.

Add to `.env.example` and `config.py`:
```
DATABASE_URL=<pooled URL from Neon dashboard — used at runtime>
DATABASE_URL_DIRECT=<direct (non-pooler) URL — used by Alembic only>
```

In `database.py`, when using the pooled URL, disable prepared statements:
```python
# psycopg3: disable prepared statements for PgBouncer transaction mode
connect_args["prepare_threshold"] = None
```

In `alembic/env.py`, use `DATABASE_URL_DIRECT` (not `DATABASE_URL`) so
migrations run against the direct connection and do not hit PgBouncer.

> **Verify against current Neon docs before implementing.**
> Neon's pooling configuration changes periodically.
> The two-URL pattern is correct as of September 2026 but must be
> rechecked at execution time.

**S1.3 — Bounded retry on OperationalError for first query after wake-up**

Neon autosuspends after ~5 min idle. The first query after resume can
raise `OperationalError`. Add a small retry only for `test_db_connection()`:

```python
import time
from sqlalchemy.exc import OperationalError

MAX_DB_RETRIES = 3

async def test_db_connection():
    for attempt in range(1, MAX_DB_RETRIES + 1):
        try:
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except OperationalError as e:
            if attempt < MAX_DB_RETRIES:
                wait = attempt * 2  # 2s, 4s
                logger.warning(f"DB attempt {attempt} failed, retrying in {wait}s")
                time.sleep(wait)
            else:
                logger.error(f"DB failed after {MAX_DB_RETRIES} attempts: {e}")
                return False
```

**Do NOT add retry logic to `get_db()` (the normal request path).**

**S1.4 — Never do DB work in FastAPI lifespan**

`lifespan()` calls only `init_db()` (no network) and seeding.
Do not add queries there. This caused a Render startup timeout in Phase 7.

---

## S2 — Backend Cold-Start Tolerance (Render free tier)

Render free tier spins down after ~15 min idle. Cold start takes 15–30s.

**S2.1 — Offline detection threshold**

Mark an agent OFFLINE only after **3 missed heartbeats**, not 1.

```python
# config.py
HEARTBEAT_INTERVAL_SECONDS = 30
AGENT_OFFLINE_MISSED_THRESHOLD = 3   # 3 × 30s = 90s before OFFLINE
```

The background task checks: `last_heartbeat_at < now() - 90s`.

**S2.2 — Demo uptime mitigation (optional)**

For demo periods, ping `https://cybershield-ai-xnn7.onrender.com/api/v1/health`
every 5 min via a free service (cron-job.org, UptimeRobot).
This is a mitigation, not a guarantee. Document in `docs/PHASE24_DEPLOYMENT.md`.

---

## S3 — Agent-Side Resilience (phases 9–14)

**S3.1 — HTTP error handling in api_client.py**

| Error | Treatment |
|---|---|
| ConnectionError / TimeoutError | Transient — exponential backoff with jitter |
| 502 / 503 / 504 | Transient — same (Render cold-start) |
| 401 | Terminal — log, set `_credential_valid=False`, exit cleanly |
| 403 | Terminal — log, do not retry |
| 404 | Skip — log, continue loop |
| Other 5xx | Transient up to MAX_RETRY_ATTEMPTS |

Backoff: `min(2 * 2^attempt + random.uniform(0,1), 30)` seconds.

**S3.2 — First-request timeout**

```python
FIRST_REQUEST_TIMEOUT = 90   # allows Render cold start
NORMAL_TIMEOUT = 10
```

Track `self._first_request_done`. Use `FIRST_REQUEST_TIMEOUT` until
the first successful response, then switch to `NORMAL_TIMEOUT`.

**S3.3 — Idempotent uploads**

- **Heartbeats**: upsert on `(agent_id, timestamp)`. Duplicate within
  the same 30s window is silently discarded.
- **Results**: agent generates a `upload_id` (UUID4). Backend checks
  for existing row with same `upload_id` before inserting.
  Add `upload_id VARCHAR(36)` column to `scan_results` if not present.

**S3.4 — Bounded local offline queue**

```python
# agent/offline_queue.py
MAX_QUEUE_SIZE = 100

class OfflineQueue:
    def enqueue(self, item: dict):
        if len(self._queue) >= MAX_QUEUE_SIZE:
            dropped = self._queue.pop(0)
            logger.warning(f"Queue full — dropped: {dropped.get('type')}")
        self._queue.append(item)

    def drain(self, api_client) -> int:
        """Send all queued items. Returns count sent successfully."""
        ...
```

On reconnect: drain queue before resuming normal heartbeat loop.

---

## S4 — Frontend Network Behavior

**S4.1 — Top-bar status indicator** (three states only)

| State | Trigger |
|---|---|
| `● Connected` | Last API call < 10s ago succeeded |
| `◌ Waking up…` | 502/503 or first call since page load |
| `✕ Disconnected` | 3+ consecutive failures (non-502/503) |

**S4.2 — Axios timeout**

```typescript
// frontend/src/api/client.ts
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 90000,   // 90s — covers Render cold start
})
// After first success: reduce to 15000ms
```

Retry: 3 times for 502/503/504 only, with `2^n * 1000ms` backoff.

---

## S5 — Required Resilience Tests

Own the test in the phase that owns the code. Do not defer to Phase 25.

**Phase 9 must add:**
- `test_db_connection_retry` — dispose engine, call `test_db_connection()`, assert retries and recovers
- `test_agent_retry_on_503` — mock 503 × 2 then 200, assert no crash, heartbeat succeeds
- `test_heartbeat_idempotent` — same `(agent_id, timestamp)` twice → 1 row only

**Phase 10 must add:**
- `test_offline_queue_drains` — 5 items queued offline, backend restored → all 5 sent, 0 duplicates

**Phase 11 must add:**
- `test_scan_result_upload_idempotent` — same `upload_id` twice → 1 row in `scan_results`

---

## S6 — Dependency Pinning

Pin every new dependency with an exact version.
Verify the version exists for **Python 3.12** on PyPI before specifying.
`backend/.python-version` is pinned to `3.12.7` — do not change it.

```
Correct:   fpdf2==2.7.9
Incorrect: fpdf2>=2.7.9
Incorrect: fpdf2
```

---

## S7 — Secrets Policy

Never log at **any** level: `DATABASE_URL`, `DATABASE_URL_DIRECT`,
`JWT_SECRET_KEY`, any token, `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`.

---

## S8 — Git Policy

Never `git push --force`. On divergence: `git pull --rebase` then push.

---

## S9 — HANDOFF.md Protocol

On completing each phase, append an entry to `prompts/HANDOFF.md`:

```markdown
## Phase N — <Title> — COMPLETED <YYYY-MM-DD>

### Produced artifacts
- File: `path/to/file.py` — what it does
- Endpoint: `METHOD /path` — auth, request, response shapes
- Table: `table_name` — key columns consumed by the next phase
- Function: `module.fn(args) -> return_type`

### Deviations from prompt
- Any differences and why.

### Test evidence
- pytest: X passed, 0 failed
- Verification checklist: PASS / FAIL / SKIPPED (with reason)
```

The **next phase's Step 0** reads `prompts/HANDOFF.md` as its primary
source of truth, not the prompt's written assumptions.
