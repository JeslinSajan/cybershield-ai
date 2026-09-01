# Local Development Setup - CyberShield AI Backend

## Phase 7 Foundation Documentation

This document describes how to set up and run the CyberShield AI backend locally for development and testing.

## Prerequisites

- **Python** 3.10 or later (tested with 3.13)
- **PostgreSQL** 14+ (for production) or **SQLite** (for local development)
- **pip** (Python package manager)
- **Git** (for version control)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/JeslinSajan/cybershield-ai.git
cd cybershield-ai
```

### 2. Set Up Python Environment

#### Option A: Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

#### Option B: Conda

```bash
conda create -n cybershield python=3.13
conda activate cybershield
```

### 3. Install Dependencies

Navigate to the backend directory and install requirements:

```bash
cd backend
pip install -r requirements.txt
```

The key dependencies are:
- **FastAPI** 0.104.1 - Web framework
- **SQLAlchemy** 2.0.36 - ORM
- **Alembic** 1.14.0 - Database migrations
- **Uvicorn** 0.24.0 - ASGI server
- **Pydantic** 2.5.0+ - Data validation
- **psycopg** 3.2.13 - PostgreSQL driver

### 4. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# For local testing with SQLite
DATABASE_URL=sqlite:///./cybershield_test.db

# For Neon PostgreSQL (production)
# DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require

# Application settings
ENVIRONMENT=development
DEBUG=True
APP_NAME=CyberShield AI
APP_VERSION=0.1.0
LOG_LEVEL=INFO

# CORS configuration (development)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Security (for Phase 8)
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Important**: Do NOT commit `.env` to Git. Use `.env.example` as a template.

### 5. Create Logs Directory

```bash
mkdir logs
```

## Running the Backend

### Start the Development Server

From the `backend/` directory:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will start on **http://localhost:8000**

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
```

### Key Endpoints

#### Health Checks
- `GET /api/v1/health` - Application health
- `GET /api/v1/health/db` - Database connectivity

#### Root
- `GET /` - Application info

#### API Documentation
- `GET /docs` - Swagger UI (interactive API docs)
- `GET /redoc` - ReDoc (alternative API docs)

### Example Requests

```bash
# Check application health
python -c "import requests; print(requests.get('http://127.0.0.1:8000/api/v1/health').json())"

# Check database health
python -c "import requests; print(requests.get('http://127.0.0.1:8000/api/v1/health/db').json())"

# Get application info
python -c "import requests; print(requests.get('http://127.0.0.1:8000/').json())"
```

## Database Management

### Initialize Database Schema (First Time)

CyberShield AI uses Alembic for database schema management:

```bash
cd backend
alembic upgrade head
```

This creates all 25 tables defined in the schema.

### View Current Database Status

```bash
alembic current
```

### Create New Migration

After modifying SQLAlchemy models:

```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Downgrade Database

```bash
# Downgrade by one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>
```

## Database Schema Overview

The Phase 7 foundation includes 25 tables:

**Core Identity**
- organizations
- roles
- permissions
- role_permissions
- users
- agents
- agent_credentials
- agent_heartbeats

**Infrastructure**
- devices
- device_interfaces

**Operations**
- scans
- scan_results
- cves
- vulnerabilities
- logs
- threat_indicators

**Security**
- alerts
- alert_events
- risk_scores

**Reporting & AI**
- reports
- ai_conversations
- ai_messages

**System**
- notifications
- audit_logs
- system_settings

See [Schema Documentation](../../docs/database/schema.md) for detailed column specifications.

## Testing

Run the test suite:

```bash
cd backend
python -m pytest ../tests/test_backend_foundation.py -v
```

### Test Results

Foundation tests verify (19 tests total):
- Configuration loading
- Database connectivity
- SQLAlchemy model imports
- All 25 tables defined correctly
- API router structure
- Pydantic schemas
- Error handling
- Logging

Expected output:
```
============================= 19 passed in 0.91s ==============================
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application with lifespan
│   ├── core/
│   │   ├── config.py          # Pydantic Settings
│   │   ├── database.py        # SQLAlchemy engine/sessions
│   │   ├── exceptions.py      # Custom exceptions
│   │   └── logging.py         # Structured logging
│   ├── models/                # SQLAlchemy ORM models (25 total)
│   │   ├── __init__.py        # Central imports
│   │   ├── organization.py
│   │   ├── user.py
│   │   ├── agent.py
│   │   ├── device.py
│   │   ├── scan.py
│   │   ├── alert.py
│   │   ├── log.py
│   │   ├── report.py
│   │   ├── ai.py
│   │   └── system.py
│   ├── schemas/               # Pydantic request/response models
│   │   ├── __init__.py
│   │   └── base.py
│   └── api/
│       └── v1/
│           ├── router.py      # Main API router
│           ├── health.py      # Health endpoints
│           ├── auth.py        # Authentication (Phase 8)
│           ├── users.py       # Placeholder routers
│           ├── agents.py
│           ├── devices.py
│           ├── scans.py
│           ├── vulnerabilities.py
│           ├── logs.py
│           ├── alerts.py
│           ├── threat_intelligence.py
│           ├── reports.py
│           ├── ai.py
│           ├── settings.py
│           └── dashboard.py
├── alembic/
│   ├── versions/
│   │   └── 001_initial_schema.py  # Complete schema migration
│   ├── env.py                     # Alembic configuration
│   └── script.py.mako
├── main.py                    # Entry point (for deployment)
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables (local only)
├── .env.example             # Environment template
├── alembic.ini              # Alembic configuration
└── logs/                    # Application logs
```

## Deployment to Render

The backend is deployed on Render.com using:
- **Start command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Python version**: 3.10+
- **Runtime**: Standard

### Environment Variables on Render

Set these in the Render dashboard:
```
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
ENVIRONMENT=production
DEBUG=False
JWT_SECRET_KEY=<strong-random-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
LOG_LEVEL=INFO
CORS_ORIGINS=https://cybershield-ai.vercel.app
```

Do NOT use default/development values in production.

## Frontend Integration

The frontend (Vercel) expects:
- Backend at: `https://render-deployed-backend-url`
- Health endpoint: `GET /api/v1/health`
- CORS headers properly configured

### Verify Frontend Connectivity

From the frontend directory:
```bash
# Test health check
curl https://your-render-backend.onrender.com/api/v1/health
```

## Troubleshooting

### Database Connection Error

**Problem**: `psycopg.Error: could not connect to server`

**Solutions**:
1. Check DATABASE_URL is correct
2. For Neon, verify connection string has `?sslmode=require`
3. Check firewall/VPN isn't blocking the connection
4. Verify database name matches the connection string

### Port Already in Use

**Problem**: `Address already in use`

**Solution**:
```bash
python -m uvicorn app.main:app --port 8001
```

### Module Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solutions**:
1. Ensure you're in the `backend/` directory
2. Verify Python path includes backend: `python -c "import sys; print(sys.path)"`
3. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

### Alembic Migration Errors

**Problem**: `sqlalchemy.exc.ProgrammingError` during migration

**Solutions**:
1. Check DATABASE_URL is correct
2. Verify database exists and is accessible
3. For development, ensure SQLite file location is writable
4. Check Alembic configuration in alembic.ini

### Logging Issues

**Problem**: Can't write logs

**Solutions**:
1. Ensure `logs/` directory exists: `mkdir logs`
2. Check directory permissions: `chmod 755 logs`
3. Verify disk space is available

## Development Workflow

```
1. Create feature branch
   git checkout -b feature/my-feature

2. Modify models/endpoints
   # Edit app/models/ or app/api/v1/

3. Create migration if schema changed
   alembic revision --autogenerate -m "description"

4. Run tests
   python -m pytest ../tests/test_backend_foundation.py -v

5. Test locally
   python -m uvicorn app.main:app --reload

6. Commit changes
   git add .
   git commit -m "feat: description"

7. Push and create PR
   git push origin feature/my-feature
```

## Phase 7 Summary

This phase establishes:
- ✅ FastAPI application foundation
- ✅ SQLAlchemy ORM with 25 tables
- ✅ Alembic database migrations
- ✅ Health check endpoints
- ✅ Configuration management
- ✅ Error handling infrastructure
- ✅ Structured logging
- ✅ API router structure
- ✅ Foundation test suite
- ✅ Local development environment

## Next Phases

- **Phase 8**: Authentication & RBAC
- **Phase 9-27**: Feature implementation

## Resources

- [API Documentation](../../docs/api/)
- [Database Schema](../../docs/database/schema.md)
- [Architecture Overview](../../docs/architecture/backend-architecture.md)
- [SRS](../../docs/srs/SRS.md)
- [GitHub Repository](https://github.com/JeslinSajan/cybershield-ai)

## Support

For questions or issues:
1. Check [GitHub Issues](https://github.com/JeslinSajan/cybershield-ai/issues)
2. Review documentation in `docs/`
3. Check application logs: `cat logs/cybershield.log`
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```powershell
Copy-Item .env.example .env
```

Edit `backend/.env` and replace `DATABASE_URL` with your actual Neon connection string:
```env
DATABASE_URL=postgresql://your-username:your-password@ep-xxx.region.aws.neon.tech/your-database?sslmode=require
```

### 5. Run Backend Server

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will start at `http://localhost:8000`

### 6. Verify Backend Health

Open a new PowerShell terminal and test:

```powershell
# Basic health check (no database)
Invoke-RestMethod -Uri http://localhost:8000/api/v1/health -Method Get

# Database health check (requires Neon connection)
Invoke-RestMethod -Uri http://localhost:8000/api/v1/health/db -Method Get
```

Expected responses:
- `/api/v1/health`: `{"status": "healthy"}`
- `/api/v1/health/db`: `{"status": "healthy", "database": "connected", "test_row": {...}}`

## Frontend Setup

### 1. Install Dependencies

Open a new PowerShell terminal (keep backend running):

```powershell
cd frontend
npm install
```

### 2. Configure Environment Variables

```powershell
Copy-Item .env.example .env
```

For local development, `frontend/.env` should contain:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Run Frontend Development Server

```powershell
npm run dev
```

The frontend will start at `http://localhost:5173`

### 4. Verify Frontend

1. Open `http://localhost:5173` in your browser
2. You should see the login page with the CyberShield AI branding
3. Click "Secure Login" to authenticate (mock login for now)
4. You should be redirected to the dashboard with:
   - Sidebar navigation
   - Top bar with backend health status indicator
   - Empty state pages (no demo data)
   - Summary cards showing 0 values

## Running Both Services

For development, you need both services running simultaneously:

**Terminal 1 - Backend:**
```powershell
cd cybershield-ai\backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd cybershield-ai\frontend
npm run dev
```

## Troubleshooting

### Backend Issues

**Virtual environment activation fails:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Database connection error:**
- Verify your Neon DATABASE_URL is correct in `backend/.env`
- Ensure the connection string includes `?sslmode=require`
- Check that your Neon database is active

**Port 8000 already in use:**
```powershell
# Find and kill the process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Frontend Issues

**npm install fails:**
```powershell
# Clear npm cache and retry
npm cache clean --force
npm install
```

**Port 5173 already in use:**
```powershell
# Find and kill the process using port 5173
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

**Frontend can't connect to backend:**
- Verify backend is running at `http://localhost:8000`
- Check `frontend/.env` has `VITE_API_BASE_URL=http://localhost:8000`
- Check browser console for CORS errors

## Stopping Services

To stop the services, press `Ctrl+C` in each terminal.

To deactivate the Python virtual environment:
```powershell
deactivate
```

## Next Steps

After verifying local development works:
- Backend health checks return healthy
- Frontend loads and mock login works
- Dashboard displays with empty states

You're ready for Phase 7: Backend API implementation with real authentication and data endpoints.
