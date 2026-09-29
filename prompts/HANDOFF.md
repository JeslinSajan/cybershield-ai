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

 # #   P h a s e   9      C O M P L E T E D   ( v e r i f i e d   f r o m   c o d e b a s e ,   c o m m i t   8 b 0 8 9 5 5 ) 
 
 * * D a t a b a s e   &   A l e m b i c : * * 
 -   A d d e d   \ D A T A B A S E _ U R L _ D I R E C T \   p a t t e r n   i n   \  l e m b i c / e n v . p y \   f o r   m i g r a t i o n s   a g a i n s t   N e o n   ( b y p a s s i n g   p o o l e r ) 
 -   M i g r a t i o n   \   0 3 _ a d d _ a g e n t _ e n r o l l m e n t _ t o k e n s . p y \   a p p l i e d :   a d d e d   \  g e n t _ e n r o l l m e n t _ t o k e n s \   t a b l e   ( D B - b a c k e d ,   s i n g l e - u s e   t o k e n s   t o   s u r v i v e   R e n d e r   c o l d   s t a r t s ) 
 -   D a t a b a s e   p o o l   r e s i l i e n c e   b a s e l i n e   e s t a b l i s h e d   i n   \ d a t a b a s e . p y \ :   \ p o o l _ r e c y c l e = 3 0 0 \ ,   \ p o o l _ s i z e = 2 \ ,   \ m a x _ o v e r f l o w = 3 \ ,   T C P   k e e p a l i v e   c o n n e c t   a r g s ,   a n d   b o u n d e d   s t a r t u p   r e t r y 
 
 * * B a c k e n d   I m p l e m e n t a t i o n   ( \  a c k e n d / a p p / a p i / v 1 / a g e n t s . p y \   a n d   \  a c k e n d / a p p / c o r e / d e p s . p y \ ) : * * 
 -   \  e q u i r e _ a g e n t _ c r e d e n t i a l ( ) \   d e p e n d e n c y   a d d e d   t o   \ d e p s . p y \ .   A u t h e n t i c a t e s   a g e n t s   b y   p e r f o r m i n g   S H A - 2 5 6   h a s h   l o o k u p   o f   t h e   b e a r e r   t o k e n   a g a i n s t   \  g e n t _ c r e d e n t i a l s \   t a b l e 
 -   \ P O S T   / a p i / v 1 / a g e n t s / e n r o l l m e n t - t o k e n \   ( A d m i n   o n l y )   w r i t e s   t o   \  g e n t _ e n r o l l m e n t _ t o k e n s \ 
 -   \ P O S T   / a p i / v 1 / a g e n t s / r e g i s t e r \   v e r i f i e s   t o k e n ,   c o n s u m e s   i t   ( m a r k s   \ u s e d _ a t = n o w \ ) ,   i s s u e s   l o n g - l i v e d   \ A g e n t C r e d e n t i a l \ 
 -   \ P O S T   / a p i / v 1 / a g e n t s / h e a r t b e a t \   i d e m p o t e n t   h e a r t b e a t   i n g e s t i o n ,   l o g s   t o   \  g e n t _ h e a r t b e a t s \   a n d   u p d a t e s   a g e n t ' s   \ l a s t _ h e a r t b e a t _ a t \   a n d   \ s t a t u s \ 
 -   \ G E T   / a p i / v 1 / a g e n t s / \   a n d   \ G E T   / a p i / v 1 / a g e n t s / { i d } \   ( A d m i n / A n a l y s t ) 
 -   \ D E L E T E   / a p i / v 1 / a g e n t s / { i d } / r e v o k e \   ( A d m i n   o n l y ) 
 -   O f f l i n e   D e t e c t i o n   b a c k g r o u n d   t a s k   a d d e d   t o   \ m a i n . p y \   l i f e s p a n :   r u n s   e v e r y   6 0 s ,   m a r k s   a g e n t s   O F F L I N E   i f   m i s s e d   h e a r t b e a t s   e x c e e d   \ A G E N T _ O F F L I N E _ M I S S E D _ T H R E S H O L D   *   H E A R T B E A T _ I N T E R V A L _ S E C O N D S \ 
 
 * * A g e n t   A p p l i c a t i o n   ( \  g e n t / m a i n . p y \   a n d   \  g e n t / a p i _ c l i e n t . p y \ ) : * * 
 -   P y t h o n   m o d u l e   s t r u c t u r e   c r e a t e d   u n d e r   \  g e n t / \ 
 -   P i n n e d   d e p s :   \ p s u t i l = = 5 . 9 . 8 \ ,   \ h t t p x = = 0 . 2 7 . 2 \ ,   \ p y t h o n - d o t e n v = = 1 . 0 . 1 \ 
 -   \  p i _ c l i e n t . p y \   i m p l e m e n t s   r e s i l i e n t   h t t p x   c l i e n t   w i t h   e x p o n e n t i a l   b a c k o f f   o n   5 0 2 / 5 0 3 / 5 0 4   e r r o r s   a n d   n e t w o r k   f a i l u r e s 
 -   I m p l e m e n t s   s e l f - r e g i s t r a t i o n   f l o w   p e r s i s t i n g   \  g e n t _ i d e n t i t y . j s o n \   w i t h   c h m o d   6 0 0 
 -   H e a r t b e a t   l o o p   c o l l e c t i n g   b a s i c   \ c p u _ p e r c e n t \   a n d   \ m e m o r y _ p e r c e n t \   v i a   \ p s u t i l \ 
 
 * * T e s t s   ( \ 	 e s t s / t e s t _ a g e n t s . p y \ ) : * * 
 -   F u l l   t e s t   s u i t e   p a s s i n g   a g a i n s t   S Q L i t e   o v e r r i d e   t e s t   D B   ( \ p y t e s t   t e s t s /   - v \ ) 
 -   F i x e d   t e s t   s u i t e   d e p e n d e n c i e s :   p i n n e d   \ h t t p x = = 0 . 2 7 . 2 \   t o   m a i n t a i n   \ T e s t C l i e n t \   c o m p a t i b i l i t y 
  
 