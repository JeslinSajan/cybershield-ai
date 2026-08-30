"""
CyberShield AI - Deployment Smoke Test Backend
Minimal FastAPI app to verify Vercel + Render + Neon connectivity
"""
import os
from fastapi import FastAPI
import asyncpg

app = FastAPI(title="CyberShield AI Smoke Test", version="0.0.1-smoke-test")


@app.get("/api/v1/health")
async def health():
    """Basic health check - no database dependency"""
    return {"status": "healthy"}


@app.get("/api/v1/health/db")
async def health_db():
    """Database health check - connects to Neon and queries test table"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        return {
            "status": "error",
            "message": "DATABASE_URL environment variable not set"
        }
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Query the smoke test table
        result = await conn.fetchrow(
            "SELECT id, timestamp FROM _healthcheck LIMIT 1"
        )
        
        await conn.close()
        
        if result:
            return {
                "status": "healthy",
                "database": "connected",
                "test_row": {
                    "id": result["id"],
                    "timestamp": str(result["timestamp"])
                }
            }
        else:
            return {
                "status": "warning",
                "database": "connected",
                "message": "No rows found in _healthcheck table"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "message": str(e)
        }
