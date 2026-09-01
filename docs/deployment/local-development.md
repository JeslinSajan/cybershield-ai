# Local Development Setup

This guide provides step-by-step instructions for running CyberShield AI locally on Windows using PowerShell.

## Prerequisites

- **Python 3.10+** - Download from [python.org](https://www.python.org/downloads/)
- **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/)
- **Git** - Download from [git-scm.com](https://git-scm.com/)
- **Neon PostgreSQL Database** - Free account at [console.neon.tech](https://console.neon.tech)

## Initial Setup

### 1. Clone the Repository

```powershell
git clone https://github.com/JeslinSajan/cybershield-ai.git
cd cybershield-ai
```

### 2. Set Up Neon Database

1. Create a free account at [console.neon.tech](https://console.neon.tech)
2. Create a new project and database
3. Copy the connection string from the Neon dashboard
4. The connection string format should be: `postgresql://username:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require`

## Backend Setup

### 1. Create Python Virtual Environment

```powershell
cd backend
python -m venv venv
```

### 2. Activate Virtual Environment (PowerShell)

```powershell
.\venv\Scripts\Activate.ps1
```

**Note:** If you get a script execution error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Install Dependencies

```powershell
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
