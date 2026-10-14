# Phase 24 — Deployment Verification & Environment Specifications

**Platform:** CyberShield AI — Unified Cybersecurity Monitoring and Threat Management  
**Deployment Date:** 2026-10-14  
**Hosting Topology:** Vercel (Frontend) + Render (Backend API) + Neon (PostgreSQL Database)

---

## 1. Production Service Endpoints

| Service / Resource | Live Production URL | Verification Status | Response / Evidence |
| :--- | :--- | :---: | :--- |
| **Backend API Root** | `https://cybershield-ai-xnn7.onrender.com/` | ✅ Active | `{"name":"CyberShield AI","version":"1.0.0","status":"running"}` |
| **Backend API v1 Health** | `https://cybershield-ai-xnn7.onrender.com/api/v1/health` | ✅ 200 OK | `{"status":"healthy"}` |
| **Database Health Probe** | `https://cybershield-ai-xnn7.onrender.com/api/v1/health/db` | ✅ 200 OK | `{"status":"healthy","database":"connected","message":"Database connection successful"}` |
| **Frontend Web Console** | `https://cybershield-ai.vercel.app` | ✅ Active | Vite + React 18 + Tailwind CSS production bundle |
| **Neon PostgreSQL** | Cloud Postgres (AWS region, pooled + direct) | ✅ Connected | All 25 database tables migrated and validated |

---

## 2. Infrastructure Configuration

### A. Render Backend (`render.yaml`)
- **Service Name:** `cybershield-ai-backend`
- **Runtime:** `python` (`runtimeVersion: 3.12`)
- **Python Version File:** `backend/.python-version` = `3.12.7`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Working Directory:** `backend`
- **Environment Variables:**
  - `DATABASE_URL`: Neon PostgreSQL pooled connection string (`postgresql+psycopg://...`)
  - `JWT_SECRET_KEY`: Strong cryptographic key (32+ bytes entropy)
  - `ENVIRONMENT`: `production`
  - `DEBUG`: `false`
  - `CORS_ORIGINS`: `https://cybershield-ai.vercel.app`
  - `AGENT_OFFLINE_MISSED_THRESHOLD`: `3`
  - `HEARTBEAT_INTERVAL_SECONDS`: `30`
  - `LOG_LEVEL`: `INFO`
  - `SEED_ADMIN_EMAIL`: `admin@cybershield.ai` (auto-seeded on initialization)
  - `SEED_ADMIN_PASSWORD`: Production secure credential (never logged)

### B. Vercel Frontend (`frontend/`)
- **Framework Preset:** Vite
- **Root Directory:** `frontend`
- **Build Command:** `npm run build` (`tsc && vite build`)
- **Output Directory:** `dist`
- **Environment Variables:**
  - `VITE_API_BASE_URL`: `https://cybershield-ai-xnn7.onrender.com`

### C. CyberShield Local Agent (`agent/`)
- **Execution Environment:** Python 3.12+ (local network probe)
- **Configuration (`agent/.env`):**
  - `BACKEND_URL`: `https://cybershield-ai-xnn7.onrender.com`
  - `ENROLLMENT_TOKEN`: One-time token from Admin Settings Console
  - `AGENT_NAME`: `soc-network-agent`
  - `HEARTBEAT_INTERVAL`: `30`

---

## 3. Database Migration State (Neon)

Alembic migrations applied and verified:
1. `001_initial_schema.py`: Initial schema provisioning all 25 tables.
2. `002_add_last_failed_at.py`: Account lockout window tracking column on `users`.
3. `003_add_agent_enrollment_tokens.py`: Agent enrollment token storage.
4. `004_make_device_id_nullable.py`: Allows standalone log collection prior to device association.
5. `005_add_upload_id_to_scan_results.py`: Scan result upload tracking and correlation.

---

## 4. Production Security Hardening Verification
- **SlowAPI Rate Limiting:** Enforces 10 requests/minute per IP on `POST /api/v1/auth/login`. Returns HTTP 429 `RATE_LIMITED` on excess attempts.
- **HTTP Security Headers:**
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- **Multi-Tenant Organization Boundary:** All queries enforce strict tenant filtering by `current_user.organization_id`.
- **Zero Secret Exposure:** Database connection strings, JWT secret keys, and passwords are never logged at any log level.
