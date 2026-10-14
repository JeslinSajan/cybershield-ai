# CyberShield AI — Installation & Setup Guide

This guide provides comprehensive, step-by-step instructions for installing, configuring, and running CyberShield AI across development and production environments.

---

## Architecture Overview

CyberShield AI consists of four primary components:
1. **Backend API**: FastAPI application (Python 3.12) running on Uvicorn.
2. **Database**: PostgreSQL 16+ hosted on Neon Serverless with connection pooling (PgBouncer).
3. **Frontend Dashboard**: React 18 Single Page Application built with TypeScript, Vite, and Tailwind CSS.
4. **Endpoint Monitoring Agent**: Lightweight Python 3.12 daemon for network discovery, vulnerability scanning, system telemetry, and log ingestion.

---

## System Requirements

- **Operating System**: Windows 10/11, Ubuntu 22.04 LTS / Debian 12, or macOS 13+
- **Python**: Version 3.12.x (Python 3.12.7 recommended; Python 3.13 is not yet supported by some binary extensions)
- **Node.js**: Version 18.x or 20.x LTS with `npm` 9+
- **Nmap**: Version 7.90+ (Required on host running the Agent for network discovery and CVE vulnerability detection)
- **Database**: PostgreSQL instance (Neon Serverless PostgreSQL recommended)

---

## 1. Database Setup (Neon PostgreSQL)

CyberShield AI uses PostgreSQL with specific connection requirements for connection pooling:

1. Create a serverless PostgreSQL database at [Neon Console](https://neon.tech).
2. Retrieve two connection strings from the dashboard:
   - **Pooled connection string** (uses Neon PgBouncer, port 5432 or 6543): Used by the FastAPI runtime.
   - **Direct connection string** (non-pooled, direct to compute): Used for Alembic database migrations.
3. Example formats:
   ```env
   # Pooled (Runtime)
   DATABASE_URL=postgresql+psycopg://username:password@ep-cool-fog-123456-pooler.us-east-2.aws.neon.tech/cybershield?sslmode=require

   # Direct (Migrations)
   DATABASE_URL_DIRECT=postgresql+psycopg://username:password@ep-cool-fog-123456.us-east-2.aws.neon.tech/cybershield?sslmode=require
   ```

---

## 2. Backend Setup & Startup

### Step 2.1: Clone Repository & Create Virtual Environment

```bash
git clone https://github.com/JeslinSajan/cybershield-ai.git
cd cybershield-ai

# Create virtual environment with Python 3.12
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate
```

### Step 2.2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

Pinned dependencies include:
- `fastapi==0.104.1`
- `uvicorn[standard]==0.24.0`
- `psycopg[binary]==3.2.13`
- `sqlalchemy==2.0.36`
- `alembic==1.14.0`
- `pydantic==2.5.0`
- `pydantic-settings==2.1.0`
- `python-jose[cryptography]==3.3.0`
- `passlib[bcrypt]==1.7.4`
- `bcrypt==4.1.1`
- `slowapi==0.1.9`
- `fpdf2==2.7.9`

### Step 2.3: Configure Environment Variables

Create `backend/.env` (copy from `backend/.env.example`):

```bash
cp backend/.env.example backend/.env
```

Set the following required keys in `backend/.env`:

```env
# Application Settings
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=replace-with-a-very-strong-secret-key-at-least-32-chars-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql+psycopg://username:password@ep-pooler.neon.tech/cybershield?sslmode=require
DATABASE_URL_DIRECT=postgresql+psycopg://username:password@ep-direct.neon.tech/cybershield?sslmode=require

# CORS (Frontend URL)
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Agent Heartbeat Settings
HEARTBEAT_INTERVAL_SECONDS=30
AGENT_OFFLINE_MISSED_THRESHOLD=3

# Initial Seed Admin Account
SEED_ADMIN_EMAIL=admin@cybershield.ai
SEED_ADMIN_PASSWORD=AdminSecurePassword2026!
```

### Step 2.4: Run Database Migrations

Apply database schemas using Alembic:

```bash
cd backend
python -m alembic upgrade head
cd ..
```

This sets up all 25 tables, including tenant organizations, RBAC roles, agents, scan tracking, CVE database, vulnerabilities, alerts, and audit logs.

### Step 2.5: Start Backend Server

```bash
# Set PYTHONPATH to backend folder
# Windows PowerShell:
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Linux/macOS:
export PYTHONPATH="backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify backend health at:
- `http://localhost:8000/api/v1/health` (should return `{"status":"healthy"}`)
- `http://localhost:8000/api/v1/health/db` (should return `{"status":"healthy","database":"connected"}`)
- Swagger API Docs: `http://localhost:8000/docs`

---

## 3. Frontend Setup & Startup

### Step 3.1: Install Node Dependencies

```bash
cd frontend
npm install
```

### Step 3.2: Configure Environment Variables

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

For production deployment on Vercel:
```env
VITE_API_BASE_URL=https://cybershield-ai-xnn7.onrender.com
```

### Step 3.3: Run Development Server

```bash
npm run dev
```

Open `http://localhost:5173` in your browser.

### Step 3.4: Production Build Check

```bash
npm run build
```
Build output is generated cleanly into `frontend/dist/`.

---

## 4. Endpoint Monitoring Agent Setup

The agent is installed on endpoints inside the monitored corporate/home network.

### Step 4.1: Install Prerequisites (Nmap)

- **Windows**: Download and install Nmap installer from [nmap.org/download.html](https://nmap.org/download.html). Ensure `nmap.exe` is added to system PATH.
- **Ubuntu/Debian**: `sudo apt update && sudo apt install -y nmap`
- **macOS**: `brew install nmap`

### Step 4.2: Install Agent Dependencies

```bash
cd agent
pip install -r requirements.txt
```

Pinned dependencies:
- `psutil==5.9.8`
- `httpx==0.27.2`
- `python-dotenv==1.0.1`

### Step 4.3: Configure Agent Environment

Create `agent/.env` (copied from `agent/.env.example`):

```env
BACKEND_URL=http://localhost:8000
ENROLLMENT_TOKEN=paste-token-from-dashboard-here
AGENT_NAME=primary-network-sensor
HEARTBEAT_INTERVAL=30
LOG_LEVEL=INFO
```

### Step 4.4: First Run & Enrollment

1. Log into the CyberShield dashboard (`http://localhost:5173`) as an Administrator.
2. Navigate to **Agents** and click **Generate Token**.
3. Copy the token into `agent/.env` as `ENROLLMENT_TOKEN`.
4. Start the agent:
   ```bash
   python main.py
   ```
5. The agent registers itself, saves its credential token locally in `agent_identity.json` (chmod 600), and begins sending health heartbeats every 30 seconds.

---

## 5. First Login & Verification

1. Access the web app at `http://localhost:5173`.
2. Login with seed credentials:
   - **Email**: `admin@cybershield.ai`
   - **Password**: `AdminSecurePassword2026!`
3. Verify that the Dashboard loads with real metrics:
   - System Agents: `1 Online`
   - Real-time Alert Breakdown: `Open`, `Acknowledged`, `Investigating`, `Resolved`
   - Discovered devices and vulnerability scan status.
