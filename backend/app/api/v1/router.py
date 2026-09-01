from fastapi import APIRouter
from app.api.v1 import health, auth, users, agents, devices, scans, vulnerabilities, logs, alerts, threat_intelligence, reports, ai, settings, dashboard

router = APIRouter()

# Health endpoints (always available)
router.include_router(health.router, prefix="/health", tags=["Health"])

# API group routers (placeholders for future phases)
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(agents.router, prefix="/agents", tags=["Agents"])
router.include_router(devices.router, prefix="/devices", tags=["Devices"])
router.include_router(scans.router, prefix="/scans", tags=["Scans"])
router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["Vulnerabilities"])
router.include_router(logs.router, prefix="/logs", tags=["Logs"])
router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
router.include_router(threat_intelligence.router, prefix="/threat-intelligence", tags=["Threat Intelligence"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(ai.router, prefix="/ai", tags=["AI"])
router.include_router(settings.router, prefix="/settings", tags=["Settings"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
